# Part 1 -- Payments & Fraud Analytics

Paytm vertical: Payments (UPI / Wallet / QR merchant payments).

## Setup

```bash
cd payments_fraud_analytics
pip install -r ../requirements.txt   # or the consolidated root requirements.txt
```

## Run, in order

```bash
python generate_data.py            # writes merchants.csv, users.csv, ledger.csv, gateway_export.csv
python build_workbook.py           # writes merchant_workbook.xlsx (formulas, not cached values)
python /mnt/skills/public/xlsx/scripts/recalc.py merchant_workbook.xlsx   # or open in Excel/Sheets/LibreOffice to recalc
python build_db_and_queries.py     # writes paytm_payments.db + sql_query_output.txt
python reconcile.py                # writes reconciliation_report.txt
python dashboard.py                # writes dashboard_charts/*.png + dashboard_interpretations.md
```

`generate_data.py` reproduces the exact 547-row ledger (500 baseline + 15 seeded
burner-account chargebacks + 32 seeded velocity-attack rows) and the discrepant
gateway export, from seed 42, as specified in the brief.

## Design decisions

- **VLOOKUP / IFERROR (Part A):** `transactions_view` looks up merchant_name/category/region
  from a fixed absolute range `merchants!$A$2:$D$41`. A synthetic demo row
  (`merchant_id = 999`, which does not exist) is appended at row 549 specifically to exercise
  the `IFERROR` -> "Merchant not found" path, since every real ledger row has a valid
  merchant_id (1-40) by construction.
- **HLOOKUP (Part A):** `fee_tiers` sheet has a horizontal payment-method -> MDR-fee-% table.
  Fee percentages (UPI 0.30%, Wallet 0.50%, Card 1.20%, Netbanking 0.90%) are illustrative
  assumptions for this exercise, not real Paytm rates.
- **Classification rule (Part A):** "High-Value Merchant Day" = `AND(merchant_day_total_inr >
  5000, region <> "East")`, exactly per the brief's stated cutoff. `merchant_day_total_inr` is
  a `SUMIFS` of that merchant's same-calendar-day transaction amounts.
- **Pivot table (Part A):** built as a live `SUMIFS`/`COUNTIFS` cross-tab
  (`pivot_summary` sheet) rather than a native Excel PivotTable object, because openpyxl
  (the reproducible toolchain used here) cannot reliably author a PivotTable's cache/definition
  XML. It is functionally equivalent -- it recalculates automatically -- and can also be
  reproduced as a native pivot via Insert > PivotTable on `transactions_view!A1:N548` if
  preferred. The count-vs-unique-days comparison uses the standard
  `SUMPRODUCT(.../COUNTIFS(...))` distinct-count formula for merchants 1-5.
- **SQL (Part B):** normalized 3-table schema with declared PK/FK. Burner-account boundary is
  `0 <= (transaction_time - signup_date) days < 30` via `julianday()` differences (surfaces all
  15 seeded rows). Velocity attacks are grouped by `user_id` + a floored 10-minute time bucket
  (surfaces all 8 seeded 4-transaction clusters).
- **Reconciliation (Part C):** `reconcile_payments()` uses set operations on `transaction_id`
  for missing-in-gateway / missing-in-ledger, and an inner merge on `transaction_id` restricted
  to common IDs for amount/status mismatches. Measured discrepancy rates (4.94% / 1.83% / 2.93%
  / 1.65%) land close to the injected 5%/2%/3%/2% rates (small deviations are expected because
  the missing/mismatch/extra/status-flip index draws in `generate_data.py` can overlap).
- **Dashboard (Part D):** GMV is defined as the sum of `amount_inr` over `status == "captured"`
  transactions only (failed/chargeback amounts are not counted as merchandise value moved).
  `match_rate` and `chargeback_ratio` use the exact definitions specified in the brief. The
  Details layer is a saved table image (matplotlib `table`), not a live DataFrame, with
  chargeback-ratio-flagged rows highlighted in red.

See `dashboard_interpretations.md` for the full 2-4 sentence write-up per chart layer, and
`sql_query_output.txt` / `reconciliation_report.txt` for full query/reconciliation output.
