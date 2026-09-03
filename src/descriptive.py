"""Descriptive statistics utilities for StatLab Zim."""

from __future__ import annotations

import numpy as np
import pandas as pd
from src.data_quality import is_numeric_series


def numeric_descriptive_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return numeric descriptive statistics with:
    count, mean, median, std, var, min, max, q25, q50, q75, iqr, skew, kurtosis, cv

    Columns: variable, count, mean, median, std, var, min, q25, q50, q75, max, iqr, skew, kurtosis, cv

    CV = std / mean * 100 (NaN if mean == 0 or NaN)
    """
    numeric_cols = [c for c in df.columns if is_numeric_series(df[c])]
    if not numeric_cols:
        return pd.DataFrame(
            columns=[
                "variable",
                "count",
                "mean",
                "median",
                "std",
                "var",
                "min",
                "q25",
                "q50",
                "q75",
                "max",
                "iqr",
                "skew",
                "kurtosis",
                "cv",
            ]
        )

    rows = []
    for col in numeric_cols:
        s = pd.to_numeric(df[col], errors="coerce")
        # dropna for count? count is non-missing count
        count = int(s.count())
        if count == 0:
            rows.append(
                {
                    "variable": col,
                    "count": 0,
                    "mean": np.nan,
                    "median": np.nan,
                    "std": np.nan,
                    "var": np.nan,
                    "min": np.nan,
                    "q25": np.nan,
                    "q50": np.nan,
                    "q75": np.nan,
                    "max": np.nan,
                    "iqr": np.nan,
                    "skew": np.nan,
                    "kurtosis": np.nan,
                    "cv": np.nan,
                }
            )
            continue

        mean = float(s.mean())
        median = float(s.median())
        std = float(s.std(ddof=1))
        var = float(s.var(ddof=1))
        min_v = float(s.min())
        max_v = float(s.max())
        q25 = float(s.quantile(0.25))
        q50 = float(s.quantile(0.50))
        q75 = float(s.quantile(0.75))
        iqr = float(q75 - q25)
        skew = float(s.skew())
        kurt = float(s.kurt())
        # kurt in pandas is Fisher's kurtosis (excess), same as scipy
        cv = float(std / mean * 100) if mean != 0 and not np.isnan(mean) and not np.isnan(std) else np.nan

        rows.append(
            {
                "variable": col,
                "count": count,
                "mean": mean,
                "median": median,
                "std": std,
                "var": var,
                "min": min_v,
                "q25": q25,
                "q50": q50,
                "q75": q75,
                "max": max_v,
                "iqr": iqr,
                "skew": skew,
                "kurtosis": kurt,
                "cv": cv,
            }
        )

    return pd.DataFrame(rows)


def categorical_frequency_table(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """
    Return frequency table for a categorical column with:
    Category, Count, Proportion, Percentage
    Sorted by Count descending. Includes NaN as 'Missing' if present.
    """
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found")

    s = df[column].astype(object)
    # Treat NaN as "Missing" for display but keep proportion vs total len
    counts = s.value_counts(dropna=False)
    # Build dataframe
    # Map NaN key to "Missing" string for display
    records = []
    total = len(df)
    for cat, cnt in counts.items():
        label = "Missing" if pd.isna(cat) else cat
        prop = cnt / total if total > 0 else 0
        records.append(
            {
                "Category": label,
                "Count": int(cnt),
                "Proportion": float(prop),
                "Percentage": round(float(prop * 100), 2),
            }
        )
    return pd.DataFrame(records)


def categorical_overview(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return categorical overview per column:
    column, n_categories, most_common, most_common_count, most_common_proportion, total_non_missing
    """
    # Use object/category and exclude pure numeric that is not categorical-like?
    # For this function we consider exclude number dtype as categorical
    cat_cols = [c for c in df.columns if not is_numeric_series(df[c])]
    # Also include numeric categorical? but is_numeric excludes, so numeric not included here.
    # However if user has numeric with few uniques, they might expect it as categorical but we treat separate.
    # To be safe, also treat columns where dtype is object/category regardless of numeric.
    # If no categorical columns, return empty
    if not cat_cols:
        return pd.DataFrame(
            columns=[
                "column",
                "n_categories",
                "most_common",
                "most_common_count",
                "most_common_proportion",
                "total_non_missing",
            ]
        )

    rows = []
    total = len(df)
    for col in cat_cols:
        s = df[col]
        n_cats = int(s.nunique(dropna=True))
        # most common
        vc = s.value_counts(dropna=True)
        if not vc.empty:
            most_common = vc.index[0]
            most_common_count = int(vc.iloc[0])
            most_common_proportion = float(most_common_count / total) if total > 0 else 0
            # handle NaN labels
            if pd.isna(most_common):
                most_common = "Missing"
        else:
            most_common = None
            most_common_count = 0
            most_common_proportion = 0.0

        rows.append(
            {
                "column": col,
                "n_categories": n_cats,
                "most_common": most_common,
                "most_common_count": most_common_count,
                "most_common_proportion": round(most_common_proportion, 4),
                "total_non_missing": int(s.count()),
            }
        )

    return pd.DataFrame(rows)
