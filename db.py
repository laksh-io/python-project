"""
db.py - SQLite storage for the Transaction Manager page of the web app.

Uses the SAME table as main.py (transactions: id, txn_date, txn_type, category, amount, description),
so the desktop app and the web app can work on the same expenses.db file when run on one computer.
"""

import os
import sqlite3
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from import_to_desktop_db import CREATE_TABLE, build_rows

# Same default file as main.py. EXPENSES_DB can point somewhere else (used by the tests).
DB_PATH = Path(os.environ.get("EXPENSES_DB", Path(__file__).with_name("expenses.db")))

# Categories offered by main.py's dropdown
DESKTOP_CATEGORIES = ["Food", "Travel", "Shopping", "Education", "Bills", "Health",
                      "Entertainment", "Rent", "Salary", "Other"]


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(CREATE_TABLE)
    return conn


def validate(txn_date: str, amount) -> float:
    """Same rules as main.py: valid YYYY-MM-DD date and amount > 0. Returns the amount."""
    datetime.strptime(txn_date, "%Y-%m-%d")
    value = float(amount)
    if value <= 0:
        raise ValueError("Amount must be greater than zero")
    return value


def fetch(txn_type: str = "All", search: str = "") -> pd.DataFrame:
    query = "SELECT id, txn_date, txn_type, category, amount, description FROM transactions WHERE 1=1"
    params = []
    if txn_type in ("Income", "Expense"):
        query += " AND txn_type=?"
        params.append(txn_type)
    if search.strip():
        query += " AND (category LIKE ? OR description LIKE ? OR txn_date LIKE ?)"
        params.extend([f"%{search.strip()}%"] * 3)
    query += " ORDER BY txn_date DESC, id DESC"
    with _connect() as conn:
        return pd.read_sql_query(query, conn, params=params)


def count() -> int:
    with _connect() as conn:
        return conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]


def categories() -> list:
    """main.py's categories plus any other category already stored (e.g. from the dataset)."""
    with _connect() as conn:
        stored = [r[0] for r in conn.execute("SELECT DISTINCT category FROM transactions ORDER BY category")]
    return DESKTOP_CATEGORIES + [c for c in stored if c not in DESKTOP_CATEGORIES]


def add(txn_date: str, txn_type: str, category: str, amount, description: str) -> None:
    value = validate(txn_date, amount)
    with _connect() as conn:
        conn.execute("""INSERT INTO transactions (txn_date, txn_type, category, amount, description)
                        VALUES (?, ?, ?, ?, ?)""", (txn_date, txn_type, category, value, description.strip()))


def update(txn_id: int, txn_date: str, txn_type: str, category: str, amount, description: str) -> None:
    value = validate(txn_date, amount)
    with _connect() as conn:
        conn.execute("""UPDATE transactions SET txn_date=?, txn_type=?, category=?, amount=?, description=?
                        WHERE id=?""", (txn_date, txn_type, category, value, description.strip(), int(txn_id)))


def delete(txn_id: int) -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM transactions WHERE id=?", (int(txn_id),))


def totals() -> dict:
    """Balance, income and expenses (the three cards of main.py)."""
    with _connect() as conn:
        income = conn.execute("SELECT COALESCE(SUM(amount),0) FROM transactions WHERE txn_type='Income'").fetchone()[0]
        expense = conn.execute("SELECT COALESCE(SUM(amount),0) FROM transactions WHERE txn_type='Expense'").fetchone()[0]
    return {"income": income, "expense": expense, "balance": income - expense}


def monthly_summary(month: str) -> pd.DataFrame:
    """Per type and category totals for 'YYYY-MM' (same query as main.py's Monthly Summary)."""
    with _connect() as conn:
        return pd.read_sql_query(
            """SELECT txn_type AS Type, category AS Category, SUM(amount) AS Total
               FROM transactions WHERE substr(txn_date,1,7)=?
               GROUP BY txn_type, category ORDER BY txn_type, SUM(amount) DESC""", conn, params=[month])


def load_dataset() -> int:
    """Fill an EMPTY tracker with the real dataset (Income/Expense rows). Returns rows added."""
    if count() > 0:
        return 0
    rows = build_rows()
    with _connect() as conn:
        conn.executemany("""INSERT INTO transactions (txn_date, txn_type, category, amount, description)
                            VALUES (?, ?, ?, ?, ?)""", rows)
    return len(rows)


def today() -> date:
    return date.today()
