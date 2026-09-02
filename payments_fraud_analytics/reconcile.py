"""
Part 1C -- payment reconciliation engine.

reconcile_payments(ledger_df, gateway_df) compares Paytm's internal ledger against the
payment gateway's export and returns four DataFrames:
  1. missing_in_gateway   -- transaction_ids present in the ledger but absent from the gateway
  2. missing_in_ledger    -- transaction_ids present in the gateway but absent from the ledger
  3. amount_mismatches    -- transaction_ids present in both, with a differing amount_inr
  4. status_mismatches    -- transaction_ids present in both, with a differing status

Run standalone: `python reconcile.py` (expects ledger.csv / gateway_export.csv in this folder).
"""
import pandas as pd


def reconcile_payments(ledger_df: pd.DataFrame, gateway_df: pd.DataFrame):
    ledger_ids = set(ledger_df["transaction_id"])
    gateway_ids = set(gateway_df["transaction_id"])

    # 1 & 2: set operations on transaction_id
    missing_in_gateway_ids = ledger_ids - gateway_ids
    missing_in_ledger_ids = gateway_ids - ledger_ids

    missing_in_gateway = ledger_df[ledger_df["transaction_id"].isin(missing_in_gateway_ids)].copy()
    missing_in_ledger = gateway_df[gateway_df["transaction_id"].isin(missing_in_ledger_ids)].copy()

    # 3 & 4: pairwise comparison via merge, restricted to transaction_ids present in both files
    common_ids = ledger_ids & gateway_ids
    l_common = ledger_df[ledger_df["transaction_id"].isin(common_ids)]
    g_common = gateway_df[gateway_df["transaction_id"].isin(common_ids)]

    merged = pd.merge(
        l_common, g_common, on="transaction_id", suffixes=("_ledger", "_gateway")
    )

    amount_mismatches = merged[merged["amount_inr_ledger"] != merged["amount_inr_gateway"]].copy()
    amount_mismatches["amount_diff_inr"] = (
        amount_mismatches["amount_inr_gateway"] - amount_mismatches["amount_inr_ledger"]
    )
    amount_mismatches = amount_mismatches[
        ["transaction_id", "amount_inr_ledger", "amount_inr_gateway", "amount_diff_inr"]
    ]

    status_mismatches = merged[merged["status_ledger"] != merged["status_gateway"]].copy()
    status_mismatches = status_mismatches[["transaction_id", "status_ledger", "status_gateway"]]

    return missing_in_gateway, missing_in_ledger, amount_mismatches, status_mismatches


if __name__ == "__main__":
    ledger = pd.read_csv("ledger.csv")
    gateway = pd.read_csv("gateway_export.csv")

    missing_in_gateway, missing_in_ledger, amount_mismatches, status_mismatches = reconcile_payments(
        ledger, gateway
    )

    n = len(ledger)
    report = []
    report.append("=== Payment Reconciliation Report: ledger.csv vs gateway_export.csv ===")
    report.append(f"Ledger transaction count: {n}")
    report.append(f"Gateway export transaction count: {len(gateway)}")
    report.append("")
    report.append(
        f"1) Missing in gateway (present in ledger only): {len(missing_in_gateway)} "
        f"({len(missing_in_gateway) / n:.2%} of ledger) -- expected ~5%"
    )
    report.append(
        f"2) Missing in ledger (extra rows in gateway only): {len(missing_in_ledger)} "
        f"({len(missing_in_ledger) / n:.2%} of ledger) -- expected ~2%"
    )
    report.append(
        f"3) Amount mismatches (same transaction_id, different amount_inr): {len(amount_mismatches)} "
        f"({len(amount_mismatches) / n:.2%} of ledger) -- expected ~3%"
    )
    report.append(
        f"4) Status mismatches (same transaction_id, different status): {len(status_mismatches)} "
        f"({len(status_mismatches) / n:.2%} of ledger) -- expected ~2%"
    )
    report.append("")
    report.append("--- Sample: missing_in_gateway (first 5) ---")
    report.append(missing_in_gateway.head().to_string(index=False))
    report.append("")
    report.append("--- Sample: missing_in_ledger (first 5) ---")
    report.append(missing_in_ledger.head().to_string(index=False))
    report.append("")
    report.append("--- Sample: amount_mismatches (first 5) ---")
    report.append(amount_mismatches.head().to_string(index=False))
    report.append("")
    report.append("--- Sample: status_mismatches (first 5) ---")
    report.append(status_mismatches.head().to_string(index=False))

    text = "\n".join(report)
    print(text)
    with open("reconciliation_report.txt", "w") as f:
        f.write(text)
    print("\nSaved reconciliation_report.txt")
