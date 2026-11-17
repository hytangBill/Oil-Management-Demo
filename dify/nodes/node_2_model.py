import json
import math

# ===== PRE-TRAINED MODEL PARAMETERS =====
# Replace this block with the coefficients exported from the Python training notebook.
# Current values are ILLUSTRATIVE (hand-set so that a vat lasts roughly 1–1.5 trading days from 18 %).
MODEL = {
    "version": "demo-0.1-illustrative",
    "vat_family": {"F1": "fries", "C1": "chicken"},
    "routing_share": {"F1": 0.5, "C1": 0.5},          # store has 2 vats per family; F1/C1 get half
    "k_tpm_per_stress_kg": {"F1": 0.045, "C1": 0.060},  # TPM points per stress-weighted kg fried
    "idle_tpm_per_block": 0.010,                       # TPM points per 15 min hot (base thermal load)
    "resid_sd_per_block": 0.05,                        # TPM points, from model residuals
    "capacity_stress_kg_per_block": {"F1": 10.0, "C1": 8.0},
    "filter_rate_multiplier": 0.85,                    # filtering slows subsequent degradation
    "filter_effect_blocks": 32,                        # ... for 8 operating hours
    "fresh_tpm": 5.0,
    "vat_volume_l": {"F1": 15.0, "C1": 15.0},
    # Historical POS profile: average orders per 15-min block, by hour of day (store open 07–24)
    "hist_orders_per_block": {7: 8, 8: 12, 9: 10, 10: 12, 11: 24, 12: 40, 13: 34, 14: 18, 15: 12,
                              16: 14, 17: 26, 18: 38, 19: 30, 20: 20, 21: 16, 22: 12, 23: 8},
    # Historical average stress-weighted fried kg per order, per family
    "hist_stress_kg_per_order": {"fries": 0.14, "chicken": 0.11},
    "peak_orders": 30,
    "quiet_orders": 15,
    "horizon_blocks": 204,                             # 3 trading days of 17 h
}
OPEN_MIN = 7 * 60


def next_block(t):
    t += 15
    if t % 1440 == 0:          # midnight: store closed until 07:00
        t += OPEN_MIN
    return t


def hour_of(t):
    return (t % 1440) // 60


def orders_at(t):
    return MODEL["hist_orders_per_block"].get(hour_of(t), 0)


def slot_label(orders):
    if orders >= MODEL["peak_orders"]:
        return "PEAK"
    if orders <= MODEL["quiet_orders"]:
        return "QUIET"
    return "NORMAL"


def hist_load(v, t):
    fam = MODEL["vat_family"][v]
    raw = MODEL["hist_stress_kg_per_order"][fam] * orders_at(t) * MODEL["routing_share"][v]
    return min(raw, MODEL["capacity_stress_kg_per_block"][v])


def mix(tpm, add_l, vol):
    return (tpm * (vol - add_l) + MODEL["fresh_tpm"] * add_l) / vol


def trajectory(v, tpm0, filter_left, times, action=None, at_idx=0):
    """Mean and sd of TPM at the END of each future block. Action applied at the start of block at_idx."""
    k = MODEL["k_tpm_per_stress_kg"][v]
    vol = MODEL["vat_volume_l"][v]
    mean, sd = [], []
    tpm = tpm0
    var = 0.0
    fl = filter_left
    for i, t in enumerate(times):
        if action and i == at_idx:
            if action == "FILTER":
                fl = MODEL["filter_effect_blocks"]
            elif action == "TOP_UP_2L":
                tpm = mix(tpm, 2.0, vol)
            elif action == "PARTIAL_5L":
                tpm = mix(tpm, 5.0, vol)
            elif action == "FULL_CHANGE":
                tpm = MODEL["fresh_tpm"]
                fl = 0
                var = 0.0
        mult = MODEL["filter_rate_multiplier"] if fl > 0 else 1.0
        tpm += MODEL["idle_tpm_per_block"] + k * mult * hist_load(v, t)
        var += MODEL["resid_sd_per_block"] ** 2
        fl = max(0, fl - 1)
        mean.append(round(tpm, 3))
        sd.append(round(math.sqrt(var), 3))
    return mean, sd


def main(new_state: str, order_json: str) -> dict:
    s = json.loads(new_state)
    order = json.loads(order_json)
    t_now = s["clock"]
    orders_slot = orders_at(t_now)
    label = slot_label(orders_slot)

    # --- 1. Update for the submitted 15-min block ---------------------------
    # Scenario reading: "this order represents the typical order in this slot",
    # so block load = order stress-kg x historical order count x routing share.
    vats_out = {}
    for v, vs in s["vats"].items():
        fam = MODEL["vat_family"][v]
        order_stress = order["per_family"][fam]["stress_kg"]
        raw_load = order_stress * orders_slot * MODEL["routing_share"][v]
        cap = MODEL["capacity_stress_kg_per_block"][v]
        load = min(raw_load, cap)
        hist = MODEL["hist_stress_kg_per_order"][fam] * orders_slot * MODEL["routing_share"][v]
        mult = MODEL["filter_rate_multiplier"] if vs.get("filter_blocks_left", 0) > 0 else 1.0
        delta = MODEL["idle_tpm_per_block"] + MODEL["k_tpm_per_stress_kg"][v] * mult * load
        vats_out[v] = {
            "family": fam,
            "tpm_before": round(vs["tpm"], 3),
            "delta": round(delta, 3),
            "tpm_after": round(vs["tpm"] + delta, 3),
            "order_stress_kg": order_stress,
            "block_load_kg": round(load, 3),
            "block_load_raw_kg": round(raw_load, 3),
            "capacity_reached": raw_load > cap,
            "hist_block_load_kg": round(hist, 3),
            "load_index": round(raw_load / hist, 3) if hist > 0 else None,
            "filter_active": vs.get("filter_blocks_left", 0) > 0,
            "filter_left_after": max(0, vs.get("filter_blocks_left", 0) - 1),
        }

    # --- 2. Forecast from the end of this block -----------------------------
    t_next = next_block(t_now)
    times = []
    t = t_next
    for _ in range(MODEL["horizon_blocks"]):
        times.append(t)
        t = next_block(t)
    quiet_idx = next((i for i, tt in enumerate(times) if orders_at(tt) <= MODEL["quiet_orders"]), 0)

    scenarios = {}
    for v, vo in vats_out.items():
        sc = {}
        for name, act, idx in [("DO_NOTHING", None, 0),
                               ("FILTER_AT_WINDOW", "FILTER", quiet_idx),
                               ("TOP_UP_2L_AT_WINDOW", "TOP_UP_2L", quiet_idx),
                               ("PARTIAL_5L_AT_WINDOW", "PARTIAL_5L", quiet_idx),
                               ("FULL_CHANGE_AT_WINDOW", "FULL_CHANGE", quiet_idx),
                               ("FULL_CHANGE_NOW", "FULL_CHANGE", 0)]:
            m, sd = trajectory(v, vo["tpm_after"], vo["filter_left_after"], times, act, idx)
            sc[name] = {"mean": m, "sd": sd, "action_idx": idx}
        scenarios[v] = sc

    out = {
        "model_version": MODEL["version"],
        "block_start": t_now,
        "clock_next": t_next,
        "slot": {"hour": hour_of(t_now), "orders_per_block": orders_slot, "label": label},
        "vats": vats_out,
        "times": times,
        "quiet_window_idx": quiet_idx,
        "quiet_window_start": times[quiet_idx],
        "scenarios": scenarios,
    }
    return {"model_json": json.dumps(out)}
