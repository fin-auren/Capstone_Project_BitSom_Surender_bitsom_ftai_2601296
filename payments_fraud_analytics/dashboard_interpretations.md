# Dashboard interpretations (Part 1D)

## Layer 1 -- Headline Scorecards

Platform-wide GMV over the 30-day synthetic window is INR 290,382 across 468
captured transactions, with an overall success rate of 85.6% (captured vs.
failed+chargeback). Reconciliation match rate against the gateway export is 90.5%,
consistent with the ~88-90% of rows expected to survive all four injected discrepancy types
(missing/extra/amount-mismatched/status-mismatched) simultaneously. The chargeback ratio of
5.12% is inflated relative to a real production platform because the
seed-data generator deliberately injects 15 burner-account chargebacks on top of the organic
~2% baseline chargeback rate -- this is expected and is the fraud signal Part 1B's SQL queries
are built to catch.

## Layer 2 -- Trends (Daily GMV vs. Chargebacks)

Daily GMV fluctuates without a strong trend across the window, consistent with the generator
drawing transaction days uniformly at random. Chargeback counts cluster more heavily toward the
back half of the window (peaking around 2026-01-23) because burner-account frauds are seeded
only in days 10-29 of the window (`random.randint(10, 29)`), while organic chargebacks are spread
uniformly across all 30 days. This day-10-onward skew is a real, inspectable artifact of the
seed data rather than a plotting error, and mirrors how burner-account fraud often ramps up as
a campaign matures.

## Layer 3 -- Breakdown (Payment Method / Category)

UPI dominates GMV by payment method (UPI leads at INR 158,895),
directly reflecting the generator's 55% UPI weighting (`METHOD_WEIGHTS`) versus 20% Wallet, 15%
Card, and 10% Netbanking. By merchant category, travel contributes the most GMV
(INR 59,759), though category totals are noisier than method totals because
categories were assigned to only 40 merchants uniformly at random rather than weighted --
category leadership here reflects which categories happened to be assigned to higher-volume
merchants, not an intentional demand signal in the seed data.

## Layer 4 -- Details (Top 10 Merchants)

Among the top 10 merchants by transaction count, 7 merchant(s) exceed the 1%
per-merchant chargeback-ratio threshold and are flagged. Because chargebacks are rare overall
(~2% baseline plus a handful of burner-account frauds spread across 40 merchants), most
individual merchants land at or near 0% chargeback ratio; a flagged merchant here is a genuine
outlier worth an ops review, not noise from a low-volume merchant with one bad transaction --
all merchants in this table have double-digit transaction counts, so a flag reflects a real
elevated rate rather than a single-chargeback fluke.

