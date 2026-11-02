"""
import_to_desktop_db.py - load the cleaned dataset into the SQLite database used by main.py.

After running it, `python main.py` shows the real transactions in the desktop app.

    python import_to_desktop_db.py              # fills expenses.db (only if it is empty)
    python import_to_desktop_db.py --replace    # deletes existing rows first (asks no questions!)
    python import_to_desktop_db.py --db demo.db # write to another file

Notes
- main.py only knows the types 'Income' and 'Expense', so 'Transfer-Out' rows
  (money moved to savings/investments) are not imported.
- main.py's own file is NOT modified.
"""

import argparse
import sqlite3
from pathlib import Path

import analysis

# Same table definition as ExpenseTracker.setup_database() in main.py
CREATE_TABLE = """
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        txn_date TEXT NOT NULL,
        txn_type TEXT NOT NULL CHECK(txn_type IN ('Income', 'Expense')),
        category TEXT NOT NULL,
        amount REAL NOT NULL CHECK(amount > 0),
        description TEXT
    )
"""


def build_rows():
    """Convert the cleaned dataset into (txn_date, txn_type, category, amount, description) tuples."""
    clean = analysis.clean_data(analysis.load_raw()).data
    clean = clean[clean["type"].isin(["Income", "Expense"])]
    rows = []
    for r in clean.itertuples():
        if r.note != "No note":
            description = r.note
        elif r.subcategory != "Not specified":
            description = r.subcategory
        else:
            description = ""
        rows.append((r.date.strftime("%Y-%m-%d"), str(r.type), r.category, float(r.amount), description))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Import the dataset into the desktop app database.")
    parser.add_argument("--db", default=str(Path(__file__).with_name("expenses.db")), help="SQLite file to fill")
    parser.add_argument("--replace", action="store_true", help="delete existing transactions first")
    args = parser.parse_args()

    rows = build_rows()
    with sqlite3.connect(args.db) as conn:
        conn.execute(CREATE_TABLE)
        existing = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
        if existing and not args.replace:
            print(f"{args.db} already contains {existing} transactions - nothing imported. "
                  "Use --replace to overwrite or --db <other file>.")
            return
        if args.replace:
            conn.execute("DELETE FROM transactions")
        conn.executemany("""INSERT INTO transactions (txn_date, txn_type, category, amount, description)
                            VALUES (?, ?, ?, ?, ?)""", rows)
    print(f"Imported {len(rows)} transactions into {args.db}. Now run: python main.py")


if __name__ == "__main__":
    main()
