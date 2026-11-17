import json
import re

WARN_TPM, LIMIT_TPM = 21.0, 24.0   # display colours only (must match policy node)
VAT_NAME = {"F1": "Fries vat F1", "C1": "Chicken vat C1"}
ACTION_LABEL = {
    "CONTINUE": "Continue frying — no action needed",
    "FILTER_IN_QUIET_WINDOW": "Filter in the next quiet window",
    "TOP_UP_IN_QUIET_WINDOW": "Top up 2 L fresh oil in the next quiet window",
    "PARTIAL_REPLACE_IN_QUIET_WINDOW": "Replace 5 L of oil in the next quiet window",
    "FULL_CHANGE_IN_QUIET_WINDOW": "Full oil change in the next quiet window",
    "FULL_CHANGE_NOW": "Full oil change now",
}
FALLBACK_REASON = {
    "RED": "The oil is at or close to the approved limit, so the policy rules only allow an immediate change.",
    "AMBER": "The oil is approaching the approved limit; the selected action is the lowest-cost option that keeps it within policy for the target period.",
    "GREEN": "The oil is comfortably within limits for the forecast period, so no costly intervention is needed now.",
}


def fmt_clock(t):
    if t is None:
        return "—"
    return "Day %d · %02d:%02d" % (t // 1440 + 1, (t % 1440) // 60, t % 60)


def dot(tpm):
    return "🔴" if tpm >= LIMIT_TPM else ("🟠" if tpm >= WARN_TPM else "🟢")


def h(x, horizon_h):
    return "> %.0f h" % horizon_h if x is None else "%.2g h" % x if x < 10 else "%.0f h" % x


def btn(msg, label, variant="secondary"):
    return '<button data-message="%s" data-variant="%s">%s</button>' % (msg, variant, label)


def parse_llm(text):
    if not text:
        return {}
    t = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    m = re.search(r"\{.*\}", t, flags=re.S)
    if not m:
        return {}
    try:
        d = json.loads(m.group(0))
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def clean_text(x):
    """LLM text may not contain numbers: numbers come only from the model and policy nodes."""
    if not isinstance(x, str) or not x.strip() or re.search(r"\d", x):
        return None
    return x.strip()[:400]


def main(llm_text: str, new_state: str, model_json: str, decision_json: str, order_md: str, order_json: str) -> dict:
    s = json.loads(new_state)
    mdl = json.loads(model_json)
    dec = json.loads(decision_json)
    llm = parse_llm(llm_text)
    horizon_h = len(mdl["times"]) * 0.25
    llm_ok = True

    # ---- update state ----
    for v, vo in mdl["vats"].items():
        s["vats"][v]["tpm"] = vo["tpm_after"]
        s["vats"][v]["filter_blocks_left"] = vo["filter_left_after"]
    s["clock"] = mdl["clock_next"]
    s["cart"] = {}
    s["orders_submitted"] = s.get("orders_submitted", 0) + 1

    f, c = s["vats"]["F1"]["tpm"], s["vats"]["C1"]["tpm"]
    out = ("> 🕐 **%s**　｜　%s F1 Fries **%.1f %%**　｜　%s C1 Chicken **%.1f %%**\n>\n"
           "> *DEMO MODEL — ILLUSTRATIVE PARAMETERS — NOT FOR FOOD-SAFETY OR LIVE OPERATIONAL DECISIONS*\n\n"
           % (fmt_clock(s["clock"]), dot(f), f, dot(c), c))

    slot = mdl["slot"]
    out += "## ① Order parsed — slot %s–%s (%s, ~%d orders / 15 min historically)\n\n" % (
        fmt_clock(mdl["block_start"]), fmt_clock(mdl["clock_next"])[-5:], slot["label"].lower(), slot["orders_per_block"])
    out += order_md + "\n"

    out += "\n## ② TPM update for this 15-minute slot\n\n"
    out += "*Scenario: every order in this slot looks like yours (your order × typical order count × vat routing share).*\n\n"
    out += "| Vat | TPM before | Load vs usual | Δ TPM | TPM now |\n|---|---:|---:|---:|---:|\n"
    for v, vo in mdl["vats"].items():
        li = vo["load_index"]
        li_txt = "—" if li is None else "%+.0f %%" % ((li - 1) * 100)
        if vo["capacity_reached"]:
            li_txt += " ⚠️ cap"
        out += "| %s | %.2f %% | %s | +%.2f | %s **%.2f %%** |\n" % (
            VAT_NAME[v], vo["tpm_before"], li_txt, vo["delta"], dot(vo["tpm_after"]), vo["tpm_after"])
    if any(vo["capacity_reached"] for vo in mdl["vats"].values()):
        out += "\n⚠️ *Vat capacity reached: load above capacity is assumed to go to the other vats of the same family.*\n"

    out += "\n## ③ Recommendation\n\n"
    out += "Next quiet window starts **%s**.\n\n" % fmt_clock(mdl["quiet_window_start"])
    for v, d in dec["decisions"].items():
        best = next(r for r in d["table"] if r["action"] == d["recommended"])
        lv = llm.get(v, {}) if isinstance(llm.get(v), dict) else {}
        reason = clean_text(lv.get("reason"))
        if reason is None:
            llm_ok = False
            reason = FALLBACK_REASON[d["status"]]
        icon = {"RED": "🔴", "AMBER": "🟠", "GREEN": "🟢"}[d["status"]]
        out += "### %s %s — %s\n\n" % (icon, VAT_NAME[v], ACTION_LABEL[d["recommended"]])
        if best["action_time"] is not None:
            out += "- **When:** %s\n" % fmt_clock(best["action_time"])
        out += "- **Measure again:** %s\n" % fmt_clock(d["next_measure_at"])
        out += "- **Remaining useful life after this action:** median %s (likely range %s – %s)\n" % (
            h(best["rul_p50_h"], horizon_h), h(best["rul_p90_h"], horizon_h), h(best["rul_p10_h"], horizon_h))
        out += "- **Why:** %s\n\n" % reason
        out += "**Action comparison**\n\n"
        out += "| Action | Allowed | Safe until (P90) | Median RUL | Oil | Labour | Cost |\n|---|:-:|---:|---:|---:|---:|---:|\n"
        for r in d["table"]:
            mark = "✅" if r["action"] == d["recommended"] else ("✓" if r["allowed"] else "✗")
            out += "| %s | %s | %s | %s | %d L | %d min | €%.2f |\n" % (
                ACTION_LABEL[r["action"]], mark, h(r["rul_p90_h"], horizon_h), h(r["rul_p50_h"], horizon_h),
                r["oil_l"], r["labor_min"], r["cost_eur"])
        out += "\n"

    summ = clean_text(llm.get("shift_summary"))
    if summ:
        out += "**Shift lead summary:** %s\n\n" % summ
    if not llm_ok:
        out += "*Explanation fallback used (LLM output missing or contained numbers).*\n\n"
    out += "*RUL = operating hours until the forecast reaches the %.0f %% policy limit (store closed 00:00–07:00). Model %s.*\n\n" % (
        dec["policy"]["limit_tpm"], mdl["model_version"])

    out += btn("MENU", "🛒 Next order (%s)" % fmt_clock(s["clock"])[-5:], "primary") + "\n\n"
    for v in ("F1", "C1"):
        out += " ".join([btn("ACT:%s:FILTER" % v, "%s filtered" % v, "ghost-accent"),
                         btn("ACT:%s:TOPUP" % v, "%s +2 L top-up" % v, "ghost-accent"),
                         btn("ACT:%s:CHANGE" % v, "%s oil changed" % v, "ghost-accent")]) + "\n\n"
    order = json.loads(order_json) if order_json else {}
    res_vats = {}
    for v, vo in mdl["vats"].items():
        d = dec["decisions"][v]
        best = next(r for r in d["table"] if r["action"] == d["recommended"])
        lv = llm.get(v, {}) if isinstance(llm.get(v), dict) else {}
        res_vats[v] = {
            "name": VAT_NAME[v], "status": d["status"],
            "tpm_before": vo["tpm_before"], "delta": vo["delta"], "tpm_now": vo["tpm_after"],
            "load_vs_usual_pct": None if vo["load_index"] is None else round((vo["load_index"] - 1) * 100),
            "capacity_reached": vo["capacity_reached"], "filter_active": vo["filter_active"],
            "action": d["recommended"], "action_label": ACTION_LABEL[d["recommended"]],
            "action_time": fmt_clock(best["action_time"]) if best["action_time"] is not None else None,
            "measure_again": fmt_clock(d["next_measure_at"]),
            "rul_median": h(best["rul_p50_h"], horizon_h), "rul_range": "%s - %s" % (h(best["rul_p90_h"], horizon_h), h(best["rul_p10_h"], horizon_h)),
            "why": clean_text(lv.get("reason")) or FALLBACK_REASON[d["status"]],
            "comparison": [{"action": ACTION_LABEL[r["action"]], "recommended": r["action"] == d["recommended"],
                            "allowed": r["allowed"], "safe_until": h(r["rul_p90_h"], horizon_h),
                            "median_rul": h(r["rul_p50_h"], horizon_h), "oil_l": r["oil_l"],
                            "labor_min": r["labor_min"], "cost_eur": r["cost_eur"]} for r in d["table"]],
        }
    api = {"type": "result", "screen": "result",
           "clock": fmt_clock(s["clock"]), "clock_min": s["clock"],
           "vats": {v: {"name": VAT_NAME[v], "tpm": round(s["vats"][v]["tpm"], 2),
                        "status": dec["decisions"][v]["status"],
                        "filter_active": s["vats"][v]["filter_blocks_left"] > 0} for v in s["vats"]},
           "slot": {"from": fmt_clock(mdl["block_start"]), "to": fmt_clock(mdl["clock_next"]),
                    "label": slot["label"], "typical_orders_per_15min": slot["orders_per_block"]},
           "order": {"lines": order.get("lines", []), "non_fried": order.get("non_fried", []),
                     "total_fried_kg": round(sum(l["fried_kg"] for l in order.get("lines", [])), 3)},
           "quiet_window": fmt_clock(mdl["quiet_window_start"]),
           "result": res_vats,
           "shift_summary": summ, "llm_fallback_used": not llm_ok,
           "policy_limit_tpm": dec["policy"]["limit_tpm"], "model_version": mdl["model_version"],
           "cart": [], "cart_count": 0,
           "disclaimer": "DEMO MODEL - ILLUSTRATIVE PARAMETERS - NOT FOR FOOD-SAFETY DECISIONS"}
    return {"final_md": out, "final_state": json.dumps(s), "api_json": json.dumps(api)}
