"""
FryWise synthetic data simulator.

Generates realistic-looking (but fully synthetic) data for a frying-oil demo:
  pos_blocks.csv    – orders per store per 15-min block
  pos_items.csv     – units sold per SKU per store per 15-min block
  tpm_readings.csv  – handheld TPM measurements (with sensor noise, some missing)
  oil_events.csv    – filter / top-up / full-change events per vat
  tpm_truth.csv     – hidden "true" TPM per vat per block (for evaluation only)

The hidden degradation process follows the same structure the demo model assumes:
  dTPM per block = idle + k_vat * store_effect * filter_mult * stress_kg_fried + process noise
where stress_kg_fried comes from POS sales routed through the recipe table, plus hidden
waste/remakes the POS never sees. Top-ups follow volume-weighted mixing.

DEMO ONLY — synthetic data, illustrative parameters. Not for food-safety decisions.

Usage:
  python model/simulator.py --stores 10 --days 30 --out data/synthetic/full
  python model/simulator.py --stores 1 --days 7 --out data/synthetic/sample --seed 7
"""
import argparse
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# ---- hidden "true" process parameters (the trainer tries to recover these) ----
TRUE = {
    "idle_per_block": 0.020,
    "k": {"F1": 0.100, "C1": 0.130},
    "filter_mult": 0.85,
    "filter_blocks": 32,
    "process_sd": 0.03,
    "meas_sd": 0.4,
    "fresh_tpm": 5.0,
    "vat_volume_l": 15.0,
    "routing_share": 0.5,          # F1 / C1 each take half of their family's load
    "absorption_l_per_kg": 0.08,   # oil carried out by food
    "waste_remake_factor": 1.05,   # extra frying the POS never sees
    "limit_tpm": 24.0,
}
VAT_FAMILY = {"F1": "fries", "C1": "chicken"}
# average units per order (synthetic menu mix)
SKU_RATE = {
    "fries_s": 0.15, "fries_m": 0.35, "fries_l": 0.25, "nuggets_6": 0.12, "nuggets_9": 0.08,
    "nuggets_20": 0.02, "mcchicken": 0.08, "mccrispy": 0.06, "chili_chicken": 0.05, "mckroket": 0.05,
    "filet_o_fish": 0.04, "big_mac": 0.15, "quarter_pounder": 0.08, "hamburger": 0.08,
    "cheeseburger": 0.12, "double_cheeseburger": 0.06,
}
MEASURE_TIMES = ["07:15", "11:00", "15:00", "19:00", "22:30"]
FILTER_TIME = "15:15"


def load_master():
    recipe = pd.read_csv(os.path.join(ROOT, "data", "recipe_master.csv")).set_index("sku")
    prof = pd.read_csv(os.path.join(ROOT, "data", "hist_orders_profile.csv")).set_index("hour")["orders_per_15min"]
    return recipe, prof


