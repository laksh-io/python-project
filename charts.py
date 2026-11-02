"""
charts.py - every chart of the project (Plotly). Each function takes the cleaned
DataFrame and returns a Plotly figure, so app.py only has to display it.

Colours: a validated colour-blind-safe categorical palette, assigned in a fixed order.
Income = blue, Expense = orange, Transfer-Out = aqua (same meaning in every chart).
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from analysis import VALID_TYPES, WEEKDAYS, monthly_table

PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
OTHER_GREY = "#9a9a94"
TYPE_COLORS = {"Income": PALETTE[0], "Expense": PALETTE[1], "Transfer-Out": PALETTE[2]}
INK = "#0b0b0b"
INK_SOFT = "#52514e"
GRID = "#e6e6e2"


def _style(fig: go.Figure, title: str, height: int = 420, legend: bool = True) -> go.Figure:
    """Shared look: white surface, light grid, title on the left, legend on top."""
    fig.update_layout(
        title=dict(text=title, x=0, font=dict(size=16, color=INK)),
        template="plotly_white", height=height,
        font=dict(family="Inter, Segoe UI, sans-serif", size=12, color=INK_SOFT),
        margin=dict(l=10, r=10, t=60, b=10), showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(bgcolor="white", font_size=12),
    )
    fig.update_xaxes(showgrid=False, linecolor=GRID)
    fig.update_yaxes(gridcolor=GRID, zeroline=False)
    return fig


def _expenses(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["type"] == "Expense"]


def _top_n_with_other(series: pd.Series, n: int) -> pd.Series:
    """Keep the n largest values and fold the rest into 'Other (combined)'."""
    series = series.sort_values(ascending=False)
    top = series.head(n)
    rest = series.iloc[n:].sum()
    return pd.concat([top, pd.Series({"Other (combined)": rest})]) if rest > 0 else top


# ----------------------------------------------------------------------------
# Time charts
# ----------------------------------------------------------------------------
def monthly_trend(df: pd.DataFrame) -> go.Figure:
    table = monthly_table(df)
    fig = go.Figure()
    for kind in VALID_TYPES:
        fig.add_trace(go.Scatter(
            x=table["month"], y=table[kind], name=kind, mode="lines+markers",
            line=dict(width=2, color=TYPE_COLORS[kind]),
            marker=dict(size=6, line=dict(width=2, color="white")),
            hovertemplate="%{x}<br>" + kind + ": ₹%{y:,.0f}<extra></extra>"))
    fig.update_xaxes(tickangle=-45, nticks=16)
    fig.update_yaxes(title="Amount (₹)", tickformat=",")
    return _style(fig, "Monthly income, expenses and transfers", 430)


def yearly_bars(df: pd.DataFrame) -> go.Figure:
    table = df.pivot_table(index="year", columns="type", values="amount", aggfunc="sum",
                           observed=True, fill_value=0.0)
    last = df["timestamp"].max()
    fig = go.Figure()
    for kind in VALID_TYPES:
        if kind in table:
            fig.add_trace(go.Bar(
                x=[f"{y} (to {last:%d %b})" if y == last.year else str(y) for y in table.index],
                y=table[kind], name=kind, marker=dict(color=TYPE_COLORS[kind], cornerradius=4),
                hovertemplate="%{x}<br>" + kind + ": ₹%{y:,.0f}<extra></extra>"))
    fig.update_layout(barmode="group", bargap=0.35)
    fig.update_yaxes(title="Amount (₹)", tickformat=",")
    return _style(fig, "Yearly totals by transaction type", 400)


def weekday_bars(df: pd.DataFrame) -> go.Figure:
    data = _expenses(df).groupby("weekday", observed=False)["amount"].sum().reindex(WEEKDAYS)
    fig = go.Figure(go.Bar(
        x=data.index, y=data.values, marker=dict(color=PALETTE[1], cornerradius=4),
        hovertemplate="%{x}<br>Expenses: ₹%{y:,.0f}<extra></extra>"))
    fig.update_yaxes(title="Total expenses (₹)", tickformat=",")
    fig.update_layout(bargap=0.35)
    return _style(fig, "Which weekday has the highest spending?", 380, legend=False)


def hour_bars(df: pd.DataFrame) -> go.Figure:
    timed = _expenses(df).dropna(subset=["hour"])
    counts = timed.groupby("hour").size().reindex(range(24), fill_value=0)
    fig = go.Figure(go.Bar(
        x=counts.index, y=counts.values, marker=dict(color=PALETTE[0], cornerradius=4),
        hovertemplate="%{x}:00<br>%{y} expenses<extra></extra>"))
    fig.update_xaxes(title="Hour of day", dtick=2)
    fig.update_yaxes(title="Number of expenses")
    fig.update_layout(bargap=0.3)
    return _style(fig, f"When are expenses recorded? ({len(timed):,} expenses that have a time stamp)",
                  380, legend=False)


# ----------------------------------------------------------------------------
# Category / mode charts
# ----------------------------------------------------------------------------
def top_categories_bar(df: pd.DataFrame, n: int = 10) -> go.Figure:
    data = _expenses(df).groupby("category", observed=True)["amount"].sum().nlargest(n).sort_values()
    fig = go.Figure(go.Bar(
        x=data.values, y=data.index, orientation="h",
        marker=dict(color=PALETTE[1], cornerradius=4),
        text=[f"₹{v:,.0f}" for v in data.values], textposition="outside", cliponaxis=False,
        hovertemplate="%{y}<br>₹%{x:,.0f}<extra></extra>"))
    fig.update_xaxes(title="Total expenses (₹)", tickformat=",")
    fig.update_yaxes(gridcolor="rgba(0,0,0,0)")
    fig.update_layout(bargap=0.35, margin=dict(r=70))
    return _style(fig, f"Top {n} expense categories", 430, legend=False)


def _donut(values: pd.Series, title: str) -> go.Figure:
    colors = PALETTE[: len(values)]
    if "Other (combined)" in values.index:
        colors = PALETTE[: len(values) - 1] + [OTHER_GREY]
    fig = go.Figure(go.Pie(
        labels=values.index, values=values.values, hole=0.55, sort=False,
        marker=dict(colors=colors, line=dict(color="white", width=2)),
        textinfo="label+percent", textposition="outside",
        hovertemplate="%{label}<br>₹%{value:,.0f} (%{percent})<extra></extra>"))
    fig.update_layout(margin=dict(l=40, r=40, t=60, b=30))
    return _style(fig, title, 420, legend=False)


def category_donut(df: pd.DataFrame) -> go.Figure:
    data = _top_n_with_other(_expenses(df).groupby("category", observed=True)["amount"].sum(), 5)
    return _donut(data, "Share of total expenses by category")


def mode_donut(df: pd.DataFrame) -> go.Figure:
    data = _top_n_with_other(_expenses(df).groupby("mode", observed=True)["amount"].sum(), 3)
    return _donut(data, "How expenses were paid")


def category_boxplot(df: pd.DataFrame, n: int = 6) -> go.Figure:
    expenses = _expenses(df)
    top = expenses.groupby("category", observed=True)["amount"].sum().nlargest(n).index
    fig = go.Figure()
    for i, cat in enumerate(top):
        fig.add_trace(go.Box(
            y=expenses.loc[expenses["category"] == cat, "amount"], name=cat,
            marker=dict(color=PALETTE[i % len(PALETTE)], size=4),
            line=dict(width=1.5), boxpoints="outliers",
            hovertemplate=cat + "<br>₹%{y:,.0f}<extra></extra>"))
    fig.update_yaxes(type="log", title="Amount per transaction (₹, log scale)", tickformat=",")
    return _style(fig, f"Spread of amounts in the top {n} expense categories", 430, legend=False)


# ----------------------------------------------------------------------------
# Distribution and relationships
# ----------------------------------------------------------------------------
def amount_histogram(df: pd.DataFrame) -> go.Figure:
    """Expense amounts are very skewed (a few big payments), so the x axis is log10(amount)."""
    amounts = _expenses(df)["amount"]
    fig = go.Figure(go.Histogram(
        x=np.log10(amounts), nbinsx=30, marker=dict(color=PALETTE[1], line=dict(color="white", width=1)),
        hovertemplate="log10(amount) %{x:.2f}<br>%{y} expenses<extra></extra>"))
    ticks = [1, 10, 100, 1000, 10000, 100000]
    fig.update_xaxes(tickvals=np.log10(ticks), ticktext=[f"₹{t:,}" for t in ticks],
                     title="Amount per expense (log scale)")
    fig.update_yaxes(title="Number of expenses")
    fig.update_layout(bargap=0.05)
    median = amounts.median()
    fig.add_vline(x=np.log10(median), line_dash="dash", line_color=INK_SOFT,
                  annotation_text=f"median ₹{median:,.0f}", annotation_position="top right")
    return _style(fig, "Distribution of expense amounts", 400, legend=False)


def category_correlation(df: pd.DataFrame, n: int = 8) -> go.Figure:
    """Correlation of MONTHLY spending between the top expense categories.

    The dataset has only one numeric column (Amount), so a classic numeric correlation matrix
    would be meaningless. Instead: do two categories tend to rise and fall together month by month?
    """
    expenses = _expenses(df)
    top = expenses.groupby("category", observed=True)["amount"].sum().nlargest(n).index
    monthly = (expenses[expenses["category"].isin(top)]
               .pivot_table(index="month", columns="category", values="amount", aggfunc="sum", fill_value=0.0))
    corr = monthly.corr().round(2)
    fig = go.Figure(go.Heatmap(
        z=corr.values, x=corr.columns, y=corr.index, zmin=-1, zmax=1,
        colorscale=[[0, PALETTE[1]], [0.5, "#ececea"], [1, PALETTE[0]]],
        text=corr.values, texttemplate="%{text:.2f}", xgap=2, ygap=2,
        colorbar=dict(title="Correlation", thickness=12),
        hovertemplate="%{y} vs %{x}<br>r = %{z:.2f}<extra></extra>"))
    fig.update_yaxes(autorange="reversed", gridcolor="rgba(0,0,0,0)")
    fig.update_xaxes(tickangle=-35)
    return _style(fig, "Do categories move together? (correlation of monthly spending)", 520, legend=False)


# Used by app.py to show "view data table" under the charts that need one.
def category_table(df: pd.DataFrame) -> pd.DataFrame:
    data = _expenses(df).groupby("category", observed=True)["amount"].agg(["sum", "count", "mean"])
    data = data.sort_values("sum", ascending=False).round(2)
    data["share %"] = (data["sum"] / data["sum"].sum() * 100).round(1)
    return data.rename(columns={"sum": "Total ₹", "count": "Transactions", "mean": "Average ₹"}).reset_index()


def mode_table(df: pd.DataFrame) -> pd.DataFrame:
    data = _expenses(df).groupby("mode", observed=True)["amount"].agg(["sum", "count"]).sort_values("sum", ascending=False)
    data["share %"] = (data["sum"] / data["sum"].sum() * 100).round(1)
    return data.round(2).rename(columns={"sum": "Total ₹", "count": "Transactions"}).reset_index()


def missing_bar(info: pd.DataFrame) -> go.Figure:
    """Bar chart of missing values per column (input: analysis.column_info output)."""
    data = info.sort_values("Missing")
    fig = go.Figure(go.Bar(
        x=data["Missing"], y=data["Column"], orientation="h",
        marker=dict(color=PALETTE[1], cornerradius=4),
        text=[f"{m:,} ({p}%)" for m, p in zip(data["Missing"], data["Missing %"])],
        textposition="outside", cliponaxis=False,
        hovertemplate="%{y}: %{x} missing<extra></extra>"))
    fig.update_xaxes(title="Missing values", range=[0, max(data["Missing"].max() * 1.35, 1)])
    fig.update_yaxes(gridcolor="rgba(0,0,0,0)")
    fig.update_layout(bargap=0.35)
    return _style(fig, "Missing values per column (raw data)", 340, legend=False)
