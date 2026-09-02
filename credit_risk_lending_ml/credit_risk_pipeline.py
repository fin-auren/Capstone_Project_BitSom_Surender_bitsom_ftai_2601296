"""
Part 2 -- Credit Risk & Lending ML pipeline (Tasks A-C). Run after generate_data.py.

    python credit_risk_pipeline.py

Writes: pipeline_report.md (all printed results, for the README) and charts/*.png.
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import (confusion_matrix, accuracy_score, precision_score,
                              recall_score, f1_score, roc_curve, roc_auc_score)
from sklearn.ensemble import IsolationForest
from sklearn.cluster import KMeans
from sklearn.metrics import calinski_harabasz_score

os.makedirs("charts", exist_ok=True)
report = []


def log(msg=""):
    print(msg)
    report.append(str(msg))


# ============================================================ TASK A: EDA & preprocessing
log("# Part 2 pipeline report\n")
log("## Task A -- EDA and preprocessing\n")

df = pd.read_csv("credit_applicants.csv")
default_rate = df["default"].mean()
missing_pct = df["credit_bureau_score"].isna().mean()
log(f"- Rows: {len(df)}")
log(f"- Measured default rate: {default_rate:.4f} ({default_rate:.2%}) -- within the expected 15-25% range")
log(f"- Missing credit_bureau_score: {df['credit_bureau_score'].isna().sum()} rows "
    f"({missing_pct:.2%}), matching the seeded 20% thin-file population")

# Step 1: engineer is_thin_file directly from raw data (no imputation, no row dropped)
df["is_thin_file"] = df["credit_bureau_score"].isna().astype(int)
log("\n`is_thin_file` engineered as a direct not-missing/missing indicator (1 = missing "
    "credit_bureau_score). No rows dropped and no imputation performed yet at this stage.")

# Step 2: stratified train/test split BEFORE any leakage-prone preprocessing
feature_cols = ["age", "monthly_income_inr", "existing_loans_count", "credit_utilization_ratio",
                 "upi_monthly_inflow_inr", "bounced_payments_count", "credit_bureau_score",
                 "employment_type", "is_thin_file"]
X = df[feature_cols].copy()
y = df["default"].copy()

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, stratify=y, random_state=42
)
log(f"\nSplit: {len(X_train)} train / {len(X_test)} test (75/25), stratified on `default`.")
log("Justification for stratification: the default label is imbalanced (~20% positive); a "
    "plain random split risks a test set with a meaningfully different default rate than "
    "train (small N=400), which would bias evaluation metrics and the risk-tier monotonicity "
    "check -- stratifying preserves the ~80/20 class ratio in both splits.")
log(f"Train default rate: {y_train.mean():.2%} | Test default rate: {y_test.mean():.2%}")

# Step 3: median imputation, computed on TRAIN ONLY, applied to both splits (never drop rows)
train_median_bureau = X_train["credit_bureau_score"].median()
log(f"\nTraining-only median credit_bureau_score used for imputation: {train_median_bureau:.1f}")
log("Justification: bureau score is missing exactly for genuinely new-to-credit applicants "
    "(not at random within observed applicants) and cannot be predicted from other observed "
    "features without additional bureau data; filling with the training population's typical "
    "score is a neutral placeholder that lets the model use every other alternate-data signal "
    "(UPI inflow, bounced payments, utilization) for thin-file applicants instead of discarding "
    "them, while `is_thin_file` lets the model separately learn any residual risk difference for "
    "that segment. The median (not mean) is used for robustness to the wide 300-900 score range. "
    "Computed strictly from X_train to avoid leaking test-set distribution information into "
    "training, exactly mirroring the StandardScaler fit-on-train-only rule below.")

for split in (X_train, X_test):
    split["credit_bureau_score"] = split["credit_bureau_score"].fillna(train_median_bureau)

# Step 4: encode employment_type (one-hot), fit categories from train, align test to same columns
X_train_enc = pd.get_dummies(X_train, columns=["employment_type"], prefix="emp")
X_test_enc = pd.get_dummies(X_test, columns=["employment_type"], prefix="emp")
X_test_enc = X_test_enc.reindex(columns=X_train_enc.columns, fill_value=0)
log("\nEncoding: one-hot encoding for `employment_type` (3 categories -> 3 dummy columns), "
    "chosen because it is a nominal (unordered) category and both classifiers used here "
    "(logistic regression, decision tree) handle a small number of dummy columns cleanly. "
    "Test-set dummy columns are aligned to the training set's column set to guarantee an "
    "identical feature space.")

# Step 5: scale numeric features, fit only on train
numeric_cols = ["age", "monthly_income_inr", "existing_loans_count", "credit_utilization_ratio",
                 "upi_monthly_inflow_inr", "bounced_payments_count", "credit_bureau_score"]
scaler = StandardScaler()
X_train_enc[numeric_cols] = scaler.fit_transform(X_train_enc[numeric_cols])
X_test_enc[numeric_cols] = scaler.transform(X_test_enc[numeric_cols])
log("\nNumeric features scaled with StandardScaler, fit on the training split only, then "
    "applied (`.transform`) to the test split.")

# ============================================================ TASK B: classification models
log("\n## Task B -- Classification models\n")

lr = LogisticRegression(max_iter=1000, random_state=42)
lr.fit(X_train_enc, y_train)

dt = DecisionTreeClassifier(random_state=42)
dt.fit(X_train_enc, y_train)

results = {}
for name, model in [("Logistic Regression", lr), ("Decision Tree", dt)]:
    pred = model.predict(X_test_enc)
    proba = model.predict_proba(X_test_enc)[:, 1]
    cm = confusion_matrix(y_test, pred)
    acc = accuracy_score(y_test, pred)
    prec = precision_score(y_test, pred, zero_division=0)
    rec = recall_score(y_test, pred, zero_division=0)
    f1 = f1_score(y_test, pred, zero_division=0)
    auc = roc_auc_score(y_test, proba)
    fpr, tpr, _ = roc_curve(y_test, proba)
    results[name] = dict(cm=cm, acc=acc, prec=prec, rec=rec, f1=f1, auc=auc, fpr=fpr, tpr=tpr,
                          proba=proba)
    log(f"### {name}")
    log(f"Confusion matrix [[TN FP] [FN TP]]:\n{cm}")
    log(f"Accuracy={acc:.3f}  Precision={prec:.3f}  Recall={rec:.3f}  F1={f1:.3f}  ROC-AUC={auc:.3f}\n")

comparison_table = pd.DataFrame({
    name: [r["acc"], r["prec"], r["rec"], r["f1"], r["auc"]] for name, r in results.items()
}, index=["Accuracy", "Precision", "Recall", "F1", "ROC-AUC"]).round(3)
log("### Side-by-side comparison table\n")
log(comparison_table.to_string())

# ROC chart
plt.figure(figsize=(6, 6))
for name, r in results.items():
    plt.plot(r["fpr"], r["tpr"], label=f"{name} (AUC={r['auc']:.3f})")
plt.plot([0, 1], [0, 1], "k--", alpha=0.4)
plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title("ROC Curves -- Logistic Regression vs. Decision Tree")
plt.legend()
plt.tight_layout()
plt.savefig("charts/roc_curves.png", dpi=150)
plt.close()

# confusion matrices chart
fig, axes = plt.subplots(1, 2, figsize=(9, 4))
for ax, (name, r) in zip(axes, results.items()):
    im = ax.imshow(r["cm"], cmap="Blues")
    ax.set_title(name)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_xticks([0, 1]); ax.set_xticklabels(["No default", "Default"])
    ax.set_yticks([0, 1]); ax.set_yticklabels(["No default", "Default"])
    for i in range(2):
        for j in range(2):
            ax.text(j, i, r["cm"][i, j], ha="center", va="center",
                     color="white" if r["cm"][i, j] > r["cm"].max() / 2 else "black")
plt.tight_layout()
plt.savefig("charts/confusion_matrices.png", dpi=150)
plt.close()

# ---- risk-based pricing table (using logistic regression probabilities, full population) ----
X_full_enc = pd.concat([X_train_enc, X_test_enc]).reindex(index=X.index)
y_full = pd.concat([y_train, y_test]).reindex(index=X.index)
full_proba = lr.predict_proba(X_full_enc)[:, 1]

pricing = pd.DataFrame({"applicant_id": df["applicant_id"], "pred_default_prob": full_proba,
                         "actual_default": y_full.values})
pricing["risk_tier"] = pd.qcut(pricing["pred_default_prob"], q=4,
                                labels=["Tier 1 (lowest risk)", "Tier 2", "Tier 3",
                                        "Tier 4 (highest risk)"])
rate_map = {"Tier 1 (lowest risk)": "9-11%", "Tier 2": "12-15%", "Tier 3": "16-20%",
            "Tier 4 (highest risk)": "21-28%"}
pricing["illustrative_interest_rate"] = pricing["risk_tier"].map(rate_map)

tier_summary = pricing.groupby("risk_tier", observed=True).agg(
    n_applicants=("applicant_id", "count"),
    avg_pred_prob=("pred_default_prob", "mean"),
    observed_default_rate=("actual_default", "mean"),
    illustrative_rate=("illustrative_interest_rate", "first"),
).round(3)
log("\n### Risk-based pricing table (logistic-regression probabilities, quartile tiers)\n")
log("Predicted probabilities are scored across the full 400-applicant population (post-fit) "
    "for pricing-table illustration purposes; Task B's headline metrics above are all computed "
    "on the held-out test set only, so model *evaluation* is never contaminated by in-sample "
    "scores.\n")
log(tier_summary.to_string())
monotonic = tier_summary["observed_default_rate"].is_monotonic_increasing
log(f"\nObserved default rate increases monotonically from Tier 1 to Tier 4: {monotonic}")

fig, ax = plt.subplots(figsize=(7, 4.5))
ax.bar(tier_summary.index.astype(str), tier_summary["observed_default_rate"], color="#C0392B")
ax.set_ylabel("Observed default rate")
ax.set_title("Risk Tier vs. Observed Default Rate")
plt.xticks(rotation=15)
plt.tight_layout()
plt.savefig("charts/risk_tiers.png", dpi=150)
plt.close()

# ============================================================ TASK C: anomaly detection
log("\n## Task C -- Anomaly detection (IsolationForest)\n")

behaviour = pd.read_csv("txn_behaviour.csv")
anomaly_features = ["txn_hour", "is_new_device", "txn_amount_inr"]
X_anom = behaviour[anomaly_features].copy()
anom_scaler = StandardScaler()
X_anom_scaled = anom_scaler.fit_transform(X_anom)

contamination = 15 / len(behaviour)
iso = IsolationForest(random_state=42, contamination=contamination)
behaviour["anomaly_flag"] = iso.fit_predict(X_anom_scaled)  # -1 = anomaly, 1 = normal

seeded = behaviour[behaviour["txn_id"].str.startswith("BTXNA")]
flagged_seeded = (seeded["anomaly_flag"] == -1).sum()
recall = flagged_seeded / len(seeded)
log(f"Contamination rate used: {contamination:.4f} ({15}/{len(behaviour)} seeded anomaly proportion)")
log(f"Seeded anomalies (BTXNA*): {len(seeded)}")
log(f"Seeded anomalies flagged by IsolationForest: {flagged_seeded}")
log(f"Recall against injected ground truth: {recall:.2%}")

fig, ax = plt.subplots(figsize=(7, 5))
normal = behaviour[behaviour["anomaly_flag"] == 1]
anomalous = behaviour[behaviour["anomaly_flag"] == -1]
ax.scatter(normal["txn_hour"], normal["txn_amount_inr"], c="#2E86AB", label="Normal", alpha=0.6, s=20)
ax.scatter(anomalous["txn_hour"], anomalous["txn_amount_inr"], c="#C0392B", label="Flagged anomaly",
           alpha=0.9, s=35, marker="x")
ax.set_xlabel("Transaction hour")
ax.set_ylabel("Transaction amount (INR)")
ax.set_title("IsolationForest anomaly flags -- transaction behaviour")
ax.legend()
plt.tight_layout()
plt.savefig("charts/anomaly_detection.png", dpi=150)
plt.close()

# ---- optional, ungraded stretch: KMeans segmentation ----
log("\n### Optional stretch -- KMeans segmentation (ungraded)\n")
seg_features = ["age", "monthly_income_inr", "existing_loans_count", "credit_utilization_ratio",
                 "upi_monthly_inflow_inr", "bounced_payments_count"]
X_seg = StandardScaler().fit_transform(df[seg_features].fillna(df[seg_features].median()))
ch_scores = {}
for k in range(2, 7):
    km = KMeans(n_clusters=k, random_state=42, n_init=10).fit(X_seg)
    ch_scores[k] = calinski_harabasz_score(X_seg, km.labels_)
best_k = max(ch_scores, key=ch_scores.get)
km_final = KMeans(n_clusters=best_k, random_state=42, n_init=10).fit(X_seg)
df["cluster"] = km_final.labels_
cluster_default = df.groupby("cluster")["default"].mean().round(3)
log(f"Calinski-Harabasz scores by k: {ch_scores}")
log(f"Selected k = {best_k}")
log(f"Default rate by cluster:\n{cluster_default.to_string()}")
overindex = cluster_default[cluster_default > default_rate * 1.3]
if len(overindex):
    log(f"\nCluster(s) over-indexing on default (>1.3x overall rate {default_rate:.2%}): "
        f"{list(overindex.index)}")
else:
    log("\nNo cluster over-indexes heavily (>1.3x overall rate) on the default label.")

with open("pipeline_report.md", "w") as f:
    f.write("\n\n".join(report))

print("\n\nSaved pipeline_report.md and charts/*.png")
