# Task D -- Bias-awareness note and final recommendation

## Bias-awareness note (proxy risk + governance)

Even though this dataset has no explicit gender, caste, religion, or location field, several
of the inputs used here can still act as **correlated proxies** for protected attributes once
this kind of model is deployed on real Paytm Postpaid applicants. `employment_type` is the
clearest risk: in the Indian labour market, "gig" and "self_employed" workers are
disproportionately drawn from lower-income and historically marginalized groups relative to
salaried, white-collar workers, and gig work itself correlates with age and, in some sectors,
gender (e.g., delivery/ride-hailing skews male; informal-sector self-employment skews toward
specific caste and regional groups). A model that learns "gig => higher risk" is not
necessarily reasoning about repayment behavior directly -- it may partly be re-encoding who
tends to hold gig jobs. `monthly_income_inr` is a second, more diffuse proxy: income is
strongly correlated with geography (urban vs. rural, city tier), and geography in India is
itself a correlated proxy for caste, religion, and language-community composition; a purely
income-driven cutoff can therefore reproduce regional/social disparities even with no
location field present. `credit_bureau_score` is the third: bureau history itself reflects
historic access to formal credit, which has not been distributed equally across social groups
in India, so a low or missing (thin-file) score can encode *past exclusion* rather than *future
default risk* -- this is exactly why the pipeline treats `is_thin_file` as its own feature
rather than silently penalizing missing-score applicants through imputation alone.

**Recommended governance step:** before this model goes live, route every "decline" decision
for thin-file (`is_thin_file == 1`) applicants through a **maker-checker human-in-the-loop
review** -- a human credit officer, distinct from the model, must independently review and
countersign any automatic decline for an applicant with no bureau history before it is
communicated to the customer, using the alternate-data signals (UPI inflow, bounced payments)
already computed in this pipeline as their review evidence. This targets the exact population
where the model has the least reliable signal and the highest proxy-bias risk, without slowing
down decisions for applicants who do have an established bureau score.

## Final model-comparison table

| Metric              | Logistic Regression | Decision Tree |
|----------------------|:-------------------:|:--------------:|
| Accuracy              | 0.760                | 0.670           |
| Precision             | 0.389                | 0.240           |
| Recall                | 0.350                | 0.300           |
| F1                     | 0.368                | 0.267           |
| ROC-AUC                | 0.719                | 0.531           |

IsolationForest anomaly-detection recall against the 15 seeded BTXNA* transaction anomalies:
**73.3%** (11 of 15 flagged), at a contamination rate of 5.66% (15/265) matching the injected
proportion.

## Recommendation

Deploy **Logistic Regression** for Paytm Postpaid's default-scoring step. It beats the Decision
Tree on every held-out metric that matters for a credit decision -- ROC-AUC of 0.719 vs. 0.531
(the tree is barely better than random ranking), accuracy of 0.760 vs. 0.670, and F1 of 0.368
vs. 0.267 -- which means logistic regression separates good and bad applicants far more
reliably at any threshold, and its output probabilities are exactly what feeds the risk-tier
pricing table (which showed a clean, monotonically increasing observed default rate from 3% in
Tier 1 to 52% in Tier 4). The unconstrained Decision Tree, by contrast, is almost certainly
overfitting this small 300-row training set (perfect/near-perfect training splits down single
branches), which is why its test-set AUC collapses toward 0.5; it would need pruning
(`max_depth`, `min_samples_leaf`) and re-validation before it could be trusted for pricing.
Logistic regression is also the more governance-friendly choice for a regulated lending
product -- its coefficients are directly inspectable for the proxy-bias review described above,
which a deep, unpruned tree is not.
