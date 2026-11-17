import json
import re

# ===== DEMO CONFIG (illustrative values, not operator-approved) =====
INITIAL_TPM = {"F1": 18.0, "C1": 18.0}   # % TPM at session start
FRESH_TPM = 5.0                           # % TPM of fresh oil
VAT_VOLUME_L = {"F1": 15.0, "C1": 15.0}
WARN_TPM = 21.0                           # display colours only; policy lives in node 3
LIMIT_TPM = 24.0
MIN_ITEMS = 5
MAX_ITEMS = 40
OPEN_MIN = 7 * 60                         # store opens 07:00
LAST_SLOT_MIN = 23 * 60 + 45              # last 15-min slot starts 23:45

MENU = [
    ("🍟 Fries", [
        ("fries_s", "Franse Frietjes Klein"),
        ("fries_m", "Franse Frietjes Medium"),
        ("fries_l", "Franse Frietjes Groot"),
    ]),
    ("🍗 Chicken, fish & snacks", [
        ("nuggets_6", "Chicken McNuggets 6"),
        ("nuggets_9", "Chicken McNuggets 9"),
        ("nuggets_20", "Chicken McNuggets 20"),
        ("mcchicken", "McChicken"),
        ("mccrispy", "McCrispy"),
        ("chili_chicken", "Chili Chicken"),
        ("mckroket", "McKroket"),
        ("filet_o_fish", "Filet-O-Fish"),
    ]),
    ("🍔 Beef burgers", [
        ("big_mac", "Big Mac"),
        ("quarter_pounder", "Quarter Pounder"),
        ("hamburger", "Hamburger"),
        ("cheeseburger", "Cheeseburger"),
        ("double_cheeseburger", "Double Cheeseburger"),
    ]),
]
NAMES = {sku: name for _, items in MENU for sku, name in items}
VAT_NAME = {"F1": "Fries vat F1", "C1": "Chicken vat C1"}
TIME_SLOTS = [("07:30", "Breakfast"), ("12:00", "Lunch peak"), ("15:00", "Afternoon quiet"),
              ("18:00", "Dinner peak"), ("21:30", "Late evening")]


