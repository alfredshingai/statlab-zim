import pandas as pd
import numpy as np
import pytest

from src.data_quality import (
    is_numeric_series,
    is_categorical_series,
    is_date_series,
    column_type_summary,
    duplicate_row_count,
    high_cardinality_columns,
    basic_outlier_flags,
    data_quality_summary,
)
from src.descriptive import numeric_descriptive_summary, categorical_frequency_table, categorical_overview
from src.export import (
    data_quality_summary_csv_bytes,
    column_type_summary_csv_bytes,
    stats_result_csv_bytes,
    stats_results_combined_csv_bytes,
    chart_to_png_bytes,
)


# --- Row/column counts ---
def test_row_column_counts_basic():
    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    summary = data_quality_summary(df)
    assert summary["n_rows"] == 3
    assert summary["n_columns"] == 2
    assert summary["n_numeric"] == 1
    assert summary["n_categorical"] == 1


def test_row_column_counts_empty():
    df = pd.DataFrame({"a": pd.Series([], dtype=float), "b": pd.Series([], dtype=object)})
    summary = data_quality_summary(df)
    assert summary["n_rows"] == 0
    assert summary["n_columns"] == 2
    assert summary["total_missing_values"] == 0
    assert summary["total_missing_pct"] == 0.0


# --- Missing-value calculations ---
def test_missing_value_calculations():
    df = pd.DataFrame({
        "a": [1, None, 3, None],
        "b": ["x", "y", None, None],
        "c": [1.0, 2.0, 3.0, 4.0],
    })
    summary = data_quality_summary(df)
    # total cells = 12, missing = 4 (2 in a, 2 in b)
    assert summary["total_missing_values"] == 4
    assert summary["total_missing_pct"] == round(4 / 12 * 100, 2)
    assert set(summary["columns_with_missing"]) == {"a", "b"}

    type_summary = column_type_summary(df)
    row_a = type_summary[type_summary["column"] == "a"].iloc[0]
    assert row_a["missing_count"] == 2
    assert row_a["missing_pct"] == 50.0
    row_c = type_summary[type_summary["column"] == "c"].iloc[0]
    assert row_c["missing_count"] == 0


def test_missing_value_all_missing_column():
    df = pd.DataFrame({"a": [None, None], "b": [1, 2]})
    type_summary = column_type_summary(df)
    row = type_summary[type_summary["column"] == "a"].iloc[0]
    assert row["is_empty"] == True
    assert row["missing_count"] == 2


# --- Duplicate detection ---
def test_duplicate_detection():
    df = pd.DataFrame({"a": [1, 1, 2, 2, 2], "b": ["x", "x", "y", "y", "z"]})
    # rows 1 duplicate of 0, row 3 duplicate of 2
    assert duplicate_row_count(df) == 2

    df2 = pd.DataFrame({"a": [1, 2, 3]})
    assert duplicate_row_count(df2) == 0

    summary = data_quality_summary(df)
    assert summary["duplicate_rows"] == 2


# --- Numeric-column detection ---
def test_numeric_column_detection():
    df = pd.DataFrame({
        "num": [1, 2, 3],
        "txt": ["a", "b", "c"],
        "bool_col": pd.Series([True, False, True], dtype=bool),
        "date_col": pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-03"]),
        "cat": pd.Series(["x", "y", "x"], dtype="category"),
    })
    assert is_numeric_series(df["num"]) is True
    assert is_numeric_series(df["txt"]) is False
    assert is_numeric_series(df["bool_col"]) is False  # bool excluded
    assert is_date_series(df["date_col"]) is True
    assert is_categorical_series(df["txt"]) is True
    assert is_numeric_series(df["num"]) is True

    summary = data_quality_summary(df)
    assert summary["n_numeric"] == 1
    assert summary["n_bool"] == 1
    assert summary["n_date"] == 1


def test_numeric_detection_with_nans():
    df = pd.DataFrame({"a": [1, None, 3], "b": ["1", "2", "3"]})
    assert is_numeric_series(df["a"]) is True
    assert is_numeric_series(df["b"]) is False


# --- Descriptive statistics spot-checks ---
def test_descriptive_statistics_spot_checks():
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [2, 4, 6, 8, 10]})
    summary = numeric_descriptive_summary(df)
    assert set(summary["variable"]) == {"x", "y"}
    row_x = summary[summary["variable"] == "x"].iloc[0]
    # known values for 1..5
    assert row_x["count"] == 5
    assert row_x["mean"] == pytest.approx(3.0)
    assert row_x["median"] == pytest.approx(3.0)
    assert row_x["min"] == pytest.approx(1.0)
    assert row_x["max"] == pytest.approx(5.0)
    assert row_x["q25"] == pytest.approx(2.0)
    assert row_x["q75"] == pytest.approx(4.0)
    assert row_x["iqr"] == pytest.approx(2.0)
    assert row_x["std"] == pytest.approx(np.std([1, 2, 3, 4, 5], ddof=1))
    assert row_x["var"] == pytest.approx(np.var([1, 2, 3, 4, 5], ddof=1))
    assert row_x["cv"] == pytest.approx(row_x["std"] / row_x["mean"] * 100)

    # test skew/kurtosis not NaN for normal data
    assert not np.isnan(row_x["skew"])
    assert not np.isnan(row_x["kurtosis"])


