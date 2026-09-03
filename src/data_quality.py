"""Data quality profiling utilities for StatLab Zim."""

from __future__ import annotations

import numpy as np
import pandas as pd


def is_numeric_series(s: pd.Series) -> bool:
    """Return True if the series is numeric (excluding bool)."""
    return pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s)


def is_categorical_series(s: pd.Series, max_unique_ratio: float = 0.1) -> bool:
    """
    Heuristic: treat as categorical if:
      - dtype is object, string, or category, or
      - numeric but with few unique values relative to length.
    """
    # Check for object / string / category dtypes robustly across pandas 2.x
    is_cat = False
    try:
        if isinstance(s.dtype, pd.CategoricalDtype):
            is_cat = True
    except Exception:
        pass
    if not is_cat:
        try:
            if pd.api.types.is_object_dtype(s) or pd.api.types.is_string_dtype(s):
                is_cat = True
        except Exception:
            pass
    # Fallback for deprecated is_categorical_dtype
    if not is_cat:
        try:
            if pd.api.types.is_categorical_dtype(s):  # type: ignore[attr-defined]
                is_cat = True
        except Exception:
            pass
    if is_cat:
        return True
    if is_numeric_series(s):
        n = s.dropna().nunique()
        ratio = n / len(s) if len(s) > 0 else 0.0
        return ratio <= max_unique_ratio
    return False


def is_date_series(s: pd.Series) -> bool:
    """Return True if the series is datetime-like."""
    return pd.api.types.is_datetime64_any_dtype(s)


def is_bool_series(s: pd.Series) -> bool:
    """Return True if the series is boolean."""
    return pd.api.types.is_bool_dtype(s)


def column_type_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return a DataFrame summarizing column types:
    - column
    - inferred_type: numeric, categorical, date, bool, text
    - dtype
    - missing_count
    - missing_pct
    - unique_count
    - is_constant
    - is_empty
    """
    rows = []
    n_rows = len(df)

    for col in df.columns:
        s = df[col]

        if is_bool_series(s):
            inferred = "bool"
        elif is_date_series(s):
            inferred = "date"
        elif is_numeric_series(s):
            inferred = "numeric"
        elif is_categorical_series(s):
            inferred = "categorical"
        else:
            inferred = "text"

        missing_count = int(s.isna().sum())
        missing_pct = (missing_count / n_rows * 100) if n_rows > 0 else 0.0
        unique_count = int(s.nunique())
        is_constant = unique_count == 1
        is_empty = unique_count == 0 or (missing_count == n_rows)

        rows.append(
            {
                "column": col,
                "inferred_type": inferred,
                "dtype": str(s.dtype),
                "missing_count": missing_count,
                "missing_pct": round(missing_pct, 2),
                "unique_count": unique_count,
                "is_constant": is_constant,
                "is_empty": is_empty,
            }
        )

    if not rows:
        return pd.DataFrame(
            columns=[
                "column",
                "inferred_type",
                "dtype",
                "missing_count",
                "missing_pct",
                "unique_count",
                "is_constant",
                "is_empty",
            ]
        )
    return pd.DataFrame(rows)


def duplicate_row_count(df: pd.DataFrame) -> int:
    """Return the number of duplicate rows (excluding the first occurrence)."""
    return int(df.duplicated().sum())


def high_cardinality_columns(
    df: pd.DataFrame, threshold: int = 50
) -> list[str]:
    """
    Return a list of categorical-like columns with unique count > threshold.
    """
    result = []
    for col in df.columns:
        s = df[col]
        if is_categorical_series(s):
            if s.nunique() > threshold:
                result.append(col)
    return result


def basic_outlier_flags(df: pd.DataFrame) -> pd.DataFrame:
    """
    For each numeric column, flag how many outliers exist using the IQR method.
    Returns a DataFrame: columns -> outlier_count.
    """
    outlier_counts = {}

    for col in df.columns:
        s = df[col]
        if not is_numeric_series(s):
            continue

        q1 = s.quantile(0.25)
        q3 = s.quantile(0.75)
        iqr = q3 - q1

        if iqr == 0:
            outlier_counts[col] = 0
            continue

        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr

        outliers = ((s < lower) | (s > upper)).sum()
        outlier_counts[col] = int(outliers)

    return pd.DataFrame(
        [{"column": col, "outlier_count": cnt} for col, cnt in outlier_counts.items()]
    )


def data_quality_summary(df: pd.DataFrame) -> dict:
    """
    Return a dictionary with a high-level data quality summary:
    - n_rows
    - n_columns
    - n_numeric
    - n_categorical
    - n_date
    - n_bool
    - n_text
    - duplicate_rows
    - empty_columns
    - constant_columns
    - high_cardinality_columns
    - columns_with_missing
    - total_missing_values
    - total_missing_pct
    """
    type_summary = column_type_summary(df)

    n_rows = len(df)
    n_columns = len(df.columns)

    if type_summary.empty:
        n_numeric = n_categorical = n_date = n_bool = n_text = 0
        empty_columns = 0
        constant_columns = 0
        cols_with_missing = []
    else:
        n_numeric = int((type_summary["inferred_type"] == "numeric").sum())
        n_categorical = int((type_summary["inferred_type"] == "categorical").sum())
        n_date = int((type_summary["inferred_type"] == "date").sum())
        n_bool = int((type_summary["inferred_type"] == "bool").sum())
        n_text = int((type_summary["inferred_type"] == "text").sum())
        empty_columns = int(type_summary["is_empty"].sum())
        constant_columns = int(type_summary["is_constant"].sum())
        cols_with_missing = type_summary[type_summary["missing_count"] > 0][
            "column"
        ].tolist()

    duplicate_rows = duplicate_row_count(df)

    high_card_cols = high_cardinality_columns(df)

    total_missing_values = int(df.isna().sum().sum())
    total_cells = n_rows * n_columns
    total_missing_pct = (
        (total_missing_values / total_cells * 100) if total_cells > 0 else 0.0
    )

    return {
        "n_rows": n_rows,
        "n_columns": n_columns,
        "n_numeric": n_numeric,
        "n_categorical": n_categorical,
        "n_date": n_date,
        "n_bool": n_bool,
        "n_text": n_text,
        "duplicate_rows": duplicate_rows,
        "empty_columns": empty_columns,
        "constant_columns": constant_columns,
        "high_cardinality_columns": high_card_cols,
        "columns_with_missing": cols_with_missing,
        "total_missing_values": total_missing_values,
        "total_missing_pct": round(total_missing_pct, 2),
    }
