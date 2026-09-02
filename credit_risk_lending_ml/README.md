# Part 2 -- Credit Risk & Lending ML

Paytm vertical: Postpaid / Lending (BNPL-style consumer and merchant credit).

## Setup

```bash
cd credit_risk_lending_ml
pip install -r ../requirements.txt   # or the consolidated root requirements.txt
```

## Run, in order

```bash
python generate_data.py          # writes credit_applicants.csv, txn_behaviour.csv
python credit_risk_pipeline.py   # writes pipeline_report.md + charts/*.png
```

`bias_and_recommendation.md` (Task D) is a static write-up and does not need to be run.

`generate_data.py` reproduces 400 credit-applicant rows (measured default rate 20.25%, within
the 15-25% expected range; 80 rows / 20% with a missing `credit_bureau_score`) and a 265-row
`txn_behaviour.csv` with 15 seeded anomalies, from seed 42, exactly as specified.

## Design decisions

- **Thin-file handling (Task A):** `is_thin_file` is engineered directly from the raw
  not-missing/missing pattern *before* any split or imputation. No row is ever dropped. The
  75/25 train/test split (`random_state=42`, stratified on `default`) happens next; only then is
  the `credit_bureau_score` median computed **from the training split alone** and used to fill
  missing values in both splits -- mirroring the StandardScaler fit-on-train-only rule, to avoid
  leaking test-set information into training.
- **Encoding:** one-hot encoding for `employment_type` (nominal, 3 categories); test-set dummy
  columns are re-indexed to the training column set.
- **Models (Task B):** `LogisticRegression` and `DecisionTreeClassifier(random_state=42)` on the
  identical processed split. Full metric suite (confusion matrix, accuracy, precision, recall,
  F1, ROC-AUC) reported side by side -- see `pipeline_report.md`. Logistic Regression wins on
  every metric (AUC 0.719 vs. 0.531); see `bias_and_recommendation.md` for the full
  recommendation and reasoning.
- **Risk-based pricing table:** logistic-regression probabilities are scored across the full
  400-applicant population and bucketed into quartile risk tiers with illustrative interest-rate
  bands (9-11% -> 21-28%). Observed default rate rises monotonically from Tier 1 (3%) to Tier 4
  (52%), confirming the ranking is meaningful. (Task B's held-out evaluation metrics above are
  computed only on the test set -- this full-population scoring is a separate, illustrative
  pricing step, not a model-evaluation step.)
- **Anomaly detection (Task C):** `IsolationForest(random_state=42, contamination=15/265)` on
  standardized `txn_hour`, `is_new_device`, `txn_amount_inr`. Recall against the 15 seeded
  BTXNA* anomalies: **73.3%** (11/15 flagged).
- **Optional stretch:** a quick KMeans segmentation (k chosen via Calinski-Harabasz index) on
  standardized applicant features found one cluster (of `best_k`, see `pipeline_report.md`)
  over-indexing on the default label -- ungraded, included for extra insight only.
- **Bias-awareness note and final recommendation (Task D):** see `bias_and_recommendation.md`.

Full run output (exact console log) is saved in `pipeline_report.md`.