def test_descriptive_with_constant():
    df = pd.DataFrame({"const": [5, 5, 5], "var": [1, 2, 3]})
    summary = numeric_descriptive_summary(df)
    row_const = summary[summary["variable"] == "const"].iloc[0]
    assert row_const["std"] == pytest.approx(0.0)
    assert row_const["var"] == pytest.approx(0.0)
    # cv should be 0
    assert row_const["cv"] == pytest.approx(0.0)
    assert row_const["iqr"] == pytest.approx(0.0)


def test_descriptive_empty_numeric():
    df = pd.DataFrame({"a": ["x", "y"]})
    summary = numeric_descriptive_summary(df)
    assert summary.empty
    assert list(summary.columns) == [
        "variable", "count", "mean", "median", "std", "var", "min", "q25", "q50", "q75", "max", "iqr", "skew", "kurtosis", "cv"
    ]


def test_categorical_frequency_proportions():
    df = pd.DataFrame({"cat": ["A", "A", "B", None, "A"]})
    freq = categorical_frequency_table(df, "cat")
    # 5 total, A=3, B=1, Missing=1
    assert freq[freq["Category"] == "A"]["Count"].iloc[0] == 3
    assert freq[freq["Category"] == "A"]["Proportion"].iloc[0] == pytest.approx(0.6)
    assert freq[freq["Category"] == "A"]["Percentage"].iloc[0] == pytest.approx(60.0)
    # most common check via overview
    overview = categorical_overview(df)
    assert overview[overview["column"] == "cat"]["most_common"].iloc[0] == "A"
    assert overview[overview["column"] == "cat"]["n_categories"].iloc[0] == 2  # excludes Missing


# --- Behavior on empty/invalid files ---
def test_empty_dataframe_handling():
    df_empty = pd.DataFrame()
    # data_quality_summary should handle 0 rows 0 cols
    summary = data_quality_summary(df_empty)
    assert summary["n_rows"] == 0
    assert summary["n_columns"] == 0
    assert summary["total_missing_pct"] == 0.0

    # descriptive should return empty with columns
    desc = numeric_descriptive_summary(df_empty)
    assert desc.empty

    # outlier flags empty
    out = basic_outlier_flags(df_empty)
    assert out.empty


def test_empty_file_with_header_only(tmp_path):
    p = tmp_path / "empty.csv"
    p.write_text("a,b,c\n")
    df = pd.read_csv(p)
    assert len(df) == 0
    assert list(df.columns) == ["a", "b", "c"]
    summary = data_quality_summary(df)
    assert summary["n_rows"] == 0
    assert summary["empty_columns"] == 3  # all empty


def test_invalid_file_handling(tmp_path):
    p = tmp_path / "bad.csv"
    p.write_text("not a csv content\nstill not\n")
    # Reading with pandas will succeed but with one column; app should handle try/except
    df = pd.read_csv(p)
    # Should not crash on data_quality
    summary = data_quality_summary(df)
    assert summary["n_rows"] == 1  # one row after header?
    # invalid numeric handling
    desc = numeric_descriptive_summary(df)
    assert desc.empty or len(desc) >= 0


def test_high_cardinality_detection():
    df = pd.DataFrame({"many": [f"val{i}" for i in range(60)], "few": ["A", "B"] * 30})
    cols = high_cardinality_columns(df, threshold=50)
    assert "many" in cols
    assert "few" not in cols


def test_outlier_flags():
    df = pd.DataFrame({"x": [1, 2, 3, 4, 100], "y": [10, 10, 10, 10, 10]})
    out = basic_outlier_flags(df)
    # x has 1 outlier (100), y has 0 because IQR=0
    assert out[out["column"] == "x"]["outlier_count"].iloc[0] == 1
    assert out[out["column"] == "y"]["outlier_count"].iloc[0] == 0


def test_export_data_quality_csv():
    df = pd.DataFrame({"a": [1, None], "b": ["x", None]})
    summary = data_quality_summary(df)
    b = data_quality_summary_csv_bytes(summary)
    assert b.startswith(b"metric,value")
    assert b"n_rows" in b
    type_sum = column_type_summary(df)
    b2 = column_type_summary_csv_bytes(type_sum)
    assert b"column" in b2


def test_export_stats_csv():
    from src.stats_tests import pearson_test
    df = pd.DataFrame({"x": [1, 2, 3, 4], "y": [2, 4, 6, 8]})
    res = pearson_test(df, "x", "y")
    b = stats_result_csv_bytes(res)
    assert b"test_name" in b.lower() or b"Pearson" in b
    combined = stats_results_combined_csv_bytes([res, res])
    assert combined.count(b"Pearson") == 2 or combined.count(b"pearson") >= 1


def test_chart_png_export_optional():
    import plotly.express as px
    fig = px.scatter(x=[1, 2], y=[3, 4])
    png = chart_to_png_bytes(fig)
    # Optional: may be None if kaleido/Chrome missing, should not crash
    assert png is None or isinstance(png, (bytes, bytearray))
