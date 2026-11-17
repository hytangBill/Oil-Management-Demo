import json

# ===== LAYER 1: APPROVED POLICY (demo values — must be set by operator / food-safety owner) =====
POLICY = {
    "limit_tpm": 24.0,              # action limit: oil must not be used at or above this
    "warn_tpm": 21.0,               # warning band
    "measure_margin": 2.0,          # re-measure when the P90 path reaches limit - margin
    "max_measure_interval_h": 4.0,  # never go longer than this without a reading
    "z_p90": 1.2816,
    "safe_target_h": 6.0,           # an action must keep the P90 path below the limit for at least this long
    "red_if_cross_within_h": 1.0,
}
# ===== LAYER 3: OPTIMIZER COSTS (illustrative) =====
COST = {"oil_eur_per_l": 2.0, "labor_eur_per_min": 0.30,
        "downtime_eur_per_min": {"PEAK": 3.0, "NORMAL": 1.0, "QUIET": 0.3}}
ACTIONS = {
    # action code: (scenario, oil L, labour min, downtime min, when)
    "CONTINUE":                        ("DO_NOTHING",            0,  0,  0,  "none"),
    "FILTER_IN_QUIET_WINDOW":          ("FILTER_AT_WINDOW",      0,  12, 12, "window"),
    "TOP_UP_IN_QUIET_WINDOW":          ("TOP_UP_2L_AT_WINDOW",   2,  4,  0,  "window"),
    "PARTIAL_REPLACE_IN_QUIET_WINDOW": ("PARTIAL_5L_AT_WINDOW",  5,  15, 15, "window"),
    "FULL_CHANGE_IN_QUIET_WINDOW":     ("FULL_CHANGE_AT_WINDOW", 15, 30, 30, "window"),
    "FULL_CHANGE_NOW":                 ("FULL_CHANGE_NOW",       15, 30, 30, "now"),
}
ORDERS_PEAK, ORDERS_QUIET = 30, 15


def first_cross(mean, sd, level, z):
    for i, (m, s) in enumerate(zip(mean, sd)):
        if m + z * s >= level:
            return i
    return None


def slot_of_orders(n):
    return "PEAK" if n >= ORDERS_PEAK else ("QUIET" if n <= ORDERS_QUIET else "NORMAL")


def load_word(li):
    if li is None:
        return "NO_LOAD"
    if li < 0.85:
        return "LOWER_THAN_USUAL"
    if li <= 1.15:
        return "SIMILAR_TO_USUAL"
    if li <= 1.5:
        return "HIGHER_THAN_USUAL"
    return "MUCH_HIGHER_THAN_USUAL"


