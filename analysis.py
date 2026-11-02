"""
analysis.py - data loading, data information and data cleaning.

Pure pandas, no Streamlit code, so it can be tested and reused on its own.
Dataset: "Daily Household Transactions" (real personal transactions in INR,
01 Jan 2015 - 20 Sep 2018). See README.md for the source and download link.
"""

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

DATA_PATH = Path(__file__).parent / "data" / "daily_household_transactions.csv"

# Dataset column -> clean column name used everywhere in this project.
COLUMN_RENAMES = {
    "Date": "date_raw",
    "Mode": "mode",
    "Category": "category",
    "Subcategory": "subcategory",
    "Note": "note",
    "Amount": "amount",
    "Income/Expense": "type",
    "Currency": "currency",
}
VALID_TYPES = ["Income", "Expense", "Transfer-Out"]
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


# ----------------------------------------------------------------------------
# 1. Loading
# ----------------------------------------------------------------------------
def load_raw(path: Path = DATA_PATH) -> pd.DataFrame:
    """Read the original CSV exactly as it is (no changes)."""
    return pd.read_csv(path)


# ----------------------------------------------------------------------------
# 2. Data information
# ----------------------------------------------------------------------------
def column_info(df: pd.DataFrame) -> pd.DataFrame:
    """One row per column: data type, non-null count, missing count and unique values."""
    return pd.DataFrame({
        "Column": df.columns,
        "Data type": [str(t) for t in df.dtypes],
        "Non-null": df.notna().sum().values,
        "Missing": df.isna().sum().values,
        "Missing %": (df.isna().mean() * 100).round(2).values,
        "Unique values": df.nunique().values,
    })


def numeric_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Statistical summary (count, mean, std, quartiles ...) of numeric columns."""
    return df.select_dtypes("number").describe().T.round(2)


def text_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Summary of the text columns: unique values, most frequent value and its count."""
    rows = []
    for col in df.select_dtypes(exclude="number").columns:
        counts = df[col].value_counts()
        rows.append({
            "Column": col,
            "Count": int(df[col].notna().sum()),
            "Unique": int(df[col].nunique()),
            "Most frequent": counts.index[0] if len(counts) else "-",
            "Frequency": int(counts.iloc[0]) if len(counts) else 0,
        })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------
# 3. Cleaning
# ----------------------------------------------------------------------------
@dataclass
class CleaningResult:
    data: pd.DataFrame            # the cleaned data
    log: pd.DataFrame             # what was checked / changed, step by step
    duplicates: pd.DataFrame      # rows that are exact duplicates (for inspection)
    rows_before: int
    rows_after: int


def _canonical_spelling(series: pd.Series) -> pd.Series:
    """Make spellings that differ only by letter case identical.

    For every group of values equal after lower-casing, the most frequent
    spelling is used, e.g. 'Small Cap fund 2' and 'Small cap fund 2'.
    """
    clean = series.dropna()
    key = clean.str.casefold()
    most_common = clean.groupby(key).agg(lambda s: s.value_counts().index[0])
    out = series.copy()
    mask = series.notna()
    out[mask] = series[mask].str.casefold().map(most_common)
    return out


def _upper_first(series: pd.Series) -> pd.Series:
    """'subscription' -> 'Subscription' (only the first letter is changed)."""
    return series.str[:1].str.upper() + series.str[1:]


def _parse_dates(raw: pd.Series) -> pd.Series:
    """Parse the two date styles in the file: 'dd/mm/YYYY HH:MM:SS' and 'dd/mm/YYYY'.

    Day-first order is certain: the file contains days above 12 in the first
    position (e.g. 20/09/2018) and never in the second.
    """
    stamped = pd.to_datetime(raw, format="%d/%m/%Y %H:%M:%S", errors="coerce")
    date_only = pd.to_datetime(raw, format="%d/%m/%Y", errors="coerce")
    return stamped.fillna(date_only)


