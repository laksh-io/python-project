"""
app.py - Streamlit web app for the Smart Expense Tracker data analysis project.

Run with:  streamlit run app.py
Pages: Project Overview | Dataset | Data Information | Data Cleaning | Data Visualisation | Results & Conclusion
"""

import pandas as pd
import streamlit as st

from datetime import datetime

import analysis
import charts
import db

KAGGLE_URL = "https://www.kaggle.com/datasets/prasad22/daily-transactions-dataset"
GITHUB_FILE_URL = "https://github.com/marcosfabietti/pivot_in_r/blob/main/Daily%20Household%20Transactions.csv"
GITHUB_RAW_URL = ("https://raw.githubusercontent.com/marcosfabietti/pivot_in_r/main/"
                  "Daily%20Household%20Transactions.csv")

PAGES = ["Project Overview", "Transaction Manager", "Dataset", "Data Information", "Data Cleaning",
         "Data Visualisation", "Results & Conclusion"]

st.set_page_config(page_title="Smart Expense Tracker - Data Analysis", page_icon="💰", layout="wide")

# ----------------------------------------------------------------------------
# Look and feel (colours follow the original desktop app: navy header, blue accent)
# ----------------------------------------------------------------------------
st.markdown("""
<style>
.block-container {padding-top: 1.6rem; max-width: 1250px;}
.hero {background: linear-gradient(120deg, #172554 0%, #2563EB 100%); color: white;
       padding: 1.6rem 1.8rem; border-radius: 16px; margin-bottom: 1.2rem;}
.hero h1 {color: white; margin: 0 0 .3rem 0; font-size: 1.9rem; line-height: 1.2;}
.hero p {color: #dbe7ff; margin: 0; font-size: 1rem;}
.kpi {background: white; border: 1px solid #E2E8F0; border-radius: 14px; padding: .9rem 1.1rem;
      box-shadow: 0 1px 2px rgba(15,23,42,.05); margin-bottom: .6rem;}
.kpi .label {color: #64748B; font-size: .72rem; font-weight: 700; letter-spacing: .06em; text-transform: uppercase;}
.kpi .value {font-size: 1.55rem; font-weight: 700; margin-top: .15rem;}
.note {background: #EFF6FF; border-left: 4px solid #2563EB; padding: .8rem 1rem; border-radius: 8px;
       color: #1E293B; margin: .6rem 0 1rem 0; font-size: .95rem;}
.warn {background: #FFF7ED; border-left: 4px solid #eb6834; padding: .8rem 1rem; border-radius: 8px;
       color: #1E293B; margin: .6rem 0 1rem 0; font-size: .95rem;}
h2, h3 {color: #172554;}
@media (max-width: 640px) {.hero h1 {font-size: 1.4rem;} .kpi .value {font-size: 1.25rem;}}
</style>
""", unsafe_allow_html=True)


def kpi(label: str, value: str, color: str = "#172554") -> None:
    st.markdown(f'<div class="kpi"><div class="label">{label}</div>'
                f'<div class="value" style="color:{color}">{value}</div></div>', unsafe_allow_html=True)


def hero(title: str, subtitle: str) -> None:
    st.markdown(f'<div class="hero"><h1>{title}</h1><p>{subtitle}</p></div>', unsafe_allow_html=True)


def note(text: str, warning: bool = False) -> None:
    st.markdown(f'<div class="{"warn" if warning else "note"}">{text}</div>', unsafe_allow_html=True)


def show_chart(fig) -> None:
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def rupees(value: float) -> str:
    return f"₹{value:,.0f}"


# ----------------------------------------------------------------------------
# Data (cached so it is only loaded/cleaned once)
# ----------------------------------------------------------------------------
@st.cache_data
def get_raw() -> pd.DataFrame:
    return analysis.load_raw()


@st.cache_data
def get_clean(drop_all_duplicates: bool) -> analysis.CleaningResult:
    return analysis.clean_data(get_raw(), drop_all_exact_duplicates=drop_all_duplicates)


# ----------------------------------------------------------------------------
# Sidebar
# ----------------------------------------------------------------------------
st.sidebar.markdown("## 💰 Expense Tracker")
st.sidebar.caption("Data Analysis Project")
page = st.sidebar.radio("Navigate", PAGES, label_visibility="collapsed")
st.sidebar.divider()
drop_all_dups = st.sidebar.checkbox(
    "Remove ALL exact duplicate rows", value=False,
    help="Off (recommended): only duplicates with a time stamp are removed. "
         "On: also removes the 9 date-only duplicate rows. See the Data Cleaning page.")
