# Restaurant Frying-Oil Management Program

## Overview

This project describes a data-driven frying-oil management program for a standardized quick-service restaurant environment such as McDonald's.

The program is intended to help restaurant teams answer four operational questions:

1. When should frying oil be measured?
2. When should a fryer vat be filtered?
3. When should fresh oil be added or part of the oil be replaced?
4. When should the oil be completely discarded and replaced?

The proposed system combines frying-oil quality readings, point-of-sale demand, fixed product recipes, fryer operating data, oil-maintenance events, and predictive models. The goal is to provide a simple next-best action to a frying operator while protecting food quality, food safety, and operational continuity.

> **Important:** This repository is a concept and demo specification. Synthetic-data models and prototype recommendations must not be used for live food-safety or oil-discard decisions. Legal limits, corporate standards, operating procedures, and approved measurement methods must be defined by the restaurant operator and relevant food-safety specialists.

---

## 1. Business Problem

Restaurants often replace frying oil too early or continue using it for too long.

Replacing oil too early can cause:

- Unnecessary fresh-oil consumption
- Higher operating cost
- More waste-oil handling
- Avoidable environmental impact

Using oil for too long can cause:

- Inconsistent color, flavor, crispness, and greasiness
- Increased food-quality risk
- Oil-quality non-compliance
- Customer complaints and product remakes

A useful system should not merely display a Total Polar Materials reading. A useful system should translate current oil condition and expected frying demand into an operational recommendation.

Example output:

```text
Vat 2
Current TPM: 21.4%
Recommended action: Filter after the lunch peak
Recommended window: 14:10–14:30
Measure again: 16:30
Reason: Breaded-product load is above normal and the last filtration was eight hours ago
Expected oil-life extension: 4–6 hours
Confidence: Medium
```

---

## 2. Core Design Principle

The program should digitize the complete lifecycle of the oil in each fryer vat:

```text
Fresh fill
→ frying load
→ measurement
→ filtration
→ top-up
→ partial replacement
→ further frying
→ full replacement
```

The analytical chain is:

```text
POS sales
→ estimated production demand
→ reconstructed frying events
→ oil stress
→ TPM degradation trajectory
→ remaining useful life
→ next-best action
→ operator action
→ measured outcome
```

The system must preserve a separate `oil_batch_id` for every oil lifecycle. A full oil change starts a new batch.

---

## 3. Why Fixed Recipes Make POS Data Valuable

In a standardized restaurant chain, product recipes and operating specifications are relatively stable. For each fried product, the program can maintain master data such as:

- Product identifier
- Fried mass per serving
- Standard frying time
- Approved fryer or vat family
- Standard basket capacity
- Holding-time rule
- Breading or batter factor
- Moisture factor
- Crumb-generation factor
- Estimated oil absorption

This allows theoretical frying demand to be calculated from POS sales:

```text
Theoretical fried mass
= POS quantity × fried mass per unit
```

For multiple products:

```text
EstimatedFriedKg(vat, time)
= sum(POS units × mass per unit × routing share)
```

However, POS data do not reveal the exact moment when food entered the fryer. Products are commonly cooked in batches before they are sold. Waste, remakes, staff meals, ending stock, and temporary vat-routing changes also create differences between sales and physical production.

The central data-science problem is therefore not only estimating **how much** was fried. It is reconstructing **when**, **in which vat**, and **in what batch size** the product was fried.

---

## 4. Required Data

### 4.1 Oil-quality measurements

Each measurement should include:

| Field | Description |
|---|---|
| `measurement_id` | Unique measurement identifier |
| `measurement_timestamp` | Date and time of measurement |
| `store_id` | Restaurant identifier |
| `fryer_id` | Fryer identifier |
| `vat_id` | Vat identifier |
| `oil_batch_id` | Current oil lifecycle identifier |
| `tpm_pct` | Total Polar Materials percentage |
| `oil_temperature_c` | Oil temperature at measurement |
| `device_id` | TPM meter identifier |
| `operator_id_hash` | Pseudonymized operator identifier |
| `measurement_validity_flag` | Valid or invalid reading |
| `device_calibration_date` | Most recent calibration or check date |

### 4.2 POS sales

| Field | Description |
|---|---|
| `transaction_timestamp` | Sale time |
| `store_id` | Restaurant identifier |
| `sku_id` | Product identifier |
| `quantity` | Units sold |
| `order_channel` | Counter, kiosk, delivery, drive-through, etc. |
| `promotion_flag` | Promotion indicator |
| `void_or_refund_flag` | Cancelled or refunded item |
| `daypart` | Breakfast, lunch, dinner, late night |

