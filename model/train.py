# %% [markdown]
# # FryWise — train the TPM degradation model
#
# **DEMO ONLY — synthetic data, illustrative parameters. Not for food-safety decisions.**
#
# Goal: learn how many TPM points each kilogram of (stress-weighted) fried food adds, using only what a
# restaurant would really have: POS sales, the recipe table, handheld TPM readings and logged oil events.
#
# Model (per vat, between two consecutive valid readings of the same oil batch):
#
# `ΔTPM + dilution_from_top_ups = idle × hot_blocks + k × stress_kg + k × (filter_mult − 1) × stress_kg_while_filtered`
#
# The fitted values are exported to `model/model_params.json` and as a ready-to-paste `MODEL` block for the
# Dify code node "② TPM model".

# %%
import json
import os

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import GroupKFold

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__) if "__file__" in globals() else ".", ".."))
if not os.path.exists(os.path.join(ROOT, "data")):
    ROOT = os.path.abspath(".")
DATA = os.path.join(ROOT, "data", "synthetic", "full")
if not os.path.exists(os.path.join(DATA, "pos_items.csv")):
    DATA = os.path.join(ROOT, "data", "synthetic", "sample")
print("Using data from", DATA)

VAT_FAMILY = {"F1": "fries", "C1": "chicken"}
ROUTING_SHARE = 0.5
FRESH_TPM, VAT_VOLUME_L, TOPUP_L, FILTER_BLOCKS = 5.0, 15.0, 2.0, 32

recipe = pd.read_csv(os.path.join(ROOT, "data", "recipe_master.csv"))
pos_items = pd.read_csv(os.path.join(DATA, "pos_items.csv"), parse_dates=["block_start"])
pos_blocks = pd.read_csv(os.path.join(DATA, "pos_blocks.csv"), parse_dates=["block_start"])
readings = pd.read_csv(os.path.join(DATA, "tpm_readings.csv"), parse_dates=["measurement_timestamp"])
events = pd.read_csv(os.path.join(DATA, "oil_events.csv"), parse_dates=["action_timestamp"])
print(len(pos_items), "POS lines,", len(readings), "TPM readings,", len(events), "oil events")

# %% [markdown]
# ## 1. POS → stress-weighted fried kg per vat per 15-minute block
# Non-fried items (grill) have no fryer family and drop out automatically.

# %%
items = pos_items.merge(recipe[["sku", "fryer_family", "fried_g_per_unit", "stress_weight"]],
                        left_on="sku_id", right_on="sku", how="left")
items = items.dropna(subset=["fryer_family"])
items["stress_kg"] = items.quantity * items.fried_g_per_unit / 1000 * items.stress_weight
fam_load = items.groupby(["store_id", "block_start", "fryer_family"]).stress_kg.sum().unstack(fill_value=0.0)

blocks = []
for vat, fam in VAT_FAMILY.items():
    b = pos_blocks[["store_id", "block_start"]].copy()
    b["vat_id"] = vat
    b = b.merge(fam_load[fam].rename("fam_stress").reset_index(), on=["store_id", "block_start"], how="left")
    b["stress_kg"] = b.fam_stress.fillna(0.0) * ROUTING_SHARE
    blocks.append(b.drop(columns="fam_stress"))
blocks = pd.concat(blocks).sort_values(["store_id", "vat_id", "block_start"]).reset_index(drop=True)

# filter effect: active for FILTER_BLOCKS operating blocks after each logged filtration
blocks["filter_active"] = False
for (store, vat), g in blocks.groupby(["store_id", "vat_id"]):
    f_times = events[(events.store_id == store) & (events.vat_id == vat) & (events.action_type == "filter")].action_timestamp
    starts = g.block_start.values
    active = np.zeros(len(g), dtype=bool)
    for ft in f_times.values:
        i0 = np.searchsorted(starts, ft)
        active[i0:i0 + FILTER_BLOCKS] = True
    blocks.loc[g.index, "filter_active"] = active
blocks.head()

# %% [markdown]
# ## 2. Build training intervals between consecutive valid readings of the same oil batch
# Top-ups dilute the oil; we add back the expected dilution using the volume-weighted mixing formula and a
# linear interpolation of TPM at the moment of the top-up. Intervals containing a full change are impossible
# by construction (a change starts a new oil batch).