st.sidebar.caption("Data: Daily Household Transactions (INR, 2015-2018)")

raw = get_raw()
result = get_clean(drop_all_dups)
clean = result.data
date_min, date_max = clean["timestamp"].min(), clean["timestamp"].max()


# ----------------------------------------------------------------------------
# Page 1 - Project Overview
# ----------------------------------------------------------------------------
def page_overview() -> None:
    hero("Smart Expense Tracker - Data Analysis",
         "From a desktop expense tracker to a data analysis project on real personal transactions")
    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi("Transactions", f"{len(clean):,}", "#2563EB")
    with c2: kpi("Columns (raw)", f"{raw.shape[1]}")
    with c3: kpi("From", f"{date_min:%d %b %Y}")
    with c4: kpi("To", f"{date_max:%d %b %Y}")

    st.subheader("About the original project")
    st.write(
        "`main.py` is a **desktop expense tracker** built with Tkinter and SQLite. You add income and "
        "expense transactions (date, type, category, amount, description), edit or delete them, search and "
        "filter the history, and see the balance, total income, total expenses and a monthly summary. "
        "That program is **kept unchanged** in this repository, and the same features are available in this web app "
        "on the **Transaction Manager** page.")
    st.subheader("What this project adds")
    st.write(
        "The desktop app only shows totals. This project analyses a **real transaction dataset with the same "
        "structure** to answer questions such as: where does the money go, how does spending change over time, "
        "which payment mode is used most, and which categories grow together.")

    st.subheader("How the dataset connects to `main.py`")
    mapping = pd.DataFrame({
        "Dataset column": ["Date", "Income/Expense", "Category", "Amount", "Note / Subcategory", "Mode", "Currency"],
        "Field in main.py": ["txn_date", "txn_type", "category", "amount", "description", "(not in main.py)", "(₹ is used)"],
        "Comment": ["Same idea; dataset has dd/mm/yyyy text, main.py stores YYYY-MM-DD",
                    "Dataset also has 'Transfer-Out' (money moved to savings/investments) - main.py has no such type",
                    "main.py has 10 fixed categories; the dataset has ~50 real ones",
                    "Same",
                    "Used as the description",
                    "Extra information (cash, bank, credit card ...)",
                    "All rows are INR, matching the ₹ in main.py"]})
    st.dataframe(mapping, hide_index=True, width="stretch")
    st.caption("`import_to_desktop_db.py` loads the cleaned dataset into the database used by main.py, "
               "so the desktop app can show the same data.")

    st.subheader("Analysis pipeline")
    st.markdown("**1. Load** the CSV → **2. Inspect** shape, types, statistics, missing values → "
                "**3. Clean** dates, spelling, missing values, duplicates, invalid values → "
                "**4. Visualise** trends, categories, distributions → **5. Conclude**")
    st.subheader("Technology")
    st.write("Python · pandas · Plotly · Streamlit · SQLite/Tkinter (original app)")


