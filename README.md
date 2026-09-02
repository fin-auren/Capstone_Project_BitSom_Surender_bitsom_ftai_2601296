

## Setup

```bash
git clone <this-repo-url>
cd <this-repo>
python -m venv venv && source venv/bin/activate     # optional but recommended
pip install -r requirements.txt                      # one consolidated file for all 3 parts
```

Only one `requirements.txt`, at the repo root, is used for all three parts (`pandas`, `numpy`,
`openpyxl`, `matplotlib`, `scikit-learn`) -- there are no part-specific requirement files.

## How to run each part end to end

**Part 1** (run generate_data.py from inside the folder -- it writes CSVs via relative paths):

```bash
cd payments_fraud_analytics
python generate_data.py
python build_workbook.py
python build_db_and_queries.py
python reconcile.py
python dashboard.py
cd ..
```

**Part 2** (also run generate_data.py from inside the folder):

```bash
cd credit_risk_lending_ml
python generate_data.py
python credit_risk_pipeline.py
cd ..
```

**Part 3** (independent scripts, no seed-data generator needed -- data is committed as
ready-to-run Python dicts/lists):

```bash
cd ai_advisory_blockchain
python advisory_agent.py
python extract_disclosure.py
python debate.py
python dcf_calculator.py
cd ..
```

Each part's own `README.md` has the full command list plus its detailed design-decision
write-up; this root README summarizes the highlights below.

## Design-decision summary

### Part 1 -- Payments & Fraud Analytics
- **Excel workbook** (`merchant_workbook.xlsx`): fixed-range `VLOOKUP` + `IFERROR` (with a
  synthetic demo row proving the "Merchant not found" path), an `HLOOKUP` fee-tier demo, a
  nested `IF/AND` "High-Value Merchant Day" classification (`merchant_day_total_inr > 5000 AND
  region <> "East"`), and a formula-driven (`SUMIFS`/`COUNTIFS`) pivot-style summary with a
  count-vs-unique-days comparison for 5 merchants -- documented in the workbook's own `Notes`
  sheet, since openpyxl cannot reliably author a native Excel PivotTable object.
- **SQL** (`paytm_payments.db`): normalized 3-table schema with declared PK/FK; 7 queries cover
  every required clause and both join types; the burner-account query surfaces all 15 seeded
  rows and the velocity-attack query surfaces all 8 seeded clusters exactly.
- **Reconciliation** (`reconcile.py`): `reconcile_payments()` returns all four discrepancy
  categories via set operations + `pd.merge`; measured rates (4.94% / 1.83% / 2.93% / 1.65%)
  track the injected 5%/2%/3%/2% rates.
- **Dashboard** (`dashboard.py`): four saved-image layers (headline scorecards, GMV/chargeback
  trend, method/category breakdown, flagged top-10-merchant table) each with a written
  interpretation in `dashboard_interpretations.md`.

### Part 2 -- Credit Risk & Lending ML
- **Leak-safe preprocessing:** `is_thin_file` engineered pre-split from raw missingness; 75/25
  stratified split (`random_state=42`); bureau-score median imputation computed from the
  training split only, then applied to both splits; `StandardScaler` also fit train-only.
- **Models:** Logistic Regression beats an unconstrained Decision Tree on every held-out metric
  (ROC-AUC 0.719 vs. 0.531) -- see `bias_and_recommendation.md` for the full comparison and
  recommendation.
- **Risk pricing:** logistic-regression quartile risk tiers show a clean, monotonically
  increasing observed default rate (3% -> 52%).
- **Anomaly detection:** `IsolationForest` at the seeded 5.66% contamination rate recovers
  73.3% (11/15) of the injected transaction-behaviour anomalies.
- **Bias-awareness note:** identifies `employment_type`, `monthly_income_inr`, and
  `credit_bureau_score` as plausible correlated proxies and recommends a maker-checker
  human-in-the-loop review for declined thin-file applicants (`bias_and_recommendation.md`).

### Part 3 -- AI-Augmented Advisory & Blockchain Risk
- **Every recorded run in this repo uses the default `MOCK_LLM` path** (unset / `=1`) -- fully
  deterministic, keyless, no network call to any LLM provider. The optional `MOCK_LLM=0`
  extension (Groq free tier) was not attempted and is not required.
- **Advisory agent:** explicit think (prescribed allocation lookup) / act (`get_stock_data()`
  tool call) / observe-decide (CAPM + portfolio variance/std) loop across all 5 investor
  profiles, matching the brief's expected deterministic std-dev pattern exactly (~8.44% /
  ~12.57% / ~20.58%) and correctly escalating only the two Aggressive-tier investors.
- **Disclosure extraction:** rule-based `extract_signals()` correctly flags doc_02 as
  litigation risk, doc_05 as "confident", and doc_01/doc_04 as hedging.
- **Debate demo:** bull/bear/synthesizer arguments for PAYTECH, each citing its actual beta /
  expected return / std_dev.
- **DCF:** WACC 12.60% (CAPM cost of equity + illustrative after-tax cost of debt, 70/30
  weights), terminal growth 5% (7.60pp buffer), full 3x3 sensitivity grid with WACC exceeding
  terminal growth by >= 5.60pp in every cell, cross-checked against an EV/EBITDA multiple.
- **Blockchain/crypto risk appendix** (`blockchain_risk_note.md`, 869 words): stablecoin-type
  and DAO-governance risk assessment, a specific 2-3% max-allocation (Aggressive-tier-only)
  crypto recommendation grounded in CAPM/skew/survivorship-bias/transaction-cost reasoning, and
  a T.A.N.G.-framework analysis of Authority and Greed social-engineering vectors with a named
  bank-side real-time defense for each.

## Repository layout

```
.
├── README.md                        (this file)
├── requirements.txt                 (consolidated, all 3 parts)
├── payments_fraud_analytics/
│   ├── generate_data.py / merchants.csv / users.csv / ledger.csv / gateway_export.csv
│   ├── build_workbook.py -> merchant_workbook.xlsx
│   ├── build_db_and_queries.py -> paytm_payments.db, sql_query_output.txt
│   ├── reconcile.py -> reconciliation_report.txt
│   ├── dashboard.py -> dashboard_charts/*.png, dashboard_interpretations.md
│   └── README.md
├── credit_risk_lending_ml/
│   ├── generate_data.py / credit_applicants.csv / txn_behaviour.csv
│   ├── credit_risk_pipeline.py -> pipeline_report.md, charts/*.png
│   ├── bias_and_recommendation.md
│   └── README.md
└── ai_advisory_blockchain/
    ├── stock_universe.py / investor_profiles.py / disclosure_snippets.py
    ├── advisory_agent.py / extract_disclosure.py / debate.py / dcf_calculator.py
    ├── blockchain_risk_note.md
    └── README.md
```

