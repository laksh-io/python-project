# Smart Expense Tracker - Data Analysis Project

A Python data analysis project built around a desktop expense tracker.

- **`main.py`** - the original Tkinter + SQLite desktop expense tracker (unchanged).
- **Streamlit web app** (`app.py`) - loads a **real public transaction dataset**, shows its structure, cleans it, visualises it and draws conclusions.

## Pages of the web app

| Page | What it shows |
|---|---|
| Project Overview | What the original app does, what was added, how the dataset maps to `main.py` |
| Transaction Manager | Add, edit, delete, search and filter transactions plus monthly summary - the features of `main.py`, stored in `expenses.db` (same table as the desktop app) |
| Dataset | Source and links, column dictionary, searchable raw data, CSV download |
| Data Information | Rows/columns/shape, data types, statistical summary, missing values |
| Data Cleaning | Step-by-step cleaning log, duplicate inspection, before/after types, cleaned CSV download |
| Data Visualisation | Monthly trend, yearly totals, weekday and hour charts, top categories (bar), category and payment-mode (donut), histogram, box plot, correlation heatmap. Filter by year and payment mode |
| Results & Conclusion | Findings (computed from the data), limitations, conclusion |

## Dataset

| | |
|---|---|
| Name | Daily Household Transactions |
| Content | 2,461 real personal transactions of one household in Indian rupees (INR), 01 Jan 2015 - 20 Sep 2018 |
| Columns | Date, Mode, Category, Subcategory, Note, Amount, Income/Expense, Currency |
| Kaggle page | https://www.kaggle.com/datasets/prasad22/daily-transactions-dataset |
| File downloaded from | https://github.com/marcosfabietti/pivot_in_r/blob/main/Daily%20Household%20Transactions.csv |
| Direct download | https://raw.githubusercontent.com/marcosfabietti/pivot_in_r/main/Daily%20Household%20Transactions.csv |
| Stored here as | `data/daily_household_transactions.csv` (unmodified) |
| SHA-256 | `2c594bd0a0bfdb5d7c52ffd0eb1709076c1f10f6db87ce78ddaac4579d726af8` |

**Why this dataset:** `main.py` records transactions with a date, type (income/expense), category, amount and description. This dataset has exactly that structure, so the analysis answers the questions the desktop app cannot.

**Honest notes**
- The file is the original CSV; nothing was added or generated. All cleaning is done in code.
- The data was downloaded from the GitHub copy above (Kaggle itself was not reachable while building the project). The Kaggle listing describes the same data ("2400+ records of daily transactions between 2015 to 2018").
- **Before you publish or submit, open the Kaggle page and confirm the original author and the licence terms**, and credit the author in your report.

## Project structure

```
expense-tracker-analysis/
├── main.py                    # original desktop app (Tkinter + SQLite) - unchanged
├── app.py                     # Streamlit web app (entry point)
├── analysis.py                # loading, data information, cleaning (pandas)
├── charts.py                  # all Plotly charts
├── db.py                      # SQLite storage for the Transaction Manager page
├── import_to_desktop_db.py    # loads the cleaned dataset into main.py's database
├── data/
│   └── daily_household_transactions.csv
├── tests/
│   └── smoke_test.py          # checks the pipeline and every page of the app
├── .streamlit/config.toml     # theme
├── requirements.txt
├── .gitignore
└── README.md
```

## Run locally

Requires Python 3.10 or newer (3.11-3.13 recommended).

```bash
# 1. Get the project
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>

# 2. Create a virtual environment
python -m venv .venv
# Windows:      .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate

# 3. Install the libraries
pip install -r requirements.txt

# 4. Start the web app (opens http://localhost:8501)
streamlit run app.py
```

Optional:

```bash
python tests/smoke_test.py            # run the checks
python import_to_desktop_db.py        # fill expenses.db with the dataset ...
python main.py                        # ... and open it in the desktop app
```

`import_to_desktop_db.py` imports only Income and Expense rows (2,301 rows); `Transfer-Out` rows are skipped because `main.py` has no such type. It refuses to run if `expenses.db` already has data (use `--replace` to overwrite or `--db other.db`).

`main.py` needs Tkinter, which is part of the standard Python installer on Windows/macOS. It is a desktop program, so it is **not** part of the web deployment.

## Transaction Manager notes

- It uses `expenses.db`, the same file and table as `main.py`: on one computer both programs see the same transactions.
- If the tracker is empty, a button loads the real dataset (2,301 income/expense rows) so you can try it.
- On Streamlit Community Cloud the file is **temporary** - entries can disappear when the app restarts. For permanent data use the desktop app on your computer.
- The analysis pages (Data Information, Cleaning, Visualisation, Conclusion) use the dataset, not these entries.

## Data cleaning summary

| Issue found | What was done |
|---|---|
| Date stored as text, two styles (with and without time) | Parsed as day-first datetime; derived year, month, weekday, hour |
| Extra spaces in text (200 values) | Trimmed |
| Same label spelled with different capital letters | Unified to the most frequent spelling |
| 635 missing Subcategory, 521 missing Note | Filled with "Not specified" / "No note"; rows kept |
| 9 exact duplicate rows | All are date-only monthly pairs (e.g. two recurring deposits), so kept by default; option in the sidebar removes them |
| Invalid values (amount ≤ 0, unknown type, future dates, mixed currencies) | Checked - none found |
| Very large amounts | Flagged (`extreme_amount`), not removed: they are real payments |

## Deploy on Streamlit Community Cloud

1. Create a **public** GitHub repository and upload this project (see below).
2. Go to https://share.streamlit.io and sign in with GitHub.
3. Click **Create app** → *Deploy a public app from GitHub*.
4. Choose your repository, branch `main`, and set **Main file path** to `app.py`.
5. Under *Advanced settings*, pick Python 3.11, 3.12 or 3.13.
6. Click **Deploy**. The first build takes a few minutes; you then get a public `*.streamlit.app` link.

The app needs no secrets or API keys.

## Publish to GitHub

```bash
git init
git add .
git status          # check: no expenses.db, no .venv, no .env
git commit -m "Expense tracker data analysis project"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

`.gitignore` keeps out your local database (`expenses.db`), virtual environment, `.env` files and Streamlit secrets, so personal files are not published.

## Limitations

- Results describe one household, not people in general.
- "Income" includes maturity/redemption amounts, so Income − Expenses overstates real savings.
- The number of recorded transactions differs greatly per year; 2018 ends on 20 Sep.
- Categories "Money transfer" and "Investment" are movements of money, not daily consumption.