### 4.3 Product recipe and fryer-routing master

| Field | Description |
|---|---|
| `sku_id` | Product identifier |
| `product_name` | Product description |
| `fried_mass_kg_per_unit` | Physical input weight per sold unit |
| `vat_family` | Approved fryer/vat group |
| `standard_fry_time_sec` | Standard cooking duration |
| `standard_batch_capacity` | Units or kilograms per full basket |
| `maximum_holding_time_min` | Approved holding window |
| `breading_factor` | Relative breading/batter load |
| `moisture_factor` | Relative moisture load |
| `crumb_factor` | Relative crumb generation |
| `oil_absorption_rate` | Estimated oil removal with product |
| `pos_to_fry_lag_min` | Initial time-lag assumption |

### 4.4 Fryer operating data

| Field | Description |
|---|---|
| `timestamp` | Event or interval timestamp |
| `fryer_id` | Fryer identifier |
| `vat_id` | Vat identifier |
| `product_program` | Selected cooking program |
| `fry_start_timestamp` | Cycle start |
| `fry_end_timestamp` | Cycle end |
| `set_temperature_c` | Temperature setting |
| `actual_temperature_c` | Measured oil temperature |
| `basket_count` | Number of cycles or baskets |
| `idle_hot_minutes` | Hot time without production |
| `overtemperature_minutes` | Time above approved range |
| `equipment_alarm` | Equipment issue indicator |

Fryer-controller event logs are the preferred source. If controller data are unavailable, a short-term basket-event logging process can be used in calibration stores.

### 4.5 Oil-management actions

| Field | Description |
|---|---|
| `action_timestamp` | Time of action |
| `vat_id` | Affected vat |
| `oil_batch_id` | Affected oil lifecycle |
| `action_type` | Filter, top-up, partial replace, full change, clean |
| `fresh_oil_added_l` | Liters of fresh oil added |
| `oil_removed_l` | Liters removed |
| `filter_duration_min` | Filtration duration |
| `filter_type` | Filtration equipment/method |
| `reason_code` | TPM, schedule, quality issue, etc. |
| `action_completed` | Completion status |
| `operator_id_hash` | Pseudonymized responsible operator |

### 4.6 Waste, remakes, and holding stock

| Field | Description |
|---|---|
| `sku_id` | Product identifier |
| `timestamp` | Event time |
| `waste_quantity` | Product discarded |
| `remake_quantity` | Additional production not represented by a new sale |
| `opening_holding_stock` | Available cooked inventory at start of interval |
| `closing_holding_stock` | Available cooked inventory at end of interval |

### 4.7 Value and outcome data

| Field | Description |
|---|---|
| `fresh_oil_used_l` | Fresh oil consumed |
| `discarded_oil_l` | Oil discarded |
| `oil_price_per_l` | Oil cost |
| `measurement_minutes` | Labor used for measurement |
| `filter_minutes` | Labor used for filtering |
| `change_oil_minutes` | Labor used for replacement |
| `downtime_minutes` | Fryer unavailable time |
| `product_quality_score` | Approved quality indicator |
| `remake_count` | Product remakes |
| `quality_complaint_count` | Relevant complaints |
| `recommended_action` | System recommendation |
| `operator_action` | Actual action |
| `action_delay_minutes` | Delay versus recommendation |
| `override_reason` | Reason for not following recommendation |

---

## 5. Reconstructing Frying Events from POS

### 5.1 Preferred hierarchy of evidence

Use the strongest available source:

1. Fryer-controller cycle logs
2. Kitchen-production-system events
3. One-tap basket event logging
4. POS plus calibrated batch reconstruction
5. POS plus a fixed time-shift kernel for an early demo

### 5.2 Short-term calibration study

Select approximately 5–10 restaurants for 4–8 weeks. Record actual fry events using fryer logs or a minimal interface with buttons for:

- Product family
- Vat
- Full basket
- Half basket
- Custom batch
- Waste/remake

Logging must take roughly one or two seconds per batch to remain practical during peak periods.

### 5.3 Time-shift kernel

When no direct fry event exists, estimate the probability that a sale was produced a number of minutes earlier:

```text
P(fry time = sale time − lag | product, store, daypart)
```