# %%
valid = readings[readings.measurement_validity_flag == "valid"].sort_values("measurement_timestamp")
rows = []
for (store, vat, batch), g in valid.groupby(["store_id", "vat_id", "oil_batch_id"]):
    g = g.sort_values("measurement_timestamp")
    b = blocks[(blocks.store_id == store) & (blocks.vat_id == vat)]
    ev = events[(events.store_id == store) & (events.vat_id == vat) & (events.oil_batch_id == batch) & (events.action_type == "top_up")]
    for (_, r0), (_, r1) in zip(g.iloc[:-1].iterrows(), g.iloc[1:].iterrows()):
        t0, t1 = r0.measurement_timestamp, r1.measurement_timestamp
        w = b[(b.block_start >= t0) & (b.block_start < t1)]
        tu = ev[(ev.action_timestamp >= t0) & (ev.action_timestamp < t1)]
        dil = 0.0
        for ts in tu.action_timestamp:
            frac = (ts - t0) / (t1 - t0)
            tpm_est = r0.tpm_pct + frac * (r1.tpm_pct - r0.tpm_pct)
            dil += (tpm_est - FRESH_TPM) * TOPUP_L / VAT_VOLUME_L
        rows.append({
            "store_id": store, "vat_id": vat, "oil_batch_id": batch, "t0": t0, "t1": t1,
            "tpm0": r0.tpm_pct, "tpm1": r1.tpm_pct, "y": r1.tpm_pct - r0.tpm_pct + dil,
            "hot_blocks": len(w),
            "stress_kg": w.stress_kg.sum(),
            "stress_kg_filtered": w.loc[w.filter_active, "stress_kg"].sum(),
            "n_top_ups": len(tu),
        })
iv = pd.DataFrame(rows)
iv = iv[iv.hot_blocks > 0]
print(len(iv), "training intervals")
iv.describe().round(2)

# %% [markdown]
# ## 3. Fit per vat, validated with store-grouped cross-validation
# Rows from the same store never appear in both train and test folds (README §8.3).

# %%
FEATURES = ["hot_blocks", "stress_kg", "stress_kg_filtered"]
results, params = {}, {}
for vat in VAT_FAMILY:
    d = iv[iv.vat_id == vat].reset_index(drop=True)
    X, y, groups = d[FEATURES].values, d.y.values, d.store_id.values
    n_splits = min(5, len(np.unique(groups)))
    maes, base_maes = [], []
    if n_splits >= 2:
        for tr, te in GroupKFold(n_splits=n_splits).split(X, y, groups):
            m = LinearRegression(fit_intercept=False).fit(X[tr], y[tr])
            maes.append(np.mean(np.abs(m.predict(X[te]) - y[te])))
            rate = y[tr].sum() / d.hot_blocks.values[tr].sum()          # baseline: time-only model
            base_maes.append(np.mean(np.abs(rate * d.hot_blocks.values[te] - y[te])))
    m = LinearRegression(fit_intercept=False).fit(X, y)
    idle, k, kf = m.coef_
    resid = y - m.predict(X)
    meas_var = 2 * 0.4 ** 2                                              # two readings, Testo-like noise
    sd_block = float(np.sqrt(max(np.var(resid) - meas_var, 1e-4) / d.hot_blocks.mean()))
    params[vat] = {"idle": idle, "k": k, "filter_mult": 1 + kf / k, "sd_block": sd_block}
    results[vat] = {"n_intervals": len(d), "cv_mae_tpm": np.mean(maes) if maes else None,
                    "baseline_time_only_mae": np.mean(base_maes) if base_maes else None}
pd.DataFrame(params).T.round(4), pd.DataFrame(results).T.round(3)

# %% [markdown]
# ## 4. Historical demand profile and export
# The forecast in Dify needs the typical orders per 15 minutes by hour and the average stress-kg per order.

# %%
pb = pos_blocks.copy()
pb["hour"] = pb.block_start.dt.hour
hist_orders = pb.groupby("hour").n_orders.mean().round(1)
total_orders = pos_blocks.n_orders.sum()
fam_total = items.groupby("fryer_family").stress_kg.sum()
hist_stress = (fam_total / total_orders).round(4)

