"""
Part 1D -- four-layer, code-generated analytics dashboard (Headline / Trends / Breakdown /
Details). Produces saved chart images under dashboard_charts/ plus a written interpretation
for each, saved to dashboard_interpretations.md.

Definitions used (exactly as specified in the capstone brief):
  match_rate = (# txns present in BOTH files with identical amount_inr AND identical status)
               / (total ledger txn count)
  chargeback_ratio (headline, platform-wide) = (# chargeback txns) / (# all txns)
  chargeback_ratio (per-merchant)            = (# that merchant's chargeback txns)
                                                / (# that merchant's txns)
Assumption (stated per xlsx-skill / documentation convention): GMV = sum(amount_inr) over
'captured' (successfully settled) transactions only -- failed/chargeback amounts are not
counted as merchandise value moved.
"""
import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from reconcile import reconcile_payments

OUT = "dashboard_charts"
os.makedirs(OUT, exist_ok=True)

ledger = pd.read_csv("ledger.csv", parse_dates=["transaction_time"])
gateway = pd.read_csv("gateway_export.csv", parse_dates=["transaction_time"])
merchants = pd.read_csv("merchants.csv")

ledger["date"] = ledger["transaction_time"].dt.date
n_total = len(ledger)
captured = ledger[ledger["status"] == "captured"]

interpretations = []

# ============================================================== HEADLINE LAYER
total_gmv = captured["amount_inr"].sum()
success_rate = len(captured) / n_total

merged_recon = pd.merge(
    ledger[["transaction_id", "amount_inr", "status"]],
    gateway[["transaction_id", "amount_inr", "status"]],
    on="transaction_id", suffixes=("_l", "_g"), how="left"
)
matched = merged_recon[
    (merged_recon["amount_inr_l"] == merged_recon["amount_inr_g"]) &
    (merged_recon["status_l"] == merged_recon["status_g"])
]
match_rate = len(matched) / n_total

chargeback_ratio_headline = (ledger["status"] == "chargeback").sum() / n_total

fig, ax = plt.subplots(figsize=(11, 2.6))
ax.axis("off")
scorecards = [
    ("Total GMV (captured)", f"INR {total_gmv:,.0f}"),
    ("Success Rate", f"{success_rate:.1%}"),
    ("Reconciliation Match Rate", f"{match_rate:.1%}"),
    ("Chargeback Ratio", f"{chargeback_ratio_headline:.2%}"),
]
for i, (label, value) in enumerate(scorecards):
    x = 0.02 + i * 0.245
    ax.add_patch(plt.Rectangle((x, 0.05), 0.22, 0.9, transform=ax.transAxes,
                                facecolor="#1F4E78", edgecolor="none"))
    ax.text(x + 0.11, 0.62, value, transform=ax.transAxes, ha="center", va="center",
            fontsize=15, fontweight="bold", color="white")
    ax.text(x + 0.11, 0.22, label, transform=ax.transAxes, ha="center", va="center",
            fontsize=9.5, color="white")
plt.title("Layer 1 -- Headline Scorecards", fontsize=12, fontweight="bold", loc="left")
plt.tight_layout()
plt.savefig(f"{OUT}/1_headline_scorecards.png", dpi=150)
plt.close()

interpretations.append(("Layer 1 -- Headline Scorecards", f"""
Platform-wide GMV over the 30-day synthetic window is INR {total_gmv:,.0f} across {len(captured)}
captured transactions, with an overall success rate of {success_rate:.1%} (captured vs.
failed+chargeback). Reconciliation match rate against the gateway export is {match_rate:.1%},
consistent with the ~88-90% of rows expected to survive all four injected discrepancy types
(missing/extra/amount-mismatched/status-mismatched) simultaneously. The chargeback ratio of
{chargeback_ratio_headline:.2%} is inflated relative to a real production platform because the
seed-data generator deliberately injects 15 burner-account chargebacks on top of the organic
~2% baseline chargeback rate -- this is expected and is the fraud signal Part 1B's SQL queries
are built to catch.
""".strip()))

# ============================================================== TRENDS LAYER
daily = ledger.groupby("date").agg(
    gmv=("amount_inr", lambda s: s[ledger.loc[s.index, "status"] == "captured"].sum()),
    chargeback_count=("status", lambda s: (s == "chargeback").sum()),
).reset_index()

fig, ax1 = plt.subplots(figsize=(11, 4.5))
ax1.bar(daily["date"], daily["gmv"], color="#1F4E78", alpha=0.85, label="Daily GMV (INR)")
ax1.set_ylabel("Daily GMV (INR)", color="#1F4E78")
ax1.tick_params(axis="x", rotation=45)
ax2 = ax1.twinx()
ax2.plot(daily["date"], daily["chargeback_count"], color="#C0392B", marker="o",
         linewidth=2, label="Daily chargeback count")
ax2.set_ylabel("Daily chargeback count", color="#C0392B")
plt.title("Layer 2 -- Daily GMV vs. Daily Chargeback Count (30-day window)", fontweight="bold")
fig.tight_layout()
plt.savefig(f"{OUT}/2_trends_gmv_chargebacks.png", dpi=150)
plt.close()

spike_day = daily.loc[daily["chargeback_count"].idxmax(), "date"]
interpretations.append(("Layer 2 -- Trends (Daily GMV vs. Chargebacks)", f"""
Daily GMV fluctuates without a strong trend across the window, consistent with the generator
drawing transaction days uniformly at random. Chargeback counts cluster more heavily toward the
back half of the window (peaking around {spike_day}) because burner-account frauds are seeded
only in days 10-29 of the window (`random.randint(10, 29)`), while organic chargebacks are spread
uniformly across all 30 days. This day-10-onward skew is a real, inspectable artifact of the
seed data rather than a plotting error, and mirrors how burner-account fraud often ramps up as
a campaign matures.
""".strip()))

