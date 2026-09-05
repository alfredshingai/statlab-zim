"""Analysis services — descriptive + statistical tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from src.descriptive import numeric_descriptive_summary, categorical_overview, categorical_frequency_table
    from src.stats_tests import (
        pearson_test,
        spearman_test,
        linear_regression_test,
        ttest_ind_test,
        chi2_test,
    )
except Exception as e:  # pragma: no cover
    raise RuntimeError(f"Failed to import src stats modules: {e}")


def run_descriptive(df: pd.DataFrame, columns: list[str] | None = None) -> dict:
    """Run descriptive summaries; optionally filter to columns."""
    sub = df
    if columns:
        missing = [c for c in columns if c not in df.columns]
        if missing:
            raise ValueError(f"Columns not found: {missing}")
        sub = df[columns]

    num_sum = numeric_descriptive_summary(sub)
    cat_over = categorical_overview(sub)

    # Build frequency tables for each categorical col
    freq_tables = {}
    # cat_over has column names
    if not cat_over.empty:
        for col in cat_over["column"].tolist():
            try:
                ft = categorical_frequency_table(sub, col)
                # Convert to records, NaN -> None
                recs = ft.where(pd.notna(ft), None).to_dict(orient="records")
                # clean numpy
                import numpy as np

                clean = []
                for r in recs:
                    clean.append({k: (None if isinstance(v, float) and np.isnan(v) else v) for k, v in r.items()})
                freq_tables[col] = clean
            except Exception:
                freq_tables[col] = []

    def to_recs(dframe: pd.DataFrame) -> list[dict]:
        if dframe.empty:
            return []
        recs = dframe.where(pd.notna(dframe), None).to_dict(orient="records")
        import numpy as np

        out = []
        for r in recs:
            nr = {}
            for k, v in r.items():
                if isinstance(v, float) and np.isnan(v):
                    nr[k] = None
                elif isinstance(v, (np.integer, np.floating)):
                    nr[k] = float(v) if isinstance(v, np.floating) else int(v)
                else:
                    nr[k] = v
            out.append(nr)
        return out

    return {
        "numeric_summary": to_recs(num_sum),
        "categorical_overview": to_recs(cat_over),
        "frequency_tables": freq_tables,
    }


def run_test(
    df: pd.DataFrame,
    test_type: str,
    alpha: float = 0.05,
    **kwargs,
) -> dict:
    """Dispatch to stats_tests based on test_type."""
    t = test_type.lower().strip()
    # Normalize aliases
    aliases = {
        "pearson": "pearson",
        "pearsonr": "pearson",
        "spearman": "spearman",
        "spearmanr": "spearman",
        "regression": "linear_regression",
        "linear": "linear_regression",
        "linear_regression": "linear_regression",
        "linreg": "linear_regression",
        "ttest": "ttest",
        "t_test": "ttest",
        "t-test": "ttest",
        "chi2": "chi2",
        "chi-square": "chi2",
        "chisq": "chi2",
    }
    norm = aliases.get(t, t)
    if norm == "pearson":
        x_col = kwargs.get("x_col")
        y_col = kwargs.get("y_col")
        if not x_col or not y_col:
            raise ValueError("pearson requires x_col and y_col")
        return pearson_test(df, x_col, y_col, alpha=alpha)
    elif norm == "spearman":
        x_col = kwargs.get("x_col")
        y_col = kwargs.get("y_col")
        if not x_col or not y_col:
            raise ValueError("spearman requires x_col and y_col")
        return spearman_test(df, x_col, y_col, alpha=alpha)
    elif norm == "linear_regression":
        x_col = kwargs.get("x_col")
        y_col = kwargs.get("y_col")
        if not x_col or not y_col:
            raise ValueError("linear_regression requires x_col and y_col")
        return linear_regression_test(df, x_col, y_col, alpha=alpha)
    elif norm == "ttest":
        numeric_col = kwargs.get("numeric_col") or kwargs.get("x_col")
        group_col = kwargs.get("group_col") or kwargs.get("y_col")
        if not numeric_col or not group_col:
            raise ValueError("ttest requires numeric_col and group_col")
        return ttest_ind_test(df, numeric_col, group_col, alpha=alpha)
    elif norm == "chi2":
        col1 = kwargs.get("col1") or kwargs.get("x_col")
        col2 = kwargs.get("col2") or kwargs.get("y_col")
        if not col1 or not col2:
            raise ValueError("chi2 requires col1 and col2 (or x_col/y_col)")
        return chi2_test(df, col1, col2, alpha=alpha)
    else:
        raise ValueError(f"Unsupported test_type '{test_type}'. Allowed: pearson, spearman, linear_regression, ttest, chi2")