# ----------------------------------------------------------------------------
# Page 2 - Transaction Manager (the features of main.py: add / edit / delete / search / summary)
# ----------------------------------------------------------------------------
def page_manager() -> None:
    hero("Transaction Manager", "Add, edit, delete and search transactions - the same features as the desktop app (main.py)")
    if "flash" in st.session_state:
        st.success(st.session_state.pop("flash"))

    if db.count() == 0:
        note("The tracker is empty. Add your first transaction below, or load the real dataset "
             "(2,301 income/expense transactions) to try everything.")
        if st.button("Load the real dataset into the tracker"):
            st.session_state["flash"] = f"{db.load_dataset():,} transactions loaded."
            st.rerun()

    t = db.totals()
    c1, c2, c3 = st.columns(3)
    with c1: kpi("Current balance", rupees(t["balance"]), "#2563EB")
    with c2: kpi("Total income", rupees(t["income"]), "#059669")
    with c3: kpi("Total expenses", rupees(t["expense"]), "#DC2626")

    left, right = st.columns([1, 2], gap="large")

    # ---- Add form -----------------------------------------------------------
    with left:
        st.subheader("Add transaction")
        with st.form("add_form", clear_on_submit=True):
            kind = st.selectbox("Transaction type", ["Expense", "Income"])
            when = st.date_input("Date", value=db.today())
            category = st.selectbox("Category", db.categories())
            amount = st.number_input("Amount (₹)", min_value=0.0, step=1.0, format="%.2f")
            description = st.text_input("Description")
            if st.form_submit_button("＋ Add Transaction", type="primary", width="stretch"):
                try:
                    db.add(when.isoformat(), kind, category, amount, description)
                    st.session_state["flash"] = "Transaction added successfully."
                    st.rerun()
                except ValueError:
                    st.error("Enter a valid date and an amount greater than zero.")

    # ---- History: filter, search, select ---------------------------------------
    with right:
        st.subheader("Transaction history")
        f1, f2 = st.columns([1, 2])
        type_filter = f1.selectbox("Type", ["All", "Income", "Expense"])
        search = f2.text_input("Search", placeholder="category, description or date (e.g. 2018-09)")
        history = db.fetch(type_filter, search)
        st.caption(f"{len(history):,} transactions - click the box at the left of a row to edit or delete it.")
        event = st.dataframe(
            history, hide_index=True, width="stretch", height=340,
            on_select="rerun", selection_mode="single-row", key="history_table",
            column_config={"id": None, "txn_date": "Date", "txn_type": "Type", "category": "Category",
                           "amount": st.column_config.NumberColumn("Amount (₹)", format="₹%.2f"),
                           "description": "Description"})

        # ---- Edit / delete the selected row ---------------------------------
        selected = event.selection.rows
        if selected:
            row = history.iloc[selected[0]]
            st.markdown(f"**Selected:** {row['txn_date']} · {row['category']} · ₹{row['amount']:,.2f}")
            options = db.categories()
            if row["category"] not in options:
                options.append(row["category"])
            try:
                row_date = datetime.strptime(row["txn_date"], "%Y-%m-%d").date()
            except ValueError:
                row_date = db.today()
            with st.form(f"edit_form_{row['id']}"):
                e1, e2 = st.columns(2)
                new_kind = e1.selectbox("Type", ["Expense", "Income"], index=["Expense", "Income"].index(row["txn_type"]))
                new_date = e2.date_input("Date", value=row_date)
                e3, e4 = st.columns(2)
                new_cat = e3.selectbox("Category", options, index=options.index(row["category"]))
                new_amount = e4.number_input("Amount (₹)", min_value=0.0, value=float(row["amount"]), step=1.0, format="%.2f")
                new_desc = st.text_input("Description", value=row["description"] or "")
                if st.form_submit_button("Save changes", type="primary"):
                    try:
                        db.update(row["id"], new_date.isoformat(), new_kind, new_cat, new_amount, new_desc)
                        st.session_state["flash"] = "Transaction updated successfully."
                        st.rerun()
                    except ValueError:
                        st.error("Enter a valid date and an amount greater than zero.")
            confirm = st.checkbox("Yes, delete this transaction permanently", key=f"confirm_{row['id']}")
            if st.button("Delete selected", disabled=not confirm):
                db.delete(row["id"])
                st.session_state["flash"] = "Transaction deleted."
                st.rerun()

    # ---- Monthly summary ---------------------------------------------------------
    with st.expander("Monthly summary"):
        all_rows = db.fetch()
        months = sorted(all_rows["txn_date"].str[:7].unique(), reverse=True) if len(all_rows) else []
        if not months:
            st.write("No transactions recorded yet.")
        else:
            month = st.selectbox("Month", months)
            summary = db.monthly_summary(month)
            inc = summary.loc[summary["Type"] == "Income", "Total"].sum()
            exp = summary.loc[summary["Type"] == "Expense", "Total"].sum()
            s1, s2, s3 = st.columns(3)
            with s1: kpi("Income", rupees(inc), "#059669")
            with s2: kpi("Expenses", rupees(exp), "#DC2626")
            with s3: kpi("Net", rupees(inc - exp), "#2563EB")
            st.dataframe(summary, hide_index=True, width="stretch",
                         column_config={"Total": st.column_config.NumberColumn("Total (₹)", format="₹%.2f")})

    st.caption("Stored in `expenses.db` - the same file and table as main.py. On Streamlit Community Cloud this file "
               "is temporary (it can reset when the app restarts); on your own computer it is permanent. "
               "The analysis pages use the dataset, not these entries.")