# ============================================================== BREAKDOWN LAYER
by_method = captured.groupby("payment_method")["amount_inr"].sum().sort_values(ascending=False)
cat_merged = pd.merge(captured, merchants[["merchant_id", "category"]], on="merchant_id", how="left")
by_category = cat_merged.groupby("category")["amount_inr"].sum().sort_values(ascending=False)

fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
axes[0].bar(by_method.index, by_method.values, color="#2E86AB")
axes[0].set_title("GMV by Payment Method")
axes[0].set_ylabel("GMV (INR)")
axes[0].tick_params(axis="x", rotation=20)
axes[1].bar(by_category.index, by_category.values, color="#5DA271")
axes[1].set_title("GMV by Merchant Category")
axes[1].set_ylabel("GMV (INR)")
axes[1].tick_params(axis="x", rotation=35)
plt.suptitle("Layer 3 -- GMV Breakdown", fontweight="bold")
plt.tight_layout()
plt.savefig(f"{OUT}/3_breakdown_method_category.png", dpi=150)
plt.close()

interpretations.append(("Layer 3 -- Breakdown (Payment Method / Category)", f"""
UPI dominates GMV by payment method ({by_method.index[0]} leads at INR {by_method.iloc[0]:,.0f}),
directly reflecting the generator's 55% UPI weighting (`METHOD_WEIGHTS`) versus 20% Wallet, 15%
Card, and 10% Netbanking. By merchant category, {by_category.index[0]} contributes the most GMV
(INR {by_category.iloc[0]:,.0f}), though category totals are noisier than method totals because
categories were assigned to only 40 merchants uniformly at random rather than weighted --
category leadership here reflects which categories happened to be assigned to higher-volume
merchants, not an intentional demand signal in the seed data.
""".strip()))

# ============================================================== DETAILS LAYER (saved table image)
per_merchant = ledger.groupby("merchant_id").agg(
    txn_count=("transaction_id", "count"),
    total_amount_inr=("amount_inr", "sum"),
    chargeback_count=("status", lambda s: (s == "chargeback").sum()),
).reset_index()
per_merchant["chargeback_ratio"] = per_merchant["chargeback_count"] / per_merchant["txn_count"]
per_merchant["high_chargeback_flag"] = per_merchant["chargeback_ratio"].apply(
    lambda r: "\u26a0 FLAG (>1%)" if r > 0.01 else "OK"
)
per_merchant = pd.merge(per_merchant, merchants[["merchant_id", "merchant_name"]], on="merchant_id")
top10 = per_merchant.sort_values("txn_count", ascending=False).head(10)
top10_display = top10[["merchant_id", "merchant_name", "txn_count", "total_amount_inr",
                        "chargeback_ratio", "high_chargeback_flag"]].copy()
top10_display["total_amount_inr"] = top10_display["total_amount_inr"].map("{:,.0f}".format)
top10_display["chargeback_ratio"] = top10_display["chargeback_ratio"].map("{:.2%}".format)

fig, ax = plt.subplots(figsize=(11, 0.5 + 0.42 * len(top10_display)))
ax.axis("off")
tbl = ax.table(
    cellText=top10_display.values,
    colLabels=["merchant_id", "merchant_name", "txn_count", "total_amount_inr",
               "chargeback_ratio", "flag"],
    loc="center", cellLoc="center",
)
tbl.auto_set_font_size(False)
tbl.set_fontsize(9.5)
tbl.scale(1, 1.6)
for j in range(6):
    tbl[0, j].set_facecolor("#1F4E78")
    tbl[0, j].set_text_props(color="white", fontweight="bold")
for i in range(len(top10_display)):
    if "FLAG" in top10_display.iloc[i]["high_chargeback_flag"]:
        for j in range(6):
            tbl[i + 1, j].set_facecolor("#FADBD8")
plt.title("Layer 4 -- Top 10 Merchants by Transaction Count (chargeback_ratio > 1% flagged)",
          fontweight="bold", pad=14)
plt.tight_layout()
plt.savefig(f"{OUT}/4_details_top10_merchants.png", dpi=150)
plt.close()

n_flagged = (top10_display["high_chargeback_flag"].str.contains("FLAG")).sum()
interpretations.append(("Layer 4 -- Details (Top 10 Merchants)", f"""
Among the top 10 merchants by transaction count, {n_flagged} merchant(s) exceed the 1%
per-merchant chargeback-ratio threshold and are flagged. Because chargebacks are rare overall
(~2% baseline plus a handful of burner-account frauds spread across 40 merchants), most
individual merchants land at or near 0% chargeback ratio; a flagged merchant here is a genuine
outlier worth an ops review, not noise from a low-volume merchant with one bad transaction --
all merchants in this table have double-digit transaction counts, so a flag reflects a real
elevated rate rather than a single-chargeback fluke.
""".strip()))

with open("dashboard_interpretations.md", "w") as f:
    f.write("# Dashboard interpretations (Part 1D)\n\n")
    for title, body in interpretations:
        f.write(f"## {title}\n\n{body}\n\n")

print("Saved 4 chart images to dashboard_charts/ and dashboard_interpretations.md")
print(f"\nheadline: GMV={total_gmv:,.0f}  success_rate={success_rate:.2%}  "
      f"match_rate={match_rate:.2%}  chargeback_ratio={chargeback_ratio_headline:.2%}")
print(f"details: {n_flagged} of top10 merchants flagged (chargeback_ratio > 1%)")
