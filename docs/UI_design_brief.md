# FryWise — UI Design Brief (for Google Stitch)

> Fictional brand for a demo. Yellow-red palette is fine, but **do not use McDonald's logo, golden arches, mascots, fonts or product photos.**
> Every screen must show the banner: `DEMO MODEL — ILLUSTRATIVE PARAMETERS — NOT FOR FOOD-SAFETY DECISIONS`

---

## 1. Product in one sentence

A tablet app for a quick-service kitchen: the operator taps menu buttons to enter an order, the system estimates how much food went into each fryer, predicts frying-oil quality (TPM %), and tells the operator the next best action (continue, filter, top up, change oil) and when to measure again.

## 2. Users & device

| User | Device | Needs |
|---|---|---|
| Fryer operator | 10–11" tablet, landscape, greasy fingers | Big buttons, one glance status, one clear action |
| Shift lead / manager | Same tablet or laptop | Trend, action history, cost |

Touch targets ≥ 56 px. No keyboard input anywhere (buttons only).

## 3. Visual style

- Mood: warm, energetic, clean kitchen-display style; high contrast, readable from 1 m away.
- Shapes: rounded corners 16 px, soft shadows, card-based layout.
- Font: Inter or Poppins. Numbers (TPM %, time) in bold tabular figures.
- Icons: simple line icons (fries, drumstick, burger, oil drop, filter, clock, thermometer).

### Colour palette (yellow-red)

| Role | Name | Hex |
|---|---|---|
| Primary | Fry Red | `#D62300` |
| Primary dark | Deep Red | `#A61B00` |
| Accent | Golden Yellow | `#FFC72C` |
| Accent soft | Butter | `#FFE8A3` |
| Background | Cream | `#FFF8E7` |
| Surface (cards) | White | `#FFFFFF` |
| Text | Charcoal | `#27251F` |
| Muted text | Warm Grey | `#6B6459` |

Status colours (oil quality) — keep separate from brand red so "red = danger" stays meaningful:

| Status | Meaning | Hex |
|---|---|---|
| GREEN | Within limits | `#2E9E5B` |
| AMBER | Approaching limit, plan action | `#F28C00` |
| RED | At / near limit, change now | `#C8102E` + pulsing outline |

Tip: brand red is used for buttons/header; status red only on vat cards and alerts, always with an icon + label (not colour alone).

## 4. Global layout (landscape tablet, 1280 × 800)

```
┌─────────────────────────────────────────────────────────────────────┐
│ HEADER (red)  FryWise logo   [Order] [Vats] [History]   🕐 Day 1 12:15│
│               F1 Fries ● 18.3 %   C1 Chicken ● 18.2 %   ← top-right  │
├─────────────────────────────────────────────────────────────────────┤
│ yellow thin banner: DEMO MODEL — ILLUSTRATIVE PARAMETERS ...         │
├──────────────────────────────────────────┬──────────────────────────┤
│                                          │                          │
│          MAIN AREA (screen content)      │   RIGHT PANEL (cart /    │
│                                          │   recommendation)        │
└──────────────────────────────────────────┴──────────────────────────┘
```

**Top-right status chip (always visible):** simulated clock + one pill per vat with status dot and TPM %. Tapping a pill opens that vat's detail.

## 5. Screens

### Screen 0 — Start / choose time slot
- Title: "Choose a time slot to simulate"
- 4–5 large cards: 07:30 Breakfast · 12:00 Lunch peak · 15:00 Afternoon quiet · 18:00 Dinner peak · 21:30 Late evening
- Each card shows a small bar sparkline of typical orders per hour, peak cards marked with a red "PEAK" tag, quiet cards with a yellow "QUIET" tag.
- Footer: "Both vats start at 18 % TPM".

### Screen 1 — Order entry (main screen)
Left (≈65 %): menu grid, 3 sections with section headers
- 🍟 Fries: Frietjes Klein / Medium / Groot
- 🍗 Chicken, fish & snacks: McNuggets 6 / 9 / 20, McChicken, McCrispy, Chili Chicken, McKroket, Filet-O-Fish
- 🍔 Beef burgers: Big Mac, Quarter Pounder, Hamburger, Cheeseburger, Double Cheeseburger

Menu tile: white card, simple flat illustration (not a photo), product name, small tag showing fryer ("Fries vat" yellow tag / "Chicken vat" orange tag / "Grill – no fryer" grey tag). Tap = +1, badge shows quantity.

Right panel (≈35 %): **Cart**
- Line items with − / + steppers
- Progress indicator: "3 / 5 items — add 2 more to submit" (progress ring in yellow)
- Big red **Submit order** button, disabled (grey) until ≥ 5 items
- Secondary: "Clear cart"

Bottom strip: **Operator actions** — for each vat: [Filtered] [+2 L top-up] [Oil changed] as outline buttons with icons.

### Screen 2 — Processing (2–3 s transition)
Horizontal 4-step progress, each step lights up in sequence:
① Recipe parser → ② TPM model → ③ Policy & optimizer → ④ AI explanation
Small caption under ④: "AI explains — it never changes numbers".

### Screen 3 — Recommendation result
Top: order summary card
- Table: item · qty · fryer · fried kg; grill items greyed with "filtered out — no fryer load"
- Total fried kg in bold