MODEL = {
    "version": "trained-synthetic-%s" % pd.Timestamp.now().strftime("%Y%m%d"),
    "vat_family": VAT_FAMILY,
    "routing_share": {v: ROUTING_SHARE for v in VAT_FAMILY},
    "k_tpm_per_stress_kg": {v: round(params[v]["k"], 4) for v in VAT_FAMILY},
    "idle_tpm_per_block": round(float(np.mean([params[v]["idle"] for v in VAT_FAMILY])), 4),
    "resid_sd_per_block": round(float(np.mean([params[v]["sd_block"] for v in VAT_FAMILY])), 4),
    "capacity_stress_kg_per_block": {"F1": 10.0, "C1": 8.0},
    "filter_rate_multiplier": round(float(np.clip(np.mean([params[v]["filter_mult"] for v in VAT_FAMILY]), 0.5, 1.0)), 3),
    "filter_effect_blocks": FILTER_BLOCKS,
    "fresh_tpm": FRESH_TPM,
    "vat_volume_l": {v: VAT_VOLUME_L for v in VAT_FAMILY},
    "hist_orders_per_block": {int(h): float(v) for h, v in hist_orders.items()},
    "hist_stress_kg_per_order": {f: float(v) for f, v in hist_stress.items()},
    "peak_orders": 30,
    "quiet_orders": 15,
    "horizon_blocks": 204,
}
os.makedirs(os.path.join(ROOT, "model"), exist_ok=True)
with open(os.path.join(ROOT, "model", "model_params.json"), "w") as f:
    json.dump({"MODEL": MODEL, "validation": results}, f, indent=2, default=float)
def plain(o):
    """Convert numpy scalars to plain Python so the block pastes cleanly into Dify (int hour keys kept)."""
    if isinstance(o, dict):
        return {(int(k) if isinstance(k, (np.integer,)) else k): plain(v) for k, v in o.items()}
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    return o


import pprint
with open(os.path.join(ROOT, "model", "MODEL_block_for_dify.py"), "w") as f:
    f.write("# Paste this over the MODEL = {...} block in Dify code node '② TPM model'\n")
    f.write("MODEL = " + pprint.pformat(plain(MODEL), indent=4, width=110, sort_dicts=False) + "\n")
print(json.dumps(MODEL, indent=2))

# %% [markdown]
# ## 5. Sanity check against the simulator's hidden truth
# Only possible with synthetic data: the simulator used idle = 0.020, k(F1) = 0.100, k(C1) = 0.130,
# filter multiplier = 0.85 (store-level effects vary around these). POS misses ~5 % waste/remakes,
# so k is expected to come out slightly higher than the hidden value.

# %%
truth = {"F1": {"idle": 0.020, "k": 0.100, "filter_mult": 0.85}, "C1": {"idle": 0.020, "k": 0.130, "filter_mult": 0.85}}
pd.DataFrame({v: {**{"fit_" + a: round(params[v][a], 4) for a in ("idle", "k", "filter_mult")},
                  **{"true_" + a: b for a, b in truth[v].items()}} for v in VAT_FAMILY}).T

# %% [markdown]
# ## 6. Picture of one oil lifecycle (synthetic)
# Hidden true TPM (line), handheld readings (dots), top-ups, filters and full changes.

# %%
import matplotlib
matplotlib.use("Agg") if "__file__" in globals() else None
import matplotlib.pyplot as plt

truth_df = pd.read_csv(os.path.join(DATA, "tpm_truth.csv"), parse_dates=["block_start"])
store, vat = sorted(truth_df.store_id.unique())[0], "F1"
t = truth_df[(truth_df.store_id == store) & (truth_df.vat_id == vat)]
t = t[t.block_start < t.block_start.min() + pd.Timedelta(days=7)]
r = readings[(readings.store_id == store) & (readings.vat_id == vat) & (readings.measurement_timestamp <= t.block_start.max())]
e = events[(events.store_id == store) & (events.vat_id == vat) & (events.action_timestamp <= t.block_start.max())]
fig, ax = plt.subplots(figsize=(11, 4))
ax.plot(t.block_start, t.true_tpm_end, color="#D62300", lw=1.2, label="true TPM (hidden)")
ax.scatter(r.measurement_timestamp, r.tpm_pct, color="#27251F", s=14, zorder=3, label="handheld reading")
for kind, c in [("top_up", "#FFC72C"), ("filter", "#2E9E5B"), ("full_change", "#6B6459")]:
    for ts in e[e.action_type == kind].action_timestamp:
        ax.axvline(ts, color=c, lw=0.8, alpha=0.7)
    ax.plot([], [], color=c, label=kind.replace("_", " "))
ax.axhline(24, color="#C8102E", ls="--", lw=1, label="illustrative limit 24 %")
ax.set_ylabel("TPM %"); ax.set_title("%s / vat %s — first 7 days (synthetic)" % (store, vat))
ax.legend(ncol=3, fontsize=8, loc="lower right"); fig.tight_layout()
os.makedirs(os.path.join(ROOT, "docs", "screenshots"), exist_ok=True)
fig.savefig(os.path.join(ROOT, "docs", "screenshots", "synthetic_oil_lifecycle.png"), dpi=120)