# ----------------------------------------------------------------------------
# Page 3 - Dataset
# ----------------------------------------------------------------------------
def page_dataset() -> None:
    hero("Dataset", "Real daily household transactions of one person, in Indian rupees")
    st.markdown(f"""
**Name:** Daily Household Transactions (Kaggle listing: *Daily Transactions Dataset*, "2400+ records of daily transactions between 2015 to 2018")
**File in this project:** `data/daily_household_transactions.csv` (unmodified copy)
**Kaggle page:** [{KAGGLE_URL}]({KAGGLE_URL})
**GitHub copy the file was downloaded from:** [{GITHUB_FILE_URL}]({GITHUB_FILE_URL})
""")
    note("The file is the original CSV, byte for byte - nothing was edited, added or generated. "
         "All cleaning happens in code (see <b>Data Cleaning</b>) and the raw file is never overwritten. "
         "Please check the original author and licence terms on the Kaggle page before publishing.")

    st.subheader("Column dictionary")
    st.dataframe(pd.DataFrame({
        "Column": ["Date", "Mode", "Category", "Subcategory", "Note", "Amount", "Income/Expense", "Currency"],
        "Meaning": ["Date (and often time) of the transaction, as dd/mm/yyyy text",
                    "How it was paid / which account it touched (Cash, Saving Bank account 1, Credit Card ...)",
                    "Main group (Food, Transportation, Salary, Investment ...)",
                    "More detailed group (e.g. Food → snacks)",
                    "Free-text note written by the owner",
                    "Amount in rupees",
                    "Income, Expense, or Transfer-Out (money moved to savings / investments)",
                    "Always INR"]}), hide_index=True, width="stretch")

    st.subheader("Browse the raw data")
    query = st.text_input("Search any text in the raw data", placeholder="e.g. Netflix, Salary, snacks")
    view = raw
    if query:
        mask = raw.astype(str).apply(lambda col: col.str.contains(query, case=False, regex=False)).any(axis=1)
        view = raw[mask]
    st.caption(f"Showing {len(view):,} of {len(raw):,} rows")
    st.dataframe(view, hide_index=True, width="stretch", height=380)
    st.download_button("⬇ Download raw CSV", raw.to_csv(index=False).encode("utf-8"),
                       "daily_household_transactions.csv", "text/csv")


# ----------------------------------------------------------------------------
# Page 3 - Data Information
# ----------------------------------------------------------------------------
def page_info() -> None:
    hero("Data Information", "Structure and quality of the raw dataset, before any cleaning")
    c1, c2, c3, c4 = st.columns(4)
    info = analysis.column_info(raw)
    with c1: kpi("Rows", f"{raw.shape[0]:,}", "#2563EB")
    with c2: kpi("Columns", f"{raw.shape[1]}", "#2563EB")
    with c3: kpi("Shape", f"{raw.shape}")
    with c4: kpi("Missing cells", f"{int(raw.isna().sum().sum()):,}", "#DC2626")

    st.subheader("Column names, data types and missing values")
    st.dataframe(info, hide_index=True, width="stretch")
    note("<b>Reading the table:</b> <code>Date</code> is plain text (not a date type) and is converted during cleaning. "
         "Only <code>Amount</code> is numeric. <code>Subcategory</code> and <code>Note</code> have missing values.")

    left, right = st.columns(2)
    with left:
        st.subheader("Missing values")
        show_chart(charts.missing_bar(info))
    with right:
        st.subheader("Transaction types")
        st.dataframe(raw["Income/Expense"].value_counts().rename_axis("Type").reset_index(name="Rows"),
                     hide_index=True, width="stretch")
        st.caption("'Transfer-Out' = money moved to savings, investments or deposits.")

    st.subheader("Statistical summary - numeric columns")
    st.dataframe(analysis.numeric_summary(raw), width="stretch")
    st.caption("Mean (₹2,751) is far above the median (₹100): a few very large transfers/payments "
               "stretch the distribution.")
    st.subheader("Statistical summary - text columns")
    st.dataframe(analysis.text_summary(raw), hide_index=True, width="stretch")