POS demand can then be shifted backward in time:

```text
EstimatedFryLoad(product, time)
= sum(future POS units × lag probability × mass per unit)
```

The lag distribution should be learned separately by product family, restaurant format, daypart, and demand level.

### 5.4 Batch reconstruction

Production is discrete, not continuous. A reconstruction model should respect:

- Basket capacity
- Frying duration
- Vat capacity
- Holding-time limits
- Opening and closing holding stock
- Waste and remakes
- Approved product routing

The inventory balance is:

```text
Production
= Sales + Waste + Closing Stock − Opening Stock
```

A first implementation can use deterministic heuristics. Later versions can use a state-space model, particle filter, mixed-integer optimization, or OR-Tools CP-SAT.

---

## 6. Oil-Stress Model

Different products do not place the same load on oil. A weighted oil-stress feature can be estimated as:

```text
OilStress(time)
= sum(FriedKg(product, time) × StressWeight(product))
```

An initial stress weight can combine:

```text
StressWeight
= 1
+ alpha × breading factor
+ beta × moisture factor
+ gamma × crumb factor
```

The coefficients should initially be defined with food-science and operations experts, then calibrated using observed TPM trajectories.

---

## 7. Synthetic Data for a Demo

Synthetic data should be produced by a Python simulator, not by asking a language model to manually write a CSV.

Recommended demo scope:

- 10 restaurants
- 3 vats per restaurant
- 30 operating days
- 15-minute intervals
- Multiple dayparts and weekday/weekend patterns
- Store-specific demand and oil-degradation effects
- Filters, top-ups, partial replacements, and full changes
- Sensor noise and realistic missing records

A simplified hidden-state equation is:

```text
TPM(t+1)
= TPM(t)
+ degradation(t)
− dilution(t)
+ process noise
```

Degradation can depend on:

- Fried kilograms
- Breaded-product load
- Moisture load
- Crumb load
- Oil temperature
- Idle hot time
- Time above temperature range
- Oil age
- Oil type
- Store and vat effects
- Recent filtration

Filtering should mainly reduce crumb load and the subsequent degradation rate. Filtering should not reset chemically degraded oil to fresh-oil condition.

Top-up and partial replacement should follow a volume-weighted mixing equation:

```text
TPM_new
= (TPM_old × remaining old oil volume
   + TPM_fresh × fresh oil added)
  / total oil volume
```

The demo must be clearly labeled:

```text
DEMO MODEL — TRAINED ON SYNTHETIC DATA
NOT FOR FOOD-SAFETY OR LIVE OPERATIONAL DECISIONS
```

---

## 8. TPM Trajectory Model

### 8.1 Recommended initial model

Start with interpretable tabular models such as:

- Generalized Additive Model
- LightGBM
- XGBoost
- Random Forest
- Mixed-effects regression

Do not begin with an LSTM or Transformer unless the volume, regularity, and quality of real time-series data justify the added complexity.

### 8.2 Example features

Current state:

- Current TPM
- Oil temperature
- Oil age
- Oil volume
- Hours since filtration
- Hours since top-up
- Hours since full replacement

Rolling demand and stress:

- Fried kilograms in the last hour
- Fried kilograms in the last four hours
- Breaded-product kilograms
- Moisture load
- Crumb load
- Idle hot minutes
- Mean and maximum temperature
- Recent TPM slope

Context:

- Oil type
- Vat capacity
- Fryer model
- Product family
- Restaurant demand band
- Daypart
- Weekday/weekend

### 8.3 Validation design

Do not randomly split individual rows from the same oil lifecycle between training and test sets.

Use grouped validation by:

- Oil batch
- Restaurant
- Fryer/vat
- Time period

A robust test should measure performance on restaurants or oil batches not seen in training.

---

## 9. Remaining Useful Life

Remaining Useful Life, or RUL, is the expected time until the predicted oil-quality trajectory reaches an approved action threshold.

```text
RUL
= first predicted threshold-crossing time − current time
```

The threshold must come from approved local policy and food-safety governance. A model or language model must never invent or override the threshold.

The system should return a range rather than a single precise number:

```text
Median RUL: 8 hours
Likely range: 6–11 hours
Probability of crossing before dinner close: 72%
Recommended next measurement: 18:00
```

Uncertainty can be estimated with quantile models, bootstrap ensembles, or calibrated probabilistic methods.

Future demand must be represented by a scenario:

- Quiet shift
- Expected shift
- Busy shift
- Forecast from historical POS
- Custom demand entered in a demo

---

## 10. Action Simulation

The system should compare counterfactual actions:

```text
Scenario A: Do nothing
Scenario B: Filter now
Scenario C: Add fresh oil
Scenario D: Partially replace oil
Scenario E: Fully replace oil
```

For each action, estimate:

- Median RUL
- RUL range
- Oil used immediately
- Labor time
- Service downtime
- Oil-quality risk
- Expected oil-life extension

Example:

| Action | Median RUL | Oil used now | Labor | Risk |
|---|---:|---:|---:|---|
| Do nothing | 5.5 hours | 0 L | 0 min | Medium |
| Filter now | 10.5 hours | 0 L | 12 min | Low |
| Top up 2 L | 8.5 hours | 2 L | 4 min | Low |
| Partial replacement | 14 hours | 5 L | 15 min | Low |

---

## 11. Decision Architecture

The recommendation system should contain three layers.

### Layer 1: Safety and policy rules

Deterministic rules enforce approved limits and prohibited actions. The predictive model cannot override these rules.

### Layer 2: Prediction

The model forecasts:

- TPM trajectory
- Threshold-crossing probability
- Remaining Useful Life
- Abnormal degradation

### Layer 3: Optimization

The optimizer selects the lowest-cost compliant action, considering:

- Fresh-oil cost
- Labor
- Downtime
- Product quality
- Food-safety risk
- Expected demand
- Availability of filtering and replacement windows

A language model may explain the result, but must not calculate TPM, RUL, safety status, or savings independently.

---

## 12. Operator and Manager Experience

### Operator view

Show only information needed for action:

- Current vat status
- Recommended action
- Recommended time window
- Short reason
- Next measurement time
- Expected benefit
- Confidence

Operator actions:

- Completed
- Delayed
- Re-measured
- Oil changed
- Report issue
- Override with reason

### Restaurant manager view

- Oil liters per 1,000 fried items
- TPM at discard
- Early discard rate
- Above-limit events
- Filter compliance
- Oil cost per sales volume
- Product-quality incidents
- Data-quality issues

### Area or chain view

- Adjusted restaurant comparisons
- Oil-use variance
- Predicted versus actual oil life
- Filter effectiveness
- Recoverable cost
- Training needs
- Equipment outliers
- Model drift

---

## 13. Pilot Plan

### Scope

- 10–20 restaurants
- 2–4 vats per restaurant
- 8–12 weeks
- High-, medium-, and low-volume locations
- Multiple product mixes

### Phase 1: Baseline

Weeks 1–2:

- Collect data
- Do not change the operating procedure
- Measure data completeness and consistency

### Phase 2: Digital measurement and visibility

Weeks 3–4:

- Introduce digital TPM records
- Standardize vat, device, and oil-batch identification
- Monitor measurement compliance

### Phase 3: Low-risk recommendations

Weeks 5–8:

- Recommend measurement times
- Recommend filtration windows
- Flag missed operating procedures
- Provide replacement preparation alerts
- Keep approved discard rules deterministic

### Phase 4: Personalized optimization

Weeks 9–12:

- Use restaurant- and vat-specific calibration
- Compare counterfactual actions
- Measure oil, labor, quality, and compliance outcomes

A stepped-wedge design can introduce recommendations to different restaurant groups at different times, helping distinguish program impact from seasonality and sales changes.

---

## 14. Key Performance Indicators

### Oil efficiency

```text
Oil Efficiency
= kilograms of food fried / liters of fresh oil used
```

### Oil cost intensity

```text
Oil Cost per 1,000 Items
= oil cost / fried items × 1,000
```

### Early discard rate

```text
Early Discard Rate
= oil-change events below the approved target band
  / all oil-change events
```

### Above-limit rate

```text
Above-Limit Rate
= measurements above the approved limit
  / all valid measurements
```

### Recommendation compliance

- Recommendation accepted
- Action completed within recommended window
- Delay
- Override reason

### RUL accuracy

- Median absolute error in hours
- Threshold crossing precision and recall
- False-safe rate
- Probability calibration

### Quality guardrails

- Product color
- Crispness
- Greasiness
- Off-flavor
- Remakes
- Waste
- Customer complaints

### Financial value

```text
Net Value
= Oil cost avoided
+ Labor value
+ Waste avoided
− Hardware
− Software
− Integration
− Training
− Support
```

