"""Visualization helpers for StatLab Zim."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.data_quality import is_numeric_series, is_date_series


def get_numeric_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if is_numeric_series(df[c])]


def get_categorical_columns(df: pd.DataFrame) -> list[str]:
    # categorical = exclude numeric, but include object/category/bool? bool is not numeric per our helper
    return [c for c in df.columns if not is_numeric_series(df[c])]


def get_date_columns(df: pd.DataFrame) -> list[str]:
    cols = []
    for c in df.columns:
        if is_date_series(df[c]):
            cols.append(c)
        else:
            # try to coerce string dates
            try:
                converted = pd.to_datetime(df[c], errors="coerce", utc=False)
                # if at least 50% parseable and original dtype is object
                if converted.notna().sum() / len(df) > 0.5 and df[c].dtype == object:
                    cols.append(c)
            except Exception:
                continue
    return cols


def histogram_fig(df: pd.DataFrame, column: str):
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found")
    fig = px.histogram(
        df,
        x=column,
        title=f"Distribution of {column}",
        labels={column: column, "count": "Frequency"},
    )
    fig.update_layout(bargap=0.1)
    return fig


def boxplot_fig(df: pd.DataFrame, column: str):
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found")
    fig = px.box(
        df,
        y=column,
        title=f"Spread of {column}",
        labels={column: column},
    )
    return fig


def bar_chart_fig(df: pd.DataFrame, column: str):
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found")
    chart_data = (
        df[column]
        .fillna("Missing")
        .value_counts()
        .rename_axis(column)
        .reset_index(name="Count")
    )
    fig = px.bar(
        chart_data,
        x=column,
        y="Count",
        title=f"Categories in {column}",
    )
    return fig


def scatter_fig(df: pd.DataFrame, x_col: str, y_col: str):
    if x_col not in df.columns or y_col not in df.columns:
        raise ValueError("X or Y column not found")
    fig = px.scatter(
        df,
        x=x_col,
        y=y_col,
        title=f"{y_col} against {x_col}",
    )
    return fig


def line_chart_fig(df: pd.DataFrame, date_col: str, value_col: str):
    """
    Line chart for date vs numeric value. Tries to coerce date_col to datetime.
    Sorts by date.
    """
    if date_col not in df.columns or value_col not in df.columns:
        raise ValueError("Date or value column not found")
    temp = df[[date_col, value_col]].copy()
    # coerce date
    if not is_date_series(temp[date_col]):
        temp[date_col] = pd.to_datetime(temp[date_col], errors="coerce")
    temp = temp.dropna(subset=[date_col, value_col])
    temp = temp.sort_values(by=date_col)
    fig = px.line(
        temp,
        x=date_col,
        y=value_col,
        title=f"{value_col} over {date_col}",
        markers=True,
    )
    return fig


def correlation_heatmap_fig(df: pd.DataFrame):
    numeric_cols = get_numeric_columns(df)
    if len(numeric_cols) < 2:
        raise ValueError("At least two numeric columns needed for correlation heatmap")
    corr = df[numeric_cols].corr()
    fig = px.imshow(
        corr,
        text_auto=True,
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
        title="Correlation between numeric variables",
    )
    return fig