# ----------------------------------------------------------------------------
# Page 4 - Data Cleaning
# ----------------------------------------------------------------------------
def page_cleaning() -> None:
    hero("Data Cleaning", "Every check and change made to the raw data, step by step")
    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi("Rows before", f"{result.rows_before:,}")
    with c2: kpi("Rows after", f"{result.rows_after:,}", "#059669")
    with c3: kpi("Rows removed", f"{result.rows_before - result.rows_after:,}", "#DC2626")
    with c4: kpi("Columns after", f"{clean.shape[1]}")

    st.subheader("Cleaning log")
    st.dataframe(result.log, hide_index=True, width="stretch")
    note("Steps with 0 rows affected are <b>checks that found nothing wrong</b> - they are listed so the "
         "reader can see that the data was verified, not assumed to be valid.")

    st.subheader("Duplicate records")
    st.write(f"The raw data has **{len(result.duplicates)} rows** that belong to exact-duplicate groups:")
    st.dataframe(result.duplicates, hide_index=False, width="stretch")
    note("All of them are <b>date-only</b> rows (no time stamp). They appear as monthly pairs "
         "(e.g. two ₹1,000 recurring deposits on the 1st of every month from Jul to Dec 2017), which points to "
         "two separate standing instructions rather than accidental copies. They are therefore kept by default. "
         "Tick <i>Remove ALL exact duplicate rows</i> in the sidebar to see the effect of removing them.",
         warning=True)

    st.subheader("Data types: before and after")
    before = pd.DataFrame({"Column": raw.columns, "Before": [str(t) for t in raw.dtypes]})
    after = pd.DataFrame({"Column": clean.columns, "After": [str(t) for t in clean.dtypes]})
    left, right = st.columns(2)
    with left: st.dataframe(before, hide_index=True, width="stretch")
    with right: st.dataframe(after, hide_index=True, width="stretch")

    st.subheader("Missing values after cleaning")
    st.write(f"Total missing cells: **{int(clean.isna().sum().sum()):,}** "
             "(only `hour` is empty where a transaction has no time of day - that is information that "
             "was never recorded, so it is not invented).")
    st.dataframe(analysis.column_info(clean)[["Column", "Data type", "Missing", "Missing %"]],
                 hide_index=True, width="stretch")

    st.subheader("Cleaned data preview")
    st.dataframe(clean.head(100), hide_index=True, width="stretch", height=320)
    st.download_button("⬇ Download cleaned CSV", clean.to_csv(index=False).encode("utf-8"),
                       "cleaned_transactions.csv", "text/csv")


# ----------------------------------------------------------------------------
# Page 5 - Data Visualisation
# ----------------------------------------------------------------------------
def page_visuals() -> None:
    hero("Data Visualisation", "Interactive charts: hover for exact values, use the filters to focus")
    f1, f2 = st.columns(2)
    years = sorted(clean["year"].unique())
    modes = sorted(clean["mode"].astype(str).unique())
    chosen_years = f1.multiselect("Year", years, default=years)
    chosen_modes = f2.multiselect("Payment mode / account", modes, default=modes)
    df = clean[clean["year"].isin(chosen_years) & clean["mode"].astype(str).isin(chosen_modes)]
    if df.empty or (df["type"] == "Expense").sum() == 0:
        st.warning("No expense transactions match these filters. Select at least one year and mode.")
        return

    t = analysis.totals(df)
    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi("Income", rupees(t["income"]), "#2a78d6")
    with c2: kpi("Expenses", rupees(t["expense"]), "#eb6834")
    with c3: kpi("Transfers to savings / investments", rupees(t["transfer"]), "#1baf7a")
    with c4: kpi("Transactions", f"{len(df):,}")

    tab_time, tab_cat, tab_dist, tab_rel = st.tabs(["📈 Trends", "🧩 Categories", "📊 Distribution", "🔥 Relationships"])

    with tab_time:
        show_chart(charts.monthly_trend(df))
        left, right = st.columns(2)
        with left: show_chart(charts.yearly_bars(df))
        with right: show_chart(charts.weekday_bars(df))
        show_chart(charts.hour_bars(df))
        with st.expander("View monthly data table"):
            st.dataframe(analysis.monthly_table(df).round(0), hide_index=True, width="stretch")

    with tab_cat:
        show_chart(charts.top_categories_bar(df))
        left, right = st.columns(2)
        with left: show_chart(charts.category_donut(df))
        with right: show_chart(charts.mode_donut(df))
        with st.expander("View category and payment-mode tables"):
            st.dataframe(charts.category_table(df), hide_index=True, width="stretch")
            st.dataframe(charts.mode_table(df), hide_index=True, width="stretch")

    with tab_dist:
        show_chart(charts.amount_histogram(df))
        show_chart(charts.category_boxplot(df))
        st.caption("Boxes show the middle 50% of amounts; dots are unusually large payments. "
                   "The log scale is used because amounts range from ₹2 to ₹100,000.")

    with tab_rel:
        show_chart(charts.category_correlation(df))
        note("<b>How to read it:</b> each cell is the correlation between two categories' <i>monthly</i> spending. "
             "Blue (+1) = they rise and fall together; orange (-1) = when one rises the other falls; "
             "grey (0) = no relationship. Correlation shows association, not cause.")


