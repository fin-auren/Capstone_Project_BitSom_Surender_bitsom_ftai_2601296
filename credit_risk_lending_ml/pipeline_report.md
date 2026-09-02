# Part 2 pipeline report


## Task A -- EDA and preprocessing


- Rows: 400

- Measured default rate: 0.2025 (20.25%) -- within the expected 15-25% range

- Missing credit_bureau_score: 80 rows (20.00%), matching the seeded 20% thin-file population


`is_thin_file` engineered as a direct not-missing/missing indicator (1 = missing credit_bureau_score). No rows dropped and no imputation performed yet at this stage.


Split: 300 train / 100 test (75/25), stratified on `default`.

Justification for stratification: the default label is imbalanced (~20% positive); a plain random split risks a test set with a meaningfully different default rate than train (small N=400), which would bias evaluation metrics and the risk-tier monotonicity check -- stratifying preserves the ~80/20 class ratio in both splits.

Train default rate: 20.33% | Test default rate: 20.00%


Training-only median credit_bureau_score used for imputation: 612.0

Justification: bureau score is missing exactly for genuinely new-to-credit applicants (not at random within observed applicants) and cannot be predicted from other observed features without additional bureau data; filling with the training population's typical score is a neutral placeholder that lets the model use every other alternate-data signal (UPI inflow, bounced payments, utilization) for thin-file applicants instead of discarding them, while `is_thin_file` lets the model separately learn any residual risk difference for that segment. The median (not mean) is used for robustness to the wide 300-900 score range. Computed strictly from X_train to avoid leaking test-set distribution information into training, exactly mirroring the StandardScaler fit-on-train-only rule below.


Encoding: one-hot encoding for `employment_type` (3 categories -> 3 dummy columns), chosen because it is a nominal (unordered) category and both classifiers used here (logistic regression, decision tree) handle a small number of dummy columns cleanly. Test-set dummy columns are aligned to the training set's column set to guarantee an identical feature space.


Numeric features scaled with StandardScaler, fit on the training split only, then applied (`.transform`) to the test split.


## Task B -- Classification models


### Logistic Regression

Confusion matrix [[TN FP] [FN TP]]:
[[69 11]
 [13  7]]

Accuracy=0.760  Precision=0.389  Recall=0.350  F1=0.368  ROC-AUC=0.719


### Decision Tree

Confusion matrix [[TN FP] [FN TP]]:
[[61 19]
 [14  6]]

Accuracy=0.670  Precision=0.240  Recall=0.300  F1=0.267  ROC-AUC=0.531


### Side-by-side comparison table


           Logistic Regression  Decision Tree
Accuracy                 0.760          0.670
Precision                0.389          0.240
Recall                   0.350          0.300
F1                       0.368          0.267
ROC-AUC                  0.719          0.531


### Risk-based pricing table (logistic-regression probabilities, quartile tiers)


Predicted probabilities are scored across the full 400-applicant population (post-fit) for pricing-table illustration purposes; Task B's headline metrics above are all computed on the held-out test set only, so model *evaluation* is never contaminated by in-sample scores.


                       n_applicants  avg_pred_prob  observed_default_rate illustrative_rate
risk_tier                                                                                  
Tier 1 (lowest risk)            100          0.020                   0.03             9-11%
Tier 2                          100          0.072                   0.08            12-15%
Tier 3                          100          0.197                   0.18            16-20%
Tier 4 (highest risk)           100          0.550                   0.52            21-28%


Observed default rate increases monotonically from Tier 1 to Tier 4: True


## Task C -- Anomaly detection (IsolationForest)


Contamination rate used: 0.0566 (15/265 seeded anomaly proportion)

Seeded anomalies (BTXNA*): 15

Seeded anomalies flagged by IsolationForest: 11

Recall against injected ground truth: 73.33%


### Optional stretch -- KMeans segmentation (ungraded)


Calinski-Harabasz scores by k: {2: 63.914985653118016, 3: 57.672957261837006, 4: 56.071175802181756, 5: 53.90961854964549, 6: 50.70717039368732}

Selected k = 2

Default rate by cluster:
cluster
0    0.321
1    0.099


Cluster(s) over-indexing on default (>1.3x overall rate 20.25%): [0]