def fmt_clock(t):
    day = t // 1440 + 1
    m = t % 1440
    return "Day %d · %02d:%02d" % (day, m // 60, m % 60)


def dot(tpm):
    if tpm >= LIMIT_TPM:
        return "🔴"
    if tpm >= WARN_TPM:
        return "🟠"
    return "🟢"


def status_bar(s):
    f = s["vats"]["F1"]["tpm"]
    c = s["vats"]["C1"]["tpm"]
    return ("> 🕐 **%s**　｜　%s F1 Fries **%.1f %%**　｜　%s C1 Chicken **%.1f %%**\n>\n"
            "> *DEMO MODEL — ILLUSTRATIVE PARAMETERS — NOT FOR FOOD-SAFETY OR LIVE OPERATIONAL DECISIONS*\n"
            % (fmt_clock(s["clock"]), dot(f), f, dot(c), c))


def btn(msg, label, variant="secondary"):
    return '<button data-message="%s" data-variant="%s">%s</button>' % (msg, variant, label)


def new_state():
    return {
        "started": False,
        "clock": 12 * 60,
        "cart": {},
        "vats": {v: {"tpm": INITIAL_TPM[v], "filter_blocks_left": 0} for v in INITIAL_TPM},
        "orders_submitted": 0,
    }


def mix(tpm, add_l, vol):
    return (tpm * (vol - add_l) + FRESH_TPM * add_l) / vol


def render_start(s, note):
    out = status_bar(s) + "\n"
    if note:
        out += note + "\n\n"
    out += "### 🕐 Choose the time slot to simulate\n\n"
    out += " ".join(btn("TIME:" + t, "%s · %s" % (t, lbl), "primary") for t, lbl in TIME_SLOTS) + "\n"
    return out


def render_menu(s, note):
    cart = s["cart"]
    n = sum(cart.values())
    out = status_bar(s) + "\n"
    if note:
        out += note + "\n\n"
    out += "### 🧾 Order for slot %s – %s\n\n" % (fmt_clock(s["clock"]), fmt_clock(s["clock"] + 15)[-5:])
    for title, items in MENU:
        out += "**%s**\n\n" % title
        out += " ".join(btn("ADD:" + sku, "+ " + name) for sku, name in items) + "\n\n"
    out += "**🛒 Cart (%d item%s)**\n\n" % (n, "" if n == 1 else "s")
    if n == 0:
        out += "*Empty — tap the buttons above.*\n\n"
    else:
        for sku, q in cart.items():
            out += "- %d × %s\n" % (q, NAMES[sku])
        out += "\n" + " ".join(btn("DEL:" + sku, "− " + NAMES[sku], "ghost") for sku in cart) + "\n\n"
    if n >= MIN_ITEMS:
        out += btn("SUBMIT", "✅ Submit order (%d items)" % n, "primary") + " " + btn("CLEAR", "Clear cart", "ghost") + "\n\n"
    else:
        out += "*Add %d more item%s to submit (minimum %d).*" % (
            MIN_ITEMS - n, "" if MIN_ITEMS - n == 1 else "s", MIN_ITEMS)
        if n:
            out += " " + btn("CLEAR", "Clear cart", "ghost")
        out += "\n\n"
    out += "**🧑‍🍳 Record operator action** *(applied at the current time)*\n\n"
    for v in ("F1", "C1"):
        out += " ".join([
            btn("ACT:%s:FILTER" % v, "%s filtered" % v, "ghost-accent"),
            btn("ACT:%s:TOPUP" % v, "%s +2 L top-up" % v, "ghost-accent"),
            btn("ACT:%s:CHANGE" % v, "%s oil changed" % v, "ghost-accent"),
        ]) + "\n\n"
    out += btn("RESET", "↺ Reset demo", "tertiary") + "\n"
    return out


def api(s, screen, note, route="menu"):
    vats = {}
    for v, vs in s["vats"].items():
        t = vs["tpm"]
        vats[v] = {"name": VAT_NAME[v], "tpm": round(t, 2),
                   "status": "RED" if t >= LIMIT_TPM else ("AMBER" if t >= WARN_TPM else "GREEN"),
                   "filter_active": vs.get("filter_blocks_left", 0) > 0}
    n = sum(s["cart"].values())
    return json.dumps({"type": "state", "screen": screen, "route": route, "note": note,
                       "clock": fmt_clock(s["clock"]), "clock_min": s["clock"], "vats": vats,
                       "cart": [{"sku": k, "name": NAMES[k], "qty": q} for k, q in s["cart"].items()],
                       "cart_count": n, "min_items": MIN_ITEMS, "can_submit": n >= MIN_ITEMS,
                       "menu": [{"section": t, "items": [{"sku": k, "name": nm} for k, nm in items]} for t, items in MENU],
                       "time_slots": [{"time": t, "label": l} for t, l in TIME_SLOTS],
                       "disclaimer": "DEMO MODEL - ILLUSTRATIVE PARAMETERS - NOT FOR FOOD-SAFETY DECISIONS"})


def main(query: str, state: str) -> dict:
    try:
        s = json.loads(state) if state else {}
    except Exception:
        s = {}
    if not isinstance(s, dict) or "vats" not in s:
        s = new_state()
    q = (query or "").strip()
    route = "menu"
    note = ""

    m = re.match(r"^TIME:(\d{1,2}):(\d{2})", q)
    if q.upper() == "RESET":
        s = new_state()
        nt = "Demo reset. Both vats start at %.1f %% TPM." % INITIAL_TPM["F1"]
        return {"new_state": json.dumps(s), "route": "menu", "reply_md": render_start(s, "↺ " + nt),
                "api_json": api(s, "start", nt)}
    if m:
        hm = int(m.group(1)) * 60 + int(m.group(2))
        hm = max(OPEN_MIN, min(LAST_SLOT_MIN, hm - hm % 15))
        day0 = (s["clock"] // 1440) * 1440 if s["started"] else 0
        s["clock"] = day0 + hm
        s["started"] = True
        note = "⏱ Simulated clock set to **%s**." % fmt_clock(s["clock"])
    elif not s["started"]:
        return {"new_state": json.dumps(s), "route": "menu",
                "reply_md": render_start(s, "👋 **FryWise demo.** Pick a time slot to start."),
                "api_json": api(s, "start", "Pick a time slot to start.")}
    elif q.startswith("ADD:"):
        sku = q[4:].strip()
        if sku in NAMES:
            if sum(s["cart"].values()) >= MAX_ITEMS:
                note = "⚠️ Cart limit (%d items) reached." % MAX_ITEMS
            else:
                s["cart"][sku] = s["cart"].get(sku, 0) + 1
                note = "➕ Added **%s**." % NAMES[sku]
        else:
            note = "⚠️ Unknown item."
    elif q.startswith("DEL:"):
        sku = q[4:].strip()
        if s["cart"].get(sku):
            s["cart"][sku] -= 1
            if s["cart"][sku] <= 0:
                del s["cart"][sku]
            note = "➖ Removed one **%s**." % NAMES.get(sku, sku)
    elif q.upper() == "CLEAR":
        s["cart"] = {}
        note = "🗑 Cart cleared."
    elif q.upper() == "MENU":
        note = ""
    elif q.startswith("ACT:"):
        parts = q.split(":")
        v = parts[1] if len(parts) > 1 else ""
        act = parts[2] if len(parts) > 2 else ""
        if v in s["vats"]:
            vat = s["vats"][v]
            before = vat["tpm"]
            if act == "FILTER":
                vat["filter_blocks_left"] = 32
                note = "🧑‍🍳 **%s filtered.** TPM unchanged (%.1f %%); degradation rate reduced for the next 8 operating hours." % (VAT_NAME[v], before)
            elif act == "TOPUP":
                vat["tpm"] = mix(before, 2.0, VAT_VOLUME_L[v])
                note = "🧑‍🍳 **%s topped up with 2 L fresh oil.** TPM %.1f %% → %.1f %% (volume-weighted mix)." % (VAT_NAME[v], before, vat["tpm"])
            elif act == "CHANGE":
                vat["tpm"] = FRESH_TPM
                vat["filter_blocks_left"] = 0
                note = "🧑‍🍳 **%s oil changed.** New oil batch started at %.1f %% TPM." % (VAT_NAME[v], FRESH_TPM)
    elif q.upper() == "SUBMIT":
        n = sum(s["cart"].values())
        if n >= MIN_ITEMS:
            return {"new_state": json.dumps(s), "route": "submit", "reply_md": "", "api_json": ""}
        note = "⚠️ At least %d items are needed to submit (cart has %d)." % (MIN_ITEMS, n)
    else:
        note = "⚠️ Free text is not accepted in this demo — please use the buttons."

    plain = note.replace("**", "")
    return {"new_state": json.dumps(s), "route": route, "reply_md": render_menu(s, note),
            "api_json": api(s, "menu", plain)}
