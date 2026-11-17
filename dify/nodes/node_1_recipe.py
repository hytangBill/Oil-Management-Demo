import json

# ===== RECIPE / FRYER-ROUTING MASTER (demo values) =====
# fried_g: grams of product that goes into the fryer per sold unit.
#   "portion"  = whole published portion weight is the fried item (fries, nuggets)
#   "estimate" = fried component not published; illustrative estimate
#   "grill"    = beef patty is cooked on the grill, not in a fryer -> 0 g
# stress: relative oil-stress weight per kg (1.0 = fries; breaded/crumbed items stress oil more)
# fry_input_factor: served weight -> raw input weight (1.0 until calibrated in pilot)
RECIPE = {
    "fries_s":             {"name": "Franse Frietjes Klein",  "family": "fries",   "fried_g": 80,  "stress": 1.0, "basis": "portion"},
    "fries_m":             {"name": "Franse Frietjes Medium", "family": "fries",   "fried_g": 114, "stress": 1.0, "basis": "portion"},
    "fries_l":             {"name": "Franse Frietjes Groot",  "family": "fries",   "fried_g": 150, "stress": 1.0, "basis": "portion"},
    "nuggets_6":           {"name": "Chicken McNuggets 6",    "family": "chicken", "fried_g": 109, "stress": 1.3, "basis": "portion"},
    "nuggets_9":           {"name": "Chicken McNuggets 9",    "family": "chicken", "fried_g": 163, "stress": 1.3, "basis": "portion"},
    "nuggets_20":          {"name": "Chicken McNuggets 20",   "family": "chicken", "fried_g": 362, "stress": 1.3, "basis": "portion"},
    "mcchicken":           {"name": "McChicken",              "family": "chicken", "fried_g": 90,  "stress": 1.3, "basis": "estimate"},
    "mccrispy":            {"name": "McCrispy",               "family": "chicken", "fried_g": 120, "stress": 1.4, "basis": "estimate"},
    "chili_chicken":       {"name": "Chili Chicken",          "family": "chicken", "fried_g": 60,  "stress": 1.3, "basis": "estimate"},
    "mckroket":            {"name": "McKroket",               "family": "chicken", "fried_g": 100, "stress": 1.5, "basis": "estimate"},
    "filet_o_fish":        {"name": "Filet-O-Fish",           "family": "chicken", "fried_g": 55,  "stress": 1.2, "basis": "estimate"},
    "big_mac":             {"name": "Big Mac",                "family": None,      "fried_g": 0,   "stress": 0.0, "basis": "grill"},
    "quarter_pounder":     {"name": "Quarter Pounder",        "family": None,      "fried_g": 0,   "stress": 0.0, "basis": "grill"},
    "hamburger":           {"name": "Hamburger",              "family": None,      "fried_g": 0,   "stress": 0.0, "basis": "grill"},
    "cheeseburger":        {"name": "Cheeseburger",           "family": None,      "fried_g": 0,   "stress": 0.0, "basis": "grill"},
    "double_cheeseburger": {"name": "Double Cheeseburger",    "family": None,      "fried_g": 0,   "stress": 0.0, "basis": "grill"},
}
FRY_INPUT_FACTOR = 1.0
FAMILY_LABEL = {"fries": "Fries vats", "chicken": "Chicken vats", None: "— (not fried)"}


def main(new_state: str) -> dict:
    s = json.loads(new_state)
    cart = s.get("cart", {})
    lines = []
    per_family = {"fries": {"kg": 0.0, "stress_kg": 0.0}, "chicken": {"kg": 0.0, "stress_kg": 0.0}}
    non_fried = []
    for sku, qty in cart.items():
        r = RECIPE.get(sku)
        if r is None or qty <= 0:
            continue
        kg = qty * r["fried_g"] * FRY_INPUT_FACTOR / 1000.0
        stress_kg = kg * r["stress"]
        lines.append({"sku": sku, "name": r["name"], "qty": qty, "family": r["family"],
                      "fried_kg": round(kg, 3), "stress_kg": round(stress_kg, 3), "basis": r["basis"]})
        if r["family"]:
            per_family[r["family"]]["kg"] += kg
            per_family[r["family"]]["stress_kg"] += stress_kg
        else:
            non_fried.append("%d × %s" % (qty, r["name"]))
    for f in per_family:
        per_family[f] = {k: round(v, 3) for k, v in per_family[f].items()}

    md = "| Item | Qty | Fryer | Fried kg | Basis |\n|---|---:|---|---:|---|\n"
    for l in lines:
        md += "| %s | %d | %s | %.3f | %s |\n" % (l["name"], l["qty"], FAMILY_LABEL[l["family"]], l["fried_kg"], l["basis"])
    md += "| **Total fried** | | | **%.3f** | |\n" % (per_family["fries"]["kg"] + per_family["chicken"]["kg"])
    if non_fried:
        md += "\n🔎 Filtered out by the recipe table (grill, no fryer load): %s\n" % ", ".join(non_fried)

    order = {"lines": lines, "per_family": per_family, "non_fried": non_fried,
             "total_items": sum(l["qty"] for l in lines)}
    return {"order_json": json.dumps(order), "order_md": md}