def clean_data(raw: pd.DataFrame, drop_all_exact_duplicates: bool = False) -> CleaningResult:
    """Clean the raw dataset and return the data plus a log of every step.

    drop_all_exact_duplicates:
        False (default) - only duplicates that carry a time-of-day stamp are removed
                          (the same second twice cannot be a coincidence). Duplicates
                          on date-only rows are kept: in this data they are repeated
                          monthly pairs (two standing instructions), not copy errors.
        True            - every exact duplicate row is removed.
    """
    log = []
    df = raw.rename(columns=COLUMN_RENAMES).copy()
    rows_before = len(df)

    def add(step, found, action, rows_changed):
        log.append({"Step": step, "What was found": found,
                    "Action taken": action, "Rows affected": int(rows_changed)})

    # -- 1. Whitespace in text columns --------------------------------------
    text_cols = ["mode", "category", "subcategory", "note", "type", "currency"]
    changed = 0
    for col in text_cols:
        before = df[col].copy()
        df[col] = df[col].str.strip().str.replace(r"\s+", " ", regex=True)
        changed += int((before.notna() & (before != df[col])).sum())
    add("Trim whitespace", "Leading/trailing/double spaces in text values (mostly the Note column)",
        "Stripped and collapsed spaces", changed)

    # -- 2. Dates: text -> datetime ------------------------------------------
    df["has_time"] = df["date_raw"].str.contains(":", na=False)
    df["timestamp"] = _parse_dates(df["date_raw"])
    bad_dates = int(df["timestamp"].isna().sum())
    df = df[df["timestamp"].notna()]
    add("Fix date type", "Date stored as text in two different styles "
        f"({int(df['has_time'].sum())} with time, {int((~df['has_time']).sum())} date only)",
        f"Parsed as day-first datetimes; {bad_dates} unreadable dates dropped",
        len(df) + bad_dates)

    # -- 3. Amount and type validity ------------------------------------------
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    invalid_amount = int((df["amount"].isna() | (df["amount"] <= 0)).sum())
    invalid_type = int((~df["type"].isin(VALID_TYPES)).sum())
    future = int((df["timestamp"] > pd.Timestamp.now()).sum())
    df = df[(df["amount"] > 0) & df["type"].isin(VALID_TYPES) & (df["timestamp"] <= pd.Timestamp.now())]
    add("Invalid values",
        f"{invalid_amount} amounts that are missing/zero/negative, {invalid_type} unknown transaction types, "
        f"{future} dates in the future",
        "Rows with invalid values would be dropped (none were found)" if invalid_amount + invalid_type + future == 0
        else "Dropped those rows", invalid_amount + invalid_type + future)

    currencies = sorted(df["currency"].dropna().unique())
    add("Currency check", f"Currencies present: {', '.join(currencies)}",
        "Single currency, so amounts are comparable as they are" if len(currencies) == 1
        else "Several currencies - amounts are NOT converted", 0)

    # -- 4. Inconsistent spelling ---------------------------------------------
    changed = 0
    for col in ["mode", "category", "subcategory"]:
        before = df[col].copy()
        df[col] = _canonical_spelling(df[col])
        if col == "category":
            df[col] = _upper_first(df[col])
        changed += int((before.notna() & (before != df[col])).sum())
    add("Standardise spelling", "Same label written with different letter case "
        "(e.g. 'subscription', 'maid', 'Small cap fund 1' vs 'Small Cap fund 2')",
        "Unified to the most frequent spelling; category starts with a capital letter", changed)

    # -- 5. Missing values ----------------------------------------------------
    missing_sub = int(df["subcategory"].isna().sum())
    missing_note = int(df["note"].isna().sum())
    df["subcategory"] = df["subcategory"].fillna("Not specified")
    df["note"] = df["note"].fillna("No note")
    add("Missing values", f"{missing_sub} missing Subcategory, {missing_note} missing Note "
        "(no missing Date, Amount, Category, Mode or Type)",
        "Filled with 'Not specified' / 'No note'. Rows kept: the amount and category are still valid",
        missing_sub + missing_note)

    # -- 6. Duplicates ----------------------------------------------------------
    raw_cols = ["date_raw", "mode", "category", "subcategory", "note", "amount", "type", "currency"]
    is_dup = df.duplicated(subset=raw_cols, keep="first")
    all_dup_rows = df[df.duplicated(subset=raw_cols, keep=False)].sort_values(raw_cols)
    n_dup = int(is_dup.sum())
    if drop_all_exact_duplicates:
        to_drop = is_dup
        action = "Removed every exact duplicate (option chosen in the sidebar)"
    else:
        to_drop = is_dup & df["has_time"]
        action = ("Removed duplicates that have a time stamp; kept date-only duplicates because they look like "
                  "genuine repeated entries (e.g. two recurring deposits on the 1st of each month)")
    df = df[~to_drop]
    add("Duplicate records", f"{n_dup} exact duplicate rows ({len(all_dup_rows)} rows involved)",
        action, int(to_drop.sum()))

    # -- 7. Derived columns -------------------------------------------------------
    df["date"] = df["timestamp"].dt.normalize()
    df["year"] = df["timestamp"].dt.year
    df["month"] = df["timestamp"].dt.strftime("%Y-%m")
    df["weekday"] = pd.Categorical(df["timestamp"].dt.day_name(), categories=WEEKDAYS, ordered=True)
    df["hour"] = df["timestamp"].dt.hour.where(df["has_time"])   # only known when a time was recorded
    add("Derived columns", "Date parts were needed for the analysis",
        "Added year, month, weekday and hour (hour only where a time was recorded)", len(df))

    # -- 8. Extreme amounts: flagged, not removed ------------------------------------
    expense_amounts = df.loc[df["type"] == "Expense", "amount"]
    q1, q3 = expense_amounts.quantile([0.25, 0.75])
    limit = q3 + 3 * (q3 - q1)
    df["extreme_amount"] = (df["type"] == "Expense") & (df["amount"] > limit)
    add("Extreme amounts", f"{int(df['extreme_amount'].sum())} expenses above Q3 + 3xIQR (> Rs {limit:,.0f})",
        "Flagged in column 'extreme_amount' but kept: they are real purchases/payments, not errors",
        int(df["extreme_amount"].sum()))

    # -- 9. Final types -------------------------------------------------------------------
    df["type"] = df["type"].astype("category")
    df["mode"] = df["mode"].astype("category")
    df = df.drop(columns=["date_raw"]).sort_values("timestamp").reset_index(drop=True)
    df = df[["timestamp", "date", "year", "month", "weekday", "hour", "has_time", "type", "category",
             "subcategory", "mode", "note", "amount", "currency", "extreme_amount"]]
    add("Final column types", "Types after cleaning", "type/mode -> category, amount -> float, dates -> datetime", len(df))

    return CleaningResult(data=df, log=pd.DataFrame(log), duplicates=all_dup_rows[raw_cols],
                          rows_before=rows_before, rows_after=len(df))


