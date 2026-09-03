"""Export utilities for StatLab Zim (Milestone 9)."""

from __future__ import annotations

import io
import pandas as pd


def data_quality_summary_csv_bytes(summary: dict) -> bytes:
    """
    Convert data_quality_summary dict to CSV bytes.
    Flattens list values as comma-joined strings.
    """
    rows = []
    for k, v in summary.items():
        if isinstance(v, list):
            v_str = ", ".join(map(str, v)) if v else ""
        else:
            v_str = v
        rows.append({"metric": k, "value": v_str})
    df = pd.DataFrame(rows)
    return df.to_csv(index=False).encode("utf-8")


def column_type_summary_csv_bytes(type_summary: pd.DataFrame) -> bytes:
    return type_summary.to_csv(index=False).encode("utf-8")


def descriptive_numeric_csv_bytes(numeric_summary: pd.DataFrame) -> bytes:
    return numeric_summary.to_csv(index=False).encode("utf-8")


def stats_result_to_dataframe(result: dict) -> pd.DataFrame:
    """
    Flatten a single statistical test result dict into a one-row DataFrame
    for CSV export. Handles hypotheses, variables, etc.
    """
    flat = {}
    for k, v in result.items():
        if k in ("contingency", "expected"):
            # skip DataFrames/arrays for CSV; they have separate exports
            continue
        if k == "hypotheses" and isinstance(v, dict):
            flat["H0"] = v.get("H0", "")
            flat["H1"] = v.get("H1", "")
        elif k == "variables" and isinstance(v, (tuple, list)):
            flat["variables"] = ", ".join(map(str, v))
        elif k == "warnings" and isinstance(v, list):
            flat["warnings"] = " | ".join(map(str, v))
        elif isinstance(v, dict):
            # generic dict flatten (e.g., group_means, n_per_group)
            flat[k] = str(v)
        elif isinstance(v, list):
            flat[k] = ", ".join(map(str, v))
        else:
            flat[k] = v
    return pd.DataFrame([flat])


def stats_result_csv_bytes(result: dict) -> bytes:
    df = stats_result_to_dataframe(result)
    return df.to_csv(index=False).encode("utf-8")


def stats_results_combined_csv_bytes(results: list[dict]) -> bytes:
    if not results:
        return pd.DataFrame().to_csv(index=False).encode("utf-8")
    dfs = [stats_result_to_dataframe(r) for r in results]
    combined = pd.concat(dfs, ignore_index=True)
    return combined.to_csv(index=False).encode("utf-8")


def chart_to_png_bytes(fig) -> bytes | None:
    """
    Export plotly figure to PNG bytes using kaleido.
    Returns None if kaleido not available or export fails.
    """
    try:
        # Requires kaleido
        return fig.to_image(format="png", scale=2)
    except Exception:
        return None