def main(model_json: str) -> dict:
    mdl = json.loads(model_json)
    times = mdl["times"]
    w = mdl["quiet_window_idx"]
    lim, z = POLICY["limit_tpm"], POLICY["z_p90"]
    decisions = {}
    facts = ["Time slot of this order: %s." % mdl["slot"]["label"],
             "A quiet window is %s." % ("happening now" if w == 0 else "coming later today")]

    for v, vo in mdl["vats"].items():
        sc = mdl["scenarios"][v]
        base = sc["DO_NOTHING"]
        p90_i = first_cross(base["mean"], base["sd"], lim, z)
        tpm = vo["tpm_after"]

        # ---- Layer 1: deterministic safety rules decide what is allowed ----
        if tpm >= lim:
            status, allowed, rule = "RED", ["FULL_CHANGE_NOW"], "TPM_AT_OR_ABOVE_LIMIT"
        elif p90_i is not None and ((p90_i + 1) * 0.25 <= POLICY["red_if_cross_within_h"] or (w > 0 and p90_i < w)):
            status, allowed, rule = "RED", ["FULL_CHANGE_NOW"], "LIMIT_LIKELY_BEFORE_QUIET_WINDOW"
        elif tpm >= POLICY["warn_tpm"] or (p90_i is not None and (p90_i + 1) * 0.25 < POLICY["safe_target_h"]):
            status, rule = "AMBER", "APPROACHING_LIMIT"
            allowed = ["FILTER_IN_QUIET_WINDOW", "TOP_UP_IN_QUIET_WINDOW", "PARTIAL_REPLACE_IN_QUIET_WINDOW",
                       "FULL_CHANGE_IN_QUIET_WINDOW", "FULL_CHANGE_NOW"]
        else:
            status, rule = "GREEN", "WITHIN_LIMITS"
            allowed = ["CONTINUE", "FILTER_IN_QUIET_WINDOW", "TOP_UP_IN_QUIET_WINDOW"]

        # ---- Layer 3: lowest-cost allowed action that meets the safety target ----
        table = []
        for a, (scn, oil, lab, down, when) in ACTIONS.items():
            tr = sc[scn]
            ci = first_cross(tr["mean"], tr["sd"], lim, z)
            p50 = first_cross(tr["mean"], tr["sd"], lim, 0.0)
            p10 = first_cross(tr["mean"], tr["sd"], lim, -z)
            act_idx = 0 if when != "window" else w
            act_slot = slot_of_orders(0) if when == "none" else mdl["slot"]["label"] if act_idx == 0 else "QUIET"
            cost = oil * COST["oil_eur_per_l"] + lab * COST["labor_eur_per_min"] + down * COST["downtime_eur_per_min"][act_slot]
            safe_h = None if ci is None else (ci + 1) * 0.25
            table.append({
                "action": a, "allowed": a in allowed,
                "rul_p90_h": safe_h,
                "rul_p50_h": None if p50 is None else (p50 + 1) * 0.25,
                "rul_p10_h": None if p10 is None else (p10 + 1) * 0.25,
                "oil_l": oil, "labor_min": lab, "downtime_min": down, "cost_eur": round(cost, 2),
                "meets_target": safe_h is None or safe_h >= POLICY["safe_target_h"],
                "action_time": times[act_idx] if when != "none" else None,
            })
        feasible = [r for r in table if r["allowed"] and r["meets_target"]]
        if feasible:
            best = sorted(feasible, key=lambda r: (r["cost_eur"], -(r["rul_p90_h"] or 1e9)))[0]
            why = "LOWEST_COST_ALLOWED_ACTION_THAT_KEEPS_OIL_BELOW_LIMIT_FOR_TARGET_PERIOD"
        else:
            best = sorted([r for r in table if r["allowed"]], key=lambda r: -(r["rul_p90_h"] or 1e9))[0]
            why = "NO_ACTION_MEETS_TARGET_SO_LONGEST_SAFE_LIFE_CHOSEN"

        # ---- Next measurement (from the chosen action's trajectory) ----
        tr = sc[ACTIONS[best["action"]][0]]
        mi = first_cross(tr["mean"], tr["sd"], lim - POLICY["measure_margin"], z)
        max_i = int(POLICY["max_measure_interval_h"] / 0.25) - 1
        if mi is None or mi > max_i:
            mi = max_i
            measure_reason = "ROUTINE_MAXIMUM_INTERVAL"
        else:
            measure_reason = "FORECAST_APPROACHING_LIMIT"
        measure_at = mdl["clock_next"] if mi <= 0 else times[mi]

        decisions[v] = {"status": status, "rule": rule, "allowed": allowed,
                        "recommended": best["action"], "why": why,
                        "next_measure_at": measure_at, "measure_reason": measure_reason,
                        "table": table}
        facts.append(
            "Vat %s (%s): status=%s; rule=%s; load_in_this_slot=%s; vat_capacity_reached=%s; filter_effect_active=%s; "
            "recommended_action=%s; selection_basis=%s; other_allowed_actions=%s; next_measurement_reason=%s."
            % (v, vo["family"], status, rule, load_word(vo["load_index"]),
               "yes" if vo["capacity_reached"] else "no", "yes" if vo["filter_active"] else "no",
               best["action"], why, ",".join(a for a in allowed if a != best["action"]) or "none", measure_reason))

    out = {"policy": POLICY, "decisions": decisions}
    return {"decision_json": json.dumps(out), "llm_facts": "\n".join(facts)}