---

## 15. Technology Stack for a Demo

A lightweight prototype can use:

- **Jupyter Notebook** for simulation, feature engineering, model training, and charts
- **Python** with pandas, NumPy, scikit-learn, LightGBM, or XGBoost
- **FastAPI** to expose trajectory, RUL, and action-simulation endpoints
- **Dify** to orchestrate prediction APIs, policy rules, SOP retrieval, and explanation
- **Google AI Studio / Gemini** to prototype the interface and generate role-specific explanations

Suggested APIs:

```text
POST /predict-trajectory
POST /predict-rul
POST /simulate-actions
POST /record-operator-action
```

The language-model instruction should include:

```text
Never calculate TPM, Remaining Useful Life, safety status, or savings independently.
Use only values returned by the approved prediction and policy APIs.
Do not override an approved oil-quality threshold.
If required data are missing, state that a recommendation cannot be determined.
```

---

## 16. Data Quality Controls

The system should flag:

- TPM measurement during active frying
- Measurement outside the approved temperature range
- Dirty or uncalibrated sensor
- Wrong-vat selection
- Duplicate readings
- Unrecorded top-up
- Oil transfer between vats
- Missing filtration record
- Sensor drift
- Full replacement without a new oil-batch identifier

Recommended safeguards:

- QR or NFC identification for each vat
- Device identifiers
- Calibration history
- Volume balance checks
- Oil-batch lifecycle checks
- Automated anomaly detection
- A short operator correction workflow

---

## 17. Privacy, Security, and Governance

The project should minimize personal data.

- Pseudonymize operator identifiers
- Do not use facial recognition
- Limit camera pilots to detecting baskets, fryers, and production events
- Define retention periods
- Apply role-based access
- Encrypt data in transit and at rest
- Maintain audit logs
- Separate demo, test, and production environments
- Define model, data, and product owners
- Monitor data drift and model performance
- Maintain manual fallback and incident procedures

Local legal, works-council, franchise, cybersecurity, and food-safety requirements must be reviewed before a live pilot.

---

## 18. Main Risks

| Risk | Mitigation |
|---|---|
| POS does not equal actual production | Calibrate with fryer or basket events |
| Operators do not record actions | Use one-tap event capture and automate where possible |
| Sensor readings are inconsistent | Standard procedure, calibration, and validity rules |
| Model appears accurate only on synthetic data | Silent real-data validation before recommendations |
| Oil savings reduce product quality | Maintain quality and safety guardrails |
| Recommendations are ignored | Design with operators and line managers; track override reasons |
| Filtering effect is overstated | Learn subsequent degradation change from observed data |
| Site differences reduce model accuracy | Use hierarchical or site-aware models and local recalibration |
| Dashboard adds work | Replace existing recording steps rather than adding another layer |
| Vendor lock-in | Use standard APIs, exportable data, documentation, and exit provisions |

---

## 19. Recommended Delivery Sequence

```text
1. Define approved oil-quality policy and operating decisions
2. Build the data model and restaurant/vat/oil identifiers
3. Produce synthetic data and demonstrate the architecture
4. Connect TPM and POS data in calibration restaurants
5. Capture temporary fryer/basket ground truth
6. Build and validate the POS-to-frying reconstruction model
7. Build the TPM trajectory and RUL models
8. Run predictions silently against actual outcomes
9. Introduce low-risk operator recommendations
10. Evaluate oil, labor, quality, adoption, and safety outcomes
11. Scale only if economic and operating thresholds are met
```

---

## 20. Success Definition

The program succeeds only if it produces measurable operational improvement without weakening food quality or safety.

Successful outcomes should include:

- Fewer premature oil changes
- No increase in above-limit oil use
- Better filtration timing
- Lower fresh-oil use per unit of fried food
- Stable or improved food quality
- Low operator burden
- Accurate and calibrated RUL predictions
- Clear financial value after full implementation and support cost
- A scalable data and operating model that can work across restaurant formats

The strategic capability is not the TPM sensor by itself. The strategic capability is the closed learning loop:

```text
Demand
→ production
→ oil degradation
→ action
→ measured effect
→ better recommendation
```

---

## Disclaimer

All thresholds, product values, fryer-routing assumptions, time ranges, costs, and numerical examples in this document are illustrative unless validated by the restaurant operator. The document contains no confidential information from any food manufacturer, supplier, or internal corporate system.