Middle: two **Vat cards** side by side (F1 Fries, C1 Chicken). Each card:
- Large TPM gauge (semicircle 0–30 %, zones green < 21, amber 21–24, red ≥ 24; needle shows TPM now, ghost needle shows before)
- "18.00 % → **18.32 %**  (+0.32 this slot)"
- Chip: "Load vs usual for this slot: +144 %"
- **Action banner** (colour by status): icon + action, e.g. "Continue frying" / "Top up 2 L at 15:00" / "Change oil now"
- Rows: When · Measure again · Remaining useful life "median 19 h (18–21 h)"
- "Why" text from AI in a speech-bubble style box with small "AI" label
- Expandable "Compare actions" table: Action · Allowed ✓/✗ · Safe until · Median RUL · Oil L · Labour min · Cost €; recommended row highlighted in butter yellow

Bottom: "Shift lead summary" one-liner + big red button **Next order (12:15)**.

### Screen 4 — Vat detail / forecast
- Line chart: TPM over time (history solid, forecast dashed, P10–P90 band shaded light yellow), horizontal red line at policy limit 24 %, vertical markers for filter / top-up / change events
- Shaded vertical bands for peak hours (light red) and quiet windows (light yellow)
- Right column: current status, last measurement, next measurement, oil batch ID, hours since last filter

### Screen 5 — History & savings (manager)
- KPI tiles: Oil used (L) · TPM at discard · Early discards avoided · Est. € saved vs. fixed-schedule changes
- Timeline list of operator actions with "followed / delayed / overridden" tags
- Simple bar: "Fixed schedule vs. FryWise" oil litres per week

## 6. Components list

- Header with tab navigation + top-right status chip
- Vat status pill (dot + label + %)
- Menu tile with quantity badge and fryer tag
- Cart line item with stepper
- Progress ring "x / 5 items"
- Primary button (red, white text), secondary (white, red outline), operator action button (yellow outline + icon)
- TPM semicircle gauge with 3 zones
- Action banner (green / amber / red variants)
- AI explanation bubble
- Comparison table with highlighted row
- Forecast line chart with uncertainty band
- Demo disclaimer banner (thin yellow bar, small caps)
- Toast: "C1 oil changed — new batch at 5.0 %"

## 7. States to design

- Cart empty / 1–4 items (submit disabled) / ≥ 5 items (submit active)
- Vat GREEN / AMBER / RED (RED with pulsing border + "Change oil now" full-width button)
- Filter effect active (small filter icon + "rate reduced, 6 h left")
- AI explanation unavailable → fallback text with small "standard explanation" label
- Store closed (after 24:00) → clock jumps to "Day 2 · 07:00" with a small notice

## 8. Copy tone

Short, imperative, operator-friendly. "Change oil now", "Filter at 15:00", "Measure again 16:00". No jargon on operator screens; "TPM" is OK because the Testo meter shows it.

---

## 9. Ready-to-paste Stitch prompts

**Prompt 1 — whole app**
```
Design a landscape tablet app (1280x800) called "FryWise" for a fast-food kitchen frying-oil assistant.
Style: warm, energetic, clean kitchen-display UI. Palette: fry red #D62300, golden yellow #FFC72C,
cream background #FFF8E7, white cards, charcoal text #27251F. Rounded 16px cards, Poppins font, big touch targets.
Status colours: green #2E9E5B, amber #F28C00, danger red #C8102E.
Red header with logo, tabs (Order, Vats, History) and a top-right status chip showing a clock "Day 1 · 12:15"
and two pills "F1 Fries ● 18.3 %" and "C1 Chicken ● 18.2 %". Thin yellow banner under header:
"DEMO MODEL — ILLUSTRATIVE PARAMETERS — NOT FOR FOOD-SAFETY DECISIONS".
No real restaurant logos or mascots.
```

**Prompt 2 — order screen**
```
Order entry screen. Left 65%: menu grid with sections Fries, Chicken & snacks, Beef burgers. Each tile: flat
illustration, product name, small tag "Fries vat" (yellow), "Chicken vat" (orange) or "Grill – no fryer" (grey),
quantity badge. Right 35%: cart with steppers, a yellow progress ring "3 / 5 items – add 2 more",
a large disabled red "Submit order" button. Bottom strip: operator actions per vat: Filtered, +2 L top-up, Oil changed.
```

**Prompt 3 — recommendation screen**
```
Result screen after submitting an order. Top: compact order summary table (item, qty, fryer, fried kg; grill items greyed).
Middle: two vat cards side by side. Each has a semicircle TPM gauge 0–30% with green/amber/red zones,
"18.00 % → 18.32 % (+0.32)", a chip "Load vs usual +144 %", a coloured action banner ("Continue frying" green,
"Top up 2 L at 15:00" amber), rows for When, Measure again, Remaining useful life "median 19 h (18–21 h)",
and an AI speech bubble explaining why. Expandable action comparison table with the recommended row highlighted yellow.
Bottom: big red button "Next order (12:15)".
```

**Prompt 4 — vat forecast**
```
Vat detail screen: line chart of TPM % over time, history solid red line, forecast dashed with a light-yellow
P10–P90 band, horizontal danger line at 24 %, event markers (filter, top-up, oil change),
peak hours shaded light red and quiet windows light yellow. Right column: status, next measurement, oil batch ID.
```

Tip: generate Prompt 1 first, then add each screen as a follow-up in the same Stitch project so the style stays consistent.