# ----------------------------------------------------------------------------
# Page 6 - Results / Conclusion  (all numbers are computed from the data)
# ----------------------------------------------------------------------------
def page_conclusion() -> None:
    hero("Project Results & Conclusion", "What the analysis of the cleaned data shows")
    exp = clean[clean["type"] == "Expense"]
    t = analysis.totals(clean)
    monthly = analysis.monthly_table(clean)
    by_cat = exp.groupby("category", observed=True)["amount"].sum().sort_values(ascending=False)
    living = by_cat.drop(["Money transfer", "Investment"], errors="ignore")   # everyday spending only
    by_mode = exp.groupby("mode", observed=True)["amount"].sum().sort_values(ascending=False)
    by_day = exp.groupby("weekday", observed=False)["amount"].sum()
    top_month = monthly.loc[monthly["Expense"].idxmax()]
    counts_by_year = clean.groupby("year").size()
    food_n = int((exp["category"] == "Food").sum())

    c1, c2, c3 = st.columns(3)
    with c1: kpi("Total expenses", rupees(t["expense"]), "#eb6834")
    with c2: kpi("Total income", rupees(t["income"]), "#2a78d6")
    with c3: kpi("Average monthly expense", rupees(monthly["Expense"].mean()), "#172554")

    st.subheader("Key findings")
    st.markdown(f"""
1. **Biggest categories:** *{by_cat.index[0]}* is the largest expense category with {rupees(by_cat.iloc[0])}
   ({by_cat.iloc[0] / t['expense']:.1%} of all expenses). *Money transfer* and *Investment* are movements of
   money rather than daily consumption; leaving them out, the largest everyday category is
   *{living.index[0]}* ({rupees(living.iloc[0])}, {living.iloc[0] / living.sum():.1%} of everyday spending),
   followed by *{living.index[1]}* and *{living.index[2]}*.
2. **Many small purchases:** the median expense is only {rupees(exp['amount'].median())}, and *Food* alone
   accounts for {food_n:,} of {len(exp):,} expense transactions ({food_n / len(exp):.1%}).
3. **Few large payments drive the totals:** the mean expense ({rupees(exp['amount'].mean())}) is many times the
   median, and {int(clean['extreme_amount'].sum())} expenses are flagged as extreme.
4. **Payment mode:** *{by_mode.index[0]}* carries {by_mode.iloc[0] / t['expense']:.1%} of expense value.
5. **Highest-spending month:** {top_month['month']} with {rupees(top_month['Expense'])}.
6. **Highest-spending weekday:** {by_day.idxmax()} ({rupees(by_day.max())}), lowest: {by_day.idxmin()} ({rupees(by_day.min())}).
7. **Savings behaviour:** {rupees(t['transfer'])} was moved to savings/investments
   (Transfer-Out), i.e. {t['transfer'] / t['income']:.1%} of recorded income.
""")

    st.subheader("Limitations - please read")
    st.markdown(f"""
- **Income is not pure salary.** It also includes maturity/redemption amounts and refunds - money that was
  earlier moved out as Transfer-Out. "Income − Expenses" ({rupees(t['surplus'])}) therefore overstates
  real savings.
- **Uneven coverage:** the number of recorded transactions per year differs a lot
  ({', '.join(f'{y}: {n:,}' for y, n in counts_by_year.items())}), and 2018 ends on {date_max:%d %b %Y}.
  Yearly differences may partly reflect how carefully the owner recorded data.
- **One person's data.** Results describe one household's habits, not people in general.
- **Time of day** is known for only {clean['has_time'].mean():.0%} of transactions.
""")

    st.subheader("Conclusion")
    st.write(
        "The original tracker records transactions and shows totals. Applying the same structure to a real "
        "dataset showed what totals hide: spending is made of many small daily items (mostly food and "
        "transport) while rare large transfers dominate the money flow. The pipeline - load, inspect, clean, "
        "visualise - is fully reproducible from the raw CSV, and the cleaned data can be loaded back into the "
        "desktop app with `import_to_desktop_db.py`.")
    st.subheader("Possible future work")
    st.markdown("- Monthly budget alerts per category\n- Forecasting next month's spending\n"
                "- Automatic category suggestion from the note text")


PAGE_FUNCTIONS = {
    "Project Overview": page_overview,
    "Transaction Manager": page_manager,
    "Dataset": page_dataset,
    "Data Information": page_info,
    "Data Cleaning": page_cleaning,
    "Data Visualisation": page_visuals,
    "Results & Conclusion": page_conclusion,
}
PAGE_FUNCTIONS[page]()
