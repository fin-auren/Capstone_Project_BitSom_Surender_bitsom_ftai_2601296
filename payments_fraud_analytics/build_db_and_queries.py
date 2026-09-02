"""
Part 1B -- builds paytm_payments.db (normalized SQLite schema) from the committed CSVs,
then runs >= 6 SQL queries covering SELECT/WHERE/ORDER BY/LIMIT/DISTINCT, GROUP BY/HAVING,
INNER JOIN, LEFT JOIN, plus the three required fraud-pattern queries (chargeback impact,
burner accounts, velocity attacks). Output is printed AND written to sql_query_output.txt.
"""
import sqlite3
import pandas as pd
import os

DB_PATH = "paytm_payments.db"
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.executescript("""
CREATE TABLE merchants (
    merchant_id   INTEGER PRIMARY KEY,
    merchant_name TEXT NOT NULL,
    category      TEXT NOT NULL,
    region        TEXT NOT NULL
);

CREATE TABLE users (
    user_id       INTEGER PRIMARY KEY,
    signup_date   TEXT NOT NULL
);

CREATE TABLE transactions (
    transaction_id   TEXT PRIMARY KEY,
    user_id          INTEGER NOT NULL,
    merchant_id      INTEGER NOT NULL,
    transaction_time TEXT NOT NULL,
    amount_inr       INTEGER NOT NULL,
    payment_method   TEXT NOT NULL,
    status           TEXT NOT NULL,
    risk_score       INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (merchant_id) REFERENCES merchants(merchant_id)
);
""")

merchants = pd.read_csv("merchants.csv")
users = pd.read_csv("users.csv")
ledger = pd.read_csv("ledger.csv")

merchants.to_sql("merchants", conn, if_exists="append", index=False)
users.to_sql("users", conn, if_exists="append", index=False)
ledger.to_sql("transactions", conn, if_exists="append", index=False)
conn.commit()

log_lines = []


def run(title, sql, clauses):
    log_lines.append("=" * 100)
    log_lines.append(f"QUERY: {title}")
    log_lines.append(f"Clauses demonstrated: {clauses}")
    log_lines.append("-" * 100)
    log_lines.append(sql.strip())
    log_lines.append("-" * 100)
    df = pd.read_sql_query(sql, conn)
    log_lines.append(df.to_string(index=False))
    log_lines.append(f"\n[{len(df)} row(s) returned]\n")
    print("\n".join(log_lines[-6:]))
    return df


# Q1 -- SELECT / WHERE / DISTINCT / ORDER BY / LIMIT, all in one query
q1 = run(
    "Q1: Top 10 distinct (payment_method, amount_inr) pairs among captured transactions",
    """
    SELECT DISTINCT payment_method, amount_inr
    FROM transactions
    WHERE status = 'captured'
    ORDER BY amount_inr DESC
    LIMIT 10;
    """,
    "SELECT, WHERE, DISTINCT, ORDER BY, LIMIT",
)

# Q2 -- GROUP BY / HAVING
q2 = run(
    "Q2: Merchants with more than 10 transactions (volume leaders)",
    """
    SELECT merchant_id, COUNT(*) AS txn_count, SUM(amount_inr) AS total_amount_inr
    FROM transactions
    GROUP BY merchant_id
    HAVING COUNT(*) > 10
    ORDER BY txn_count DESC;
    """,
    "GROUP BY, HAVING, ORDER BY",
)

# Q3 -- INNER JOIN
q3 = run(
    "Q3: Chargeback transactions with merchant detail (INNER JOIN)",
    """
    SELECT t.transaction_id, t.amount_inr, t.transaction_time, m.merchant_name, m.category, m.region
    FROM transactions t
    INNER JOIN merchants m ON t.merchant_id = m.merchant_id
    WHERE t.status = 'chargeback'
    ORDER BY t.amount_inr DESC;
    """,
    "INNER JOIN, WHERE, ORDER BY",
)

# Q4 -- LEFT JOIN (keeps users with zero transactions)
q4 = run(
    "Q4: Every user's transaction count, including users with none (LEFT JOIN)",
    """
    SELECT u.user_id, u.signup_date, COUNT(t.transaction_id) AS txn_count
    FROM users u
    LEFT JOIN transactions t ON u.user_id = t.user_id
    GROUP BY u.user_id
    ORDER BY txn_count ASC, u.user_id ASC
    LIMIT 20;
    """,
    "LEFT JOIN, GROUP BY, ORDER BY, LIMIT",
)

# Q5 -- Chargeback impact quantification
q5 = run(
    "Q5: Chargeback impact -- count, unique users affected, total amount",
    """
    SELECT COUNT(*) AS chargeback_txn_count,
           COUNT(DISTINCT user_id) AS unique_users_affected,
           SUM(amount_inr) AS total_chargeback_amount_inr
    FROM transactions
    WHERE status = 'chargeback';
    """,
    "SELECT, WHERE, aggregate functions",
)

# Q6 -- Burner-account detection: signup_date on/before txn, and strictly < 30 days earlier
q6 = run(
    "Q6: Burner-account chargebacks (0 <= txn_time - signup_date days < 30, status='chargeback') "
    "-- must surface all 15 seeded rows",
    """
    SELECT t.transaction_id, t.user_id, u.signup_date, t.transaction_time,
           (julianday(t.transaction_time) - julianday(u.signup_date)) AS account_age_days,
           t.amount_inr
    FROM transactions t
    INNER JOIN users u ON t.user_id = u.user_id
    WHERE t.status = 'chargeback'
      AND (julianday(t.transaction_time) - julianday(u.signup_date)) >= 0
      AND (julianday(t.transaction_time) - julianday(u.signup_date)) < 30
    ORDER BY account_age_days ASC;
    """,
    "INNER JOIN, WHERE (compound), ORDER BY",
)

# Q7 -- Velocity-attack detection: >=3 txns by the same user within any 10-minute bucket
q7 = run(
    "Q7: Velocity attacks -- users with >=3 transactions in a rounded 10-minute bucket "
    "-- must surface all 8 seeded clusters",
    """
    SELECT user_id,
           strftime('%Y-%m-%d %H:', transaction_time) ||
             printf('%02d', (CAST(strftime('%M', transaction_time) AS INTEGER) / 10) * 10) AS bucket_start,
           COUNT(*) AS txns_in_bucket,
           MIN(transaction_time) AS earliest_txn_in_bucket,
           GROUP_CONCAT(transaction_id) AS transaction_ids
    FROM transactions
    GROUP BY user_id, bucket_start
    HAVING COUNT(*) >= 3
    ORDER BY txns_in_bucket DESC, bucket_start;
    """,
    "GROUP BY, HAVING, ORDER BY, string functions",
)

with open("sql_query_output.txt", "w") as f:
    f.write("\n".join(log_lines))

print("\n\n=== ACCEPTANCE CHECKS ===")
print(f"Q6 burner-account rows surfaced: {len(q6)} (need >= 15)")
print(f"Q7 distinct qualifying (user_id, bucket_start) velocity clusters: {len(q7)} (need >= 8)")

conn.close()
print("\nSaved paytm_payments.db and sql_query_output.txt")