def simulate(n_stores=10, n_days=30, seed=42, start="2026-01-05"):
    rng = np.random.default_rng(seed)
    recipe, prof = load_master()
    skus = list(SKU_RATE)
    pos_blocks, pos_items, readings, events, truth = [], [], [], [], []
    rid = eid = 0

    for s in range(1, n_stores + 1):
        store = "S%02d" % s
        demand_scale = rng.uniform(0.6, 1.4)
        store_eff = {v: float(np.exp(rng.normal(0, 0.10))) for v in TRUE["k"]}
        policy = "schedule" if s % 2 == 0 else "measure"   # how the store decides to change oil today
        state = {v: {"tpm": TRUE["fresh_tpm"] + rng.normal(0, 0.3), "filter_left": 0, "absorbed": 0.0,
                     "batch": 1, "batch_start_day": 0} for v in TRUE["k"]}

        for d in range(n_days):
            day = pd.Timestamp(start) + pd.Timedelta(days=d)
            weekend = day.dayofweek >= 5
            for blk in range(7 * 4, 24 * 4):                 # 07:00 – 23:45
                ts = day + pd.Timedelta(minutes=15 * blk)
                hhmm = ts.strftime("%H:%M")
                lam = prof[ts.hour] * demand_scale * (1.2 if weekend else 1.0)
                n_orders = int(rng.poisson(lam))
                pos_blocks.append((store, ts, n_orders))
                stress = {"fries": 0.0, "chicken": 0.0}
                kg = {"fries": 0.0, "chicken": 0.0}
                for sku in skus:
                    q = int(rng.poisson(n_orders * SKU_RATE[sku])) if n_orders else 0
                    if q:
                        pos_items.append((store, ts, sku, q))
                        r = recipe.loc[sku]
                        if isinstance(r["fryer_family"], str):
                            fkg = q * r["fried_g_per_unit"] / 1000 * TRUE["waste_remake_factor"]
                            kg[r["fryer_family"]] += fkg
                            stress[r["fryer_family"]] += fkg * r["stress_weight"]

                for v, st in state.items():
                    fam = VAT_FAMILY[v]
                    # operator actions at the start of the block
                    if hhmm == FILTER_TIME and rng.random() < 0.8:
                        st["filter_left"] = TRUE["filter_blocks"]
                        eid += 1
                        events.append((eid, store, v, st["batch"], ts, "filter", 0.0, 0.0, None))
                    if st["absorbed"] >= 2.0:
                        before = st["tpm"]
                        vol = TRUE["vat_volume_l"]
                        st["tpm"] = (before * (vol - 2.0) + TRUE["fresh_tpm"] * 2.0) / vol
                        st["absorbed"] -= 2.0
                        eid += 1
                        events.append((eid, store, v, st["batch"], ts, "top_up", 2.0, 0.0, round(before, 3)))
                    # degradation during the block
                    load = stress[fam] * TRUE["routing_share"]
                    mult = TRUE["filter_mult"] if st["filter_left"] > 0 else 1.0
                    st["tpm"] += (TRUE["idle_per_block"] + TRUE["k"][v] * store_eff[v] * mult * load
                                  + rng.normal(0, TRUE["process_sd"]))
                    st["filter_left"] = max(0, st["filter_left"] - 1)
                    st["absorbed"] += kg[fam] * TRUE["routing_share"] * TRUE["absorption_l_per_kg"]
                    truth.append((store, v, st["batch"], ts, round(st["tpm"], 4)))

                    # measurement at the END of the block
                    end_hhmm = (ts + pd.Timedelta(minutes=15)).strftime("%H:%M")
                    if end_hhmm in MEASURE_TIMES and rng.random() < 0.9:
                        rid += 1
                        val = st["tpm"] + rng.normal(0, TRUE["meas_sd"])
                        valid = rng.random() > 0.02
                        if not valid:
                            val += rng.normal(0, 5)
                        temp = rng.normal(172, 4)
                        readings.append((rid, store, v, st["batch"], ts + pd.Timedelta(minutes=15),
                                         round(max(0.0, val), 1), round(temp, 1), "testo-270-%s" % store,
                                         "valid" if valid else "invalid"))
                        # measurement-based policy: change when the reading hits the limit
                        if policy == "measure" and valid and val >= TRUE["limit_tpm"]:
                            eid += 1
                            events.append((eid, store, v, st["batch"], ts + pd.Timedelta(minutes=15), "full_change",
                                           TRUE["vat_volume_l"], TRUE["vat_volume_l"], round(st["tpm"], 3)))
                            st.update(tpm=TRUE["fresh_tpm"] + rng.normal(0, 0.3), filter_left=0, absorbed=0.0,
                                      batch=st["batch"] + 1, batch_start_day=d)
            # schedule-based policy: change every 3rd day at closing, whatever the TPM
            for v, st in state.items():
                if policy == "schedule" and (d - st["batch_start_day"]) >= 2:
                    eid += 1
                    ts = day + pd.Timedelta(hours=23, minutes=59)
                    events.append((eid, store, v, st["batch"], ts, "full_change",
                                   TRUE["vat_volume_l"], TRUE["vat_volume_l"], round(st["tpm"], 3)))
                    st.update(tpm=TRUE["fresh_tpm"] + rng.normal(0, 0.3), filter_left=0, absorbed=0.0,
                              batch=st["batch"] + 1, batch_start_day=d + 1)

    def batch_id(store, v, b):
        return "%s-%s-B%03d" % (store, v, b)

    out = {
        "pos_blocks": pd.DataFrame(pos_blocks, columns=["store_id", "block_start", "n_orders"]),
        "pos_items": pd.DataFrame(pos_items, columns=["store_id", "block_start", "sku_id", "quantity"]),
        "tpm_readings": pd.DataFrame(readings, columns=["measurement_id", "store_id", "vat_id", "oil_batch", "measurement_timestamp",
                                                        "tpm_pct", "oil_temperature_c", "device_id", "measurement_validity_flag"]),
        "oil_events": pd.DataFrame(events, columns=["event_id", "store_id", "vat_id", "oil_batch", "action_timestamp", "action_type",
                                                    "fresh_oil_added_l", "oil_removed_l", "tpm_before"]),
        "tpm_truth": pd.DataFrame(truth, columns=["store_id", "vat_id", "oil_batch", "block_start", "true_tpm_end"]),
    }
    for k in ("tpm_readings", "oil_events", "tpm_truth"):
        df = out[k]
        df.insert(3, "oil_batch_id", [batch_id(a, b, c) for a, b, c in zip(df.store_id, df.vat_id, df.oil_batch)])
        out[k] = df.drop(columns="oil_batch")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stores", type=int, default=10)
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default=os.path.join(ROOT, "data", "synthetic", "full"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    data = simulate(a.stores, a.days, a.seed)
    for name, df in data.items():
        df.to_csv(os.path.join(a.out, name + ".csv"), index=False)
        print("%-14s %8d rows" % (name, len(df)))
    print("written to", a.out)


if __name__ == "__main__":
    main()
