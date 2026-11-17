# FryWise — Slide Brief for Microsoft Copilot (5 slides)

---

## MASTER PROMPT (paste this into Copilot together with this file)

```
Create a 5-slide PowerPoint presentation from the attached document "FryWise — Slide Brief".
Audience: restaurant operations managers, franchisees and business-school reviewers. Language: English.
Use exactly the 5 slides described in the section "SLIDE CONTENT", in that order, with the given titles.
Style: clean, modern, warm colours — red #D62300, golden yellow #FFC72C, cream background #FFF8E7,
charcoal text #27251F. One idea per slide, max 6 bullets per slide, max 12 words per bullet.
Use simple icons (fries, oil drop, chart, gear, shield). Use a flow diagram on slide 2 and slide 3
and a 3-column layout on slide 4. Put the speaker notes from each slide into the notes section.
Do not use any real restaurant brand logos, mascots or product photos.
Add a small footer on every slide: "Demo prototype — illustrative parameters, not for food-safety decisions".
```

---

## BACKGROUND (for Copilot context — do not create extra slides from this)

FryWise is a demo prototype of a frying-oil decision-support system for quick-service restaurants.
It connects three data sources — oil-quality readings (Total Polar Materials, TPM %, from a handheld
Bluetooth tester such as the Testo 270 BT), point-of-sale orders, and fixed product recipes — and turns
them into one simple instruction for the fryer operator: continue, filter, top up, or change the oil,
plus when to measure again.

The demo runs as: Google AI Studio front end (tablet UI designed in Google Stitch) → Dify chatflow
back end (Python code nodes + one LLM node). All numbers come from deterministic code; the LLM only
writes the explanation and is blocked from writing numbers.

---

## SLIDE CONTENT

### Slide 1 — The Problem: Frying Oil Is Managed by Habit, Not Data

**Bullets**
- Oil is often changed on a fixed schedule, not on actual condition
- Changed too early → wasted oil, higher cost, more waste handling
- Changed too late → inconsistent taste, colour and crispness; compliance risk
- Many European countries enforce TPM limits around 24–27 %
- A TPM reading alone does not tell staff *what to do next*
- Opportunity: turn demand data into oil decisions

**Speaker notes**
Restaurants face a trade-off every day. Replace the oil too early and you throw away usable oil;
replace it too late and food quality and compliance suffer. A tester can show today's TPM value,
but it does not predict how fast the oil will degrade during the lunch or dinner peak. FryWise
closes that gap by connecting oil readings with what is actually being sold and fried.

---

### Slide 2 — The Solution: From POS Order to Next Best Action

**Visual:** left-to-right flow diagram with 5 boxes:
`POS order` → `Recipe parser` → `TPM prediction model` → `Policy & optimizer` → `Operator action`

**Bullets**
- Every sold item is mapped to fried weight via the fixed recipe table
- Non-fried items (e.g. grilled beef burgers) are filtered out automatically
- Model forecasts TPM per vat and remaining useful life with a range
- Safety rules decide which actions are allowed
- Optimizer picks the lowest-cost safe action and the best time window
- Operator sees one instruction: action, time, next measurement

**Speaker notes**
In a standardized chain, recipes are fixed, so a sale of large fries or nine nuggets translates
directly into kilograms in a specific fryer vat. Breaded products stress oil more than fries, so each
product has a stress weight. The model then forecasts the TPM trajectory, and the system recommends
the cheapest action that keeps the oil within the approved limit — for example, topping up in the next
quiet window instead of a full change during the dinner rush.

---

### Slide 3 — How the Demo Is Built

**Visual:** two-layer architecture diagram
- Top: "Tablet UI — Google AI Studio (React), designed in Google Stitch"
- Arrow: "Button commands only (no free text)"
- Bottom: "Dify chatflow back end" with 5 steps:
  ① State & cart → ② Recipe parser → ③ TPM model → ④ Policy rules + optimizer → ⑤ LLM explanation (no numbers) + validation

**Bullets**
- Button-only ordering; minimum five hot items per submission
- Simulated clock compares each order with historical peak and quiet slots
- Three decision layers: safety rules → prediction → cost optimization
- LLM explains decisions but cannot change actions or numbers
- Output validated: any number in LLM text triggers a safe fallback
- Operator buttons (filtered / top-up / oil changed) close the feedback loop

**Speaker notes**
The architecture is deliberately conservative. Python code calculates every number; the language model
only writes a short, operator-friendly reason. If the model's text contains any number, the system
discards it and uses a standard explanation. This keeps food-safety decisions deterministic, auditable
and explainable — which is what operations and compliance teams need before trusting an AI tool.

---

### Slide 4 — Practical Value

**Visual:** 3 columns with icons

**Column 1 — Cost & sustainability (oil drop icon)**
- Use oil until its real limit, not the calendar
- Fewer premature changes, less fresh-oil purchase
- Less waste oil to handle and transport

**Column 2 — Food quality & compliance (shield icon)**
- Early warning before the TPM limit is reached
- Consistent taste, colour and crispness
- Automatic digital record of readings and actions

**Column 3 — Operations (gear icon)**
- Filtering and changes scheduled in quiet windows, not peaks
- Fewer unnecessary measurements; clear "measure again" time
- One simple instruction per vat for busy staff

**Speaker notes**
The value is not the sensor itself; it is the decision. FryWise tells the crew what to do and when,
so oil changes move out of the rush hour and oil is not discarded while it is still within limits.
For the manager, every reading and action is recorded automatically, supporting food-safety audits.
Savings figures will be quantified in the pilot; the demo uses illustrative parameters.

---

### Slide 5 — Roadmap: From Demo to Pilot

**Visual:** horizontal timeline with 4 phases

- **Phase 1 – Demo (now):** synthetic data, illustrative model parameters, full UI and decision flow
- **Phase 2 – Calibration (60 days, 1–3 stores):** daily TPM readings + staff fry logs + POS export
- **Phase 3 – Silent validation:** predictions run in the background and are compared with real readings
- **Phase 4 – Live recommendations & scale:** store-specific models, multi-store dashboard, oil purchasing forecasts, ESG reporting

**Success criteria**
- Fewer premature oil changes, no increase in above-limit use
- Stable or better food-quality scores
- Low staff burden (one-tap actions)
- Clear net value after hardware, software and training costs

**Speaker notes**
The next step is a small, low-risk pilot. Staff record fry events for 60 days so the model can learn
the gap between POS sales and actual frying. Predictions then run silently before any recommendation
reaches the crew. Only when accuracy and value are proven do we switch on live recommendations and
expand to a multi-store platform for franchisees and head office.