# ----------------------------------------------------------------------------
# 4. Small helpers used by the charts and the conclusion page
# ----------------------------------------------------------------------------
def totals(df: pd.DataFrame) -> dict:
    """Total income, expense and transfers (money moved to savings/investments)."""
    by_type = df.groupby("type", observed=True)["amount"].sum()
    income = float(by_type.get("Income", 0.0))
    expense = float(by_type.get("Expense", 0.0))
    transfer = float(by_type.get("Transfer-Out", 0.0))
    return {"income": income, "expense": expense, "transfer": transfer,
            "surplus": income - expense}


def monthly_table(df: pd.DataFrame) -> pd.DataFrame:
    """Income / Expense / Transfer-Out per calendar month (months with no data are filled with 0)."""
    table = df.pivot_table(index="month", columns="type", values="amount", aggfunc="sum",
                           observed=True, fill_value=0.0)
    for col in VALID_TYPES:
        if col not in table:
            table[col] = 0.0
    full = pd.period_range(table.index.min(), table.index.max(), freq="M").strftime("%Y-%m")
    return table.reindex(full, fill_value=0.0)[VALID_TYPES].rename_axis("month").reset_index()


def month_label(value: float) -> str:
    """Format a rupee amount for display."""
    return f"₹{value:,.0f}"


if __name__ == "__main__":      # quick check:  python analysis.py
    raw_df = load_raw()
    print("Raw shape:", raw_df.shape)
    result = clean_data(raw_df)
    print("Clean shape:", result.data.shape)
    print(result.log.to_string(index=False))
    print(np.round(list(totals(result.data).values()), 2))
