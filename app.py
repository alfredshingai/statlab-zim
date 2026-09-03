import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from scipy.stats import pearsonr, ttest_ind, chi2_contingency, f_oneway

from src.data_quality import data_quality_summary, column_type_summary, basic_outlier_flags
from src.descriptive import (
    numeric_descriptive_summary,
    categorical_frequency_table,
    categorical_overview,
)
from src.visualizations import (
    get_numeric_columns,
    get_categorical_columns,
    get_date_columns,
    histogram_fig,
    boxplot_fig,
    bar_chart_fig,
    scatter_fig,
    line_chart_fig,
    correlation_heatmap_fig,
)
from src.stats_tests import (
    pearson_test,
    spearman_test,
    linear_regression_test,
    ttest_ind_test,
    chi2_test,
)
from src.export import (
    data_quality_summary_csv_bytes,
    column_type_summary_csv_bytes,
    stats_result_csv_bytes,
    stats_results_combined_csv_bytes,
    chart_to_png_bytes,
)

# --- Page config ---
st.set_page_config(
    page_title="StatLab Zim",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Header ---
st.title("📊 StatLab Zim")
st.markdown(
    "A practical statistical analysis tool for **students, researchers, and businesses**. "
    "Upload a CSV to explore data quality, descriptive statistics, visualizations, and statistical tests."
)
st.divider()

# --- Sidebar navigation ---
st.sidebar.title("🧭 Navigation")
st.sidebar.caption("Choose a section to explore your dataset.")
page = st.sidebar.radio(
    "Go to",
    ["Overview", "Descriptive Statistics", "Visualizations", "Statistical Tests", "Data Quality"],
    help="Overview: preview & structure • Descriptive: numeric/categorical summaries • Visualizations: charts • Tests: inference • Data Quality: missing/duplicates/outliers",
)

st.sidebar.divider()
st.sidebar.info(
    "💡 **Tip:** Upload a CSV file to unlock all sections. "
    "For line charts, include a date column (e.g., `date` or `timestamp`)."
)

# --- File uploader ---
uploaded_file = st.file_uploader(
    "📁 Upload a CSV dataset",
    type=["csv"],
    help="Select a CSV file with a header row. Max 200MB. Example: sales.csv, survey.csv",
)

# --- Helper: test result display ---
def display_test_result(result: dict):
    """Render standardized test result display with full reporting."""
    st.markdown(f"**Test:** {result.get('test_name', 'N/A')}")
    vars_val = result.get("variables", ())
    st.markdown(f"**Variables:** `{vars_val}`")
    hyps = result.get("hypotheses", {})
    if hyps:
        st.markdown(f"**H₀:** {hyps.get('H0', '')}")
        st.markdown(f"**H₁:** {hyps.get('H1', '')}")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        "Statistic",
        f"{result.get('statistic', float('nan')):.3f}" if pd.notna(result.get("statistic", np.nan)) else "N/A",
        help="Test statistic (e.g., r, rho, t, chi², slope/SE)",
    )
    col2.metric(
        "P-value",
        f"{result.get('p_value', float('nan')):.4f}" if pd.notna(result.get("p_value", np.nan)) else "N/A",
        help="Probability of observing this result if H₀ is true",
    )
    col3.metric("Alpha", f"{result.get('alpha', 0.05):.2f}", help="Significance level")
    col4.metric(
        "Decision",
        result.get("decision", "N/A"),
        help="Reject H₀ if p < alpha, otherwise fail to reject",
    )
    # Additional metrics for regression
    if "slope" in result and pd.notna(result.get("slope", np.nan)):
        c1, c2, c3 = st.columns(3)
        c1.metric("Slope", f"{result.get('slope'):.3f}", help="Change in Y per unit X")
        c2.metric("Intercept", f"{result.get('intercept'):.3f}", help="Expected Y when X=0")
        c3.metric("R²", f"{result.get('r_squared'):.3f}", help="Proportion of variance explained")
        st.success(f"**Equation:** `{result.get('equation', '')}`")
    if "degrees_of_freedom" in result and pd.notna(result.get("degrees_of_freedom", np.nan)):
        st.write(f"**Degrees of freedom:** {result.get('degrees_of_freedom')}")
    if "n" in result:
        st.caption(f"Complete observations used: **{result.get('n')}**")
    # Interpretation with context
    decision = result.get("decision", "")
    if decision == "Reject H0":
        st.success(f"**Interpretation:** {result.get('interpretation', '')}")
    elif decision == "Fail to reject H0":
        st.info(f"**Interpretation:** {result.get('interpretation', '')}")
    else:
        st.warning(f"**Interpretation:** {result.get('interpretation', '')}")
    st.markdown(f"**Assumptions:** {result.get('assumptions', '')}")
    warnings = result.get("warnings", [])
    if warnings:
        for w in warnings:
            st.warning(f"⚠️ {w}", icon="⚠️")
    # Export single test result as CSV (Milestone 9)
    try:
        csv_bytes = stats_result_csv_bytes(result)
        st.download_button(
            label=f"⬇️ Download {result.get('test_name', 'test')} result (CSV)",
            data=csv_bytes,
            file_name=f"statlab_{result.get('test_name', 'test').replace(' ', '_').lower()}_result.csv",
            mime="text/csv",
            key=f"dl_{result.get('test_name', 'test')}_{str(result.get('variables', ''))}_{result.get('alpha', 0)}",
            help="Download this test's full reporting as CSV",
        )
    except Exception as e:
        st.error(f"Could not prepare download: {e}")


def chart_png_download(fig, file_name: str, key: str):
    """Provide PNG download for a Plotly figure (optional, requires kaleido)."""
    with st.spinner("Preparing PNG export…"):
        png_bytes = chart_to_png_bytes(fig)
    if png_bytes is not None:
        st.download_button(
            label="🖼️ Download chart as PNG",
            data=png_bytes,
            file_name=file_name,
            mime="image/png",
            key=key,
            help="Download this chart as a high-resolution PNG (requires kaleido)",
        )
    else:
        st.caption("ℹ️ PNG export requires `kaleido` + Chrome. Use browser screenshot or download CSV data instead.")


# --- Main logic ---
if uploaded_file is None:
    # Enhanced empty state (Milestone 11)
    st.info("👋 **Welcome!** Upload a CSV file to begin.", icon="👋")
    with st.expander("What makes a good CSV?", expanded=False):
        st.markdown("""
        - **First row = header** (column names)
        - **Consistent delimiter:** commas
        - **Mixed types are fine:** numeric, categorical, dates
        - **Example header:** `age, income, gender, date, score`
        - **Empty cells** are treated as missing values
        """)
    st.markdown("### 📌 What you can do after upload")
    col1, col2, col3 = st.columns(3)
    col1.markdown("**🔢 Descriptive**\n\n- Count, mean, median, std, IQR, skew, kurtosis, CV")
    col2.markdown("**📈 Visualize**\n\n- Histogram, boxplot, bar, scatter, line, heatmap")
    col3.markdown("**🧪 Test**\n\n- Pearson/Spearman, regression, t-test, chi-square")
    st.stop()

# File present: read with spinner and enhanced error handling
with st.spinner("📖 Reading CSV…"):
    try:
        df = pd.read_csv(uploaded_file)
        if df.empty and len(df.columns) == 0:
            st.error("The uploaded file appears empty or has no columns. Please check the CSV structure.")
            st.stop()
        if df.shape[0] == 0:
            st.warning("The file has a header but no data rows. Visualizations and tests will be limited.", icon="⚠️")
    except pd.errors.EmptyDataError:
        st.error("❌ The file is empty. Please upload a CSV with a header and at least one data row.", icon="❌")
        st.stop()
    except pd.errors.ParserError as e:
        st.error(f"❌ Could not parse CSV: {e}", icon="❌")
        st.info("Ensure the file is comma-separated, UTF-8 encoded, and not corrupted.")
        st.stop()
    except Exception as e:
        st.error(f"❌ Unexpected error reading CSV: {e}", icon="❌")
        st.stop()

# Validate basic structure
if df.columns.duplicated().any():
    st.warning("⚠️ Duplicate column names detected. Consider renaming columns for clarity.", icon="⚠️")

st.success(f"✅ File loaded: **{df.shape[0]} rows × {df.shape[1]} columns**", icon="✅")

dataset_csv = df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="⬇️ Download uploaded dataset",
    data=dataset_csv,
    file_name="statlab_uploaded_dataset.csv",
    mime="text/csv",
    help="Download the exact data currently loaded (with same formatting)",
)

# ============================================================
# 1. OVERVIEW
# ============================================================
if page == "Overview":
    st.header("🔍 Overview")
    st.caption("High-level preview of your dataset's structure and health.")

    with st.spinner("Computing overview metrics…"):
        total_rows = df.shape[0]
        total_columns = df.shape[1]
        total_missing_values = int(df.isna().sum().sum())
        duplicate_rows = int(df.duplicated().sum())

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Rows", total_rows, help="Number of observations")
    col2.metric("Columns", total_columns, help="Number of variables")
    col3.metric("Missing values", total_missing_values, help="Total empty cells")
    col4.metric("Duplicate rows", duplicate_rows, help="Rows that are exact duplicates")

    # Quick health indicator
    if total_missing_values == 0 and duplicate_rows == 0:
        st.success("✨ Dataset looks clean: no missing values or duplicates detected.", icon="✨")
    elif total_missing_values > 0 or duplicate_rows > 0:
        st.info(f"ℹ️ Found **{total_missing_values}** missing cells and **{duplicate_rows}** duplicate rows. See **Data Quality** for details.", icon="ℹ️")

    st.subheader("👀 Dataset preview")
    st.caption("First 10 rows")
    st.dataframe(df.head(10), width="stretch")

    st.subheader("🧱 Column information")
    column_information = pd.DataFrame({
        "Column": df.columns,
        "Data type": df.dtypes.astype(str).values,
        "Missing values": df.isna().sum().values,
        "Unique values": df.nunique().values,
    })
    st.dataframe(column_information, width="stretch")
    column_information_csv = column_information.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download column information (CSV)",
        data=column_information_csv,
        file_name="statlab_column_information.csv",
        mime="text/csv",
        help="Column names, types, missing counts, unique counts",
    )

# ============================================================
# 2. DESCRIPTIVE STATISTICS PAGE
# ============================================================
elif page == "Descriptive Statistics":
    st.header("📊 Descriptive Statistics")
    st.caption("Comprehensive summaries for numeric and categorical variables.")

    # Numeric summary
    st.subheader("🔢 Numeric summary")
    st.caption("Includes: **count, mean, median, std, var, min, max, Q1 (25%), median (50%), Q3 (75%), IQR, skewness, kurtosis, CV (%)**")

    with st.spinner("Calculating numeric statistics…"):
        numeric_summary = numeric_descriptive_summary(df)

    if numeric_summary.empty:
        st.info("No numeric columns were found. If you expected numeric data, check that columns are formatted as numbers (not text) and have no stray symbols.", icon="ℹ️")
    else:
        display_numeric = numeric_summary.copy()
        for col in ["mean", "median", "std", "var", "min", "q25", "q50", "q75", "max", "iqr", "skew", "kurtosis", "cv"]:
            if col in display_numeric.columns:
                display_numeric[col] = display_numeric[col].round(3)

        st.dataframe(display_numeric, width="stretch", height=300)

        # Metric definitions
        with st.expander("📖 Metric definitions", expanded=False):
            st.markdown("""
            - **count**: non-missing observations
            - **mean**: arithmetic average
            - **median**: 50th percentile (Q2)
            - **std**: sample standard deviation (ddof=1)
            - **var**: sample variance (ddof=1)
            - **min / max**: extremes
            - **q25 / q50 / q75**: 25th / 50th / 75th percentiles
            - **iqr**: `Q3 - Q1` (spread of middle 50%)
            - **skew**: skewness (`0` = symmetric, `>0` right-skewed)
            - **kurtosis**: excess kurtosis (`0` = normal tails, `>0` heavy tails)
            - **cv**: coefficient of variation = `std / mean × 100%` (`NaN` if mean=0)
            """)

        numeric_csv = numeric_summary.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Download numeric summary (CSV)",
            data=numeric_csv,
            file_name="statlab_numeric_summary.csv",
            mime="text/csv",
            help="Full precision numeric statistics",
        )

    st.divider()

    # Categorical summary
    st.subheader("🔤 Categorical summary")

    with st.spinner("Analyzing categorical columns…"):
        cat_overview = categorical_overview(df)

    if cat_overview.empty:
        st.info("No categorical columns were found. Columns with text labels (e.g., gender, region) will appear here.", icon="ℹ️")
    else:
        st.write("**Overview per categorical column**")
        st.caption("Shows number of distinct categories and the most frequent value")
        st.dataframe(cat_overview, width="stretch")
        cat_overview_csv = cat_overview.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Download categorical overview (CSV)",
            data=cat_overview_csv,
            file_name="statlab_categorical_overview.csv",
            mime="text/csv",
            help="One row per categorical column",
        )

        categorical_cols = get_categorical_columns(df)
        if not categorical_cols:
            categorical_cols = cat_overview["column"].tolist()

        selected_cat = st.selectbox(
            "Choose a categorical column for frequency table",
            categorical_cols,
            key="cat_freq_selector",
            help="Select a column to see its frequency distribution, proportions, and most common category",
            placeholder="Select categorical column…",
        )

        with st.spinner(f"Building frequency table for '{selected_cat}'…"):
            freq_table = categorical_frequency_table(df, selected_cat)

        st.write(f"**Frequency table for `{selected_cat}`** — {freq_table.shape[0]} categories")
        st.dataframe(freq_table, width="stretch")

        n_cats = freq_table.shape[0]
        most_common_row = freq_table.iloc[0] if not freq_table.empty else None
        if most_common_row is not None:
            st.success(
                f"**Number of categories:** {n_cats} | "
                f"**Most common:** `{most_common_row['Category']}` "
                f"({most_common_row['Count']} occurrences, {most_common_row['Percentage']}%)",
                icon="📌",
            )

        freq_csv = freq_table.to_csv(index=False).encode("utf-8")
        st.download_button(
            label=f"⬇️ Download frequency table for {selected_cat} (CSV)",
            data=freq_csv,
            file_name=f"statlab_freq_{selected_cat}.csv",
            mime="text/csv",
            help="Counts, proportions, and percentages per category",
        )

# ============================================================
# 3. VISUALIZATIONS PAGE
# ============================================================
elif page == "Visualizations":
    st.header("📈 Visualizations")
    st.caption("Explore distributions and relationships. All charts are interactive (zoom, pan, hover).")

    numeric_cols = get_numeric_columns(df)
    categorical_cols = get_categorical_columns(df)
    date_cols = get_date_columns(df)

    # Histogram
    st.subheader("📊 Histogram")
    st.caption("Distribution of a single numeric variable")
    if not numeric_cols:
        st.info("No numeric columns available for histogram. Upload a dataset with numeric values.", icon="ℹ️")
    else:
        hist_col = st.selectbox(
            "Choose a numeric column for histogram",
            numeric_cols,
            key="viz_hist",
            help="Select the numeric variable to visualize. Look for skewness or outliers.",
            placeholder="Select numeric column…",
        )
        bins = st.slider(
            "Number of bins",
            min_value=5, max_value=100, value=30,
            key="hist_bins",
            help="More bins = finer detail. Fewer bins = smoother shape.",
        )
        with st.spinner("Rendering histogram…"):
            fig = histogram_fig(df, hist_col)
            fig.update_traces(nbinsx=bins)
        st.plotly_chart(fig, width="stretch")
        chart_png_download(fig, f"histogram_{hist_col}.png", f"png_hist_{hist_col}")

    st.divider()

    # Boxplot
    st.subheader("📦 Boxplot")
    st.caption("Spread and outliers for a numeric variable (median, quartiles, whiskers)")
    if not numeric_cols:
        st.info("No numeric columns available for boxplot.", icon="ℹ️")
    else:
        box_col = st.selectbox(
            "Choose a numeric column for boxplot",
            numeric_cols,
            key="viz_box",
            help="Box shows Q1, median, Q3. Points beyond whiskers are potential outliers.",
            placeholder="Select numeric column…",
        )
        with st.spinner("Rendering boxplot…"):
            fig = boxplot_fig(df, box_col)
        st.plotly_chart(fig, width="stretch")
        chart_png_download(fig, f"boxplot_{box_col}.png", f"png_box_{box_col}")

    st.divider()

    # Bar chart
    st.subheader("📊 Bar chart")
    st.caption("Frequency of categories")
    if not categorical_cols:
        st.info("No categorical columns available for bar chart. Text or label columns work best.", icon="ℹ️")
    else:
        bar_col = st.selectbox(
            "Choose a categorical column for bar chart",
            categorical_cols,
            key="viz_bar",
            help="Shows count per category. Useful for spotting imbalance.",
            placeholder="Select categorical column…",
        )
        with st.spinner("Rendering bar chart…"):
            fig = bar_chart_fig(df, bar_col)
        st.plotly_chart(fig, width="stretch")
        chart_png_download(fig, f"barchart_{bar_col}.png", f"png_bar_{bar_col}")

    st.divider()

    # Scatter plot
    st.subheader("🔵 Scatter plot")
    st.caption("Relationship between two numeric variables")
    if len(numeric_cols) < 2:
        st.info("At least two numeric columns are needed for a scatter plot. Current numeric columns: " + (", ".join(numeric_cols) if numeric_cols else "none"), icon="ℹ️")
    else:
        sc_col1, sc_col2 = st.columns(2)
        with sc_col1:
            x_col = st.selectbox(
                "X-axis (predictor)",
                numeric_cols,
                key="viz_scatter_x",
                help="Horizontal axis variable",
                placeholder="Select X…",
            )
        with sc_col2:
            y_col = st.selectbox(
                "Y-axis (outcome)",
                numeric_cols,
                index=1 if len(numeric_cols) > 1 else 0,
                key="viz_scatter_y",
                help="Vertical axis variable",
                placeholder="Select Y…",
            )
        if x_col == y_col:
            st.warning("⚠️ Choose two **different** columns for a meaningful scatter plot.", icon="⚠️")
        else:
            with st.spinner("Rendering scatter plot…"):
                fig = scatter_fig(df, x_col, y_col)
            st.plotly_chart(fig, width="stretch")
            chart_png_download(fig, f"scatter_{x_col}_{y_col}.png", f"png_scatter_{x_col}_{y_col}")

    st.divider()

    # Line chart (date + value)
    st.subheader("📈 Line chart (date + value)")
    st.caption("Trend over time — requires a date column")
    if not date_cols:
        st.info("No date columns detected. A date column (e.g., `date`, `time`, `timestamp`) is required for line chart.", icon="ℹ️")
        all_cols = df.columns.tolist()
        with st.expander("Try manual date parsing?"):
            if len(numeric_cols) >= 1:
                lc_date = st.selectbox(
                    "Choose date column (will try to parse as datetime)",
                    all_cols,
                    key="viz_line_date_fallback",
                    help="Select any column that looks like dates. We'll coerce it.",
                )
                lc_val = st.selectbox(
                    "Choose value column",
                    numeric_cols,
                    key="viz_line_val_fallback",
                    help="Numeric variable to track over time",
                )
                if st.button("Generate line chart", help="Attempt to create line chart with selected columns"):
                    with st.spinner("Rendering line chart…"):
                        try:
                            fig = line_chart_fig(df, lc_date, lc_val)
                            st.plotly_chart(fig, width="stretch")
                            chart_png_download(fig, f"line_{lc_date}_{lc_val}.png", f"png_line_{lc_date}_{lc_val}")
                        except Exception as e:
                            st.error(f"Could not create line chart: {e}", icon="❌")
                            st.info("Ensure the date column contains recognizable dates (YYYY-MM-DD) and value column is numeric.")
            else:
                st.info("No numeric value columns available for line chart.", icon="ℹ️")
    else:
        if not numeric_cols:
            st.info("A numeric value column is required for line chart.", icon="ℹ️")
        else:
            lc_c1, lc_c2 = st.columns(2)
            with lc_c1:
                line_date = st.selectbox(
                    "Date column",
                    date_cols,
                    key="viz_line_date",
                    help="Temporal axis. Should be date/datetime type.",
                )
            with lc_c2:
                line_val = st.selectbox(
                    "Value column",
                    numeric_cols,
                    key="viz_line_val",
                    help="Numeric metric to plot over time",
                )
            with st.spinner("Rendering line chart…"):
                try:
                    fig = line_chart_fig(df, line_date, line_val)
                    st.plotly_chart(fig, width="stretch")
                    chart_png_download(fig, f"line_{line_date}_{line_val}.png", f"png_line_{line_date}_{line_val}")
                except Exception as e:
                    st.error(f"Could not create line chart: {e}", icon="❌")

    st.divider()

    # Correlation heatmap
    st.subheader("🔥 Correlation heatmap")
    st.caption("Pairwise Pearson correlations between all numeric variables")
    if len(numeric_cols) < 2:
        st.info("At least two numeric columns are needed for a correlation heatmap.", icon="ℹ️")
    else:
        with st.spinner("Computing correlations…"):
            try:
                fig = correlation_heatmap_fig(df)
                st.plotly_chart(fig, width="stretch")
                chart_png_download(fig, "correlation_heatmap.png", "png_corr_heatmap")
                corr_mat = df[numeric_cols].corr().round(3)
                st.write("**Correlation matrix**")
                st.dataframe(corr_mat, width="stretch")
                corr_csv = corr_mat.to_csv().encode("utf-8")
                st.download_button(
                    label="⬇️ Download correlation matrix (CSV)",
                    data=corr_csv,
                    file_name="statlab_correlation_matrix.csv",
                    mime="text/csv",
                    help="Pairwise correlation coefficients",
                )
            except Exception as e:
                st.error(f"Could not create correlation heatmap: {e}", icon="❌")

# ============================================================
# 4. STATISTICAL TESTS PAGE
# ============================================================
elif page == "Statistical Tests":
    st.header("🧪 Statistical Tests")
    st.caption("Each test reports: **test name, variables, hypotheses, statistic, p-value, alpha, decision, interpretation, assumptions, warnings**.")

    numeric_cols = get_numeric_columns(df)
    categorical_cols = get_categorical_columns(df)

    global_alpha = st.sidebar.slider(
        "Significance level (α)",
        0.01, 0.10, 0.05, 0.01,
        help="Default p-value threshold for all tests. Lower = stricter.",
    )

    collected_results = []

    # Pearson
    st.subheader("1️⃣ Pearson correlation")
    st.caption("Measures **linear** relationship between two numeric variables")
    if len(numeric_cols) < 2:
        st.info("At least two numeric columns are needed for Pearson correlation.", icon="ℹ️")
    else:
        p_c1, p_c2 = st.columns(2)
        with p_c1:
            pearson_x = st.selectbox(
                "First variable (Pearson)",
                numeric_cols,
                key="pearson_x",
                help="Numeric variable. Check scatter plot for linearity.",
                placeholder="Select X…",
            )
        with p_c2:
            pearson_y = st.selectbox(
                "Second variable (Pearson)",
                numeric_cols,
                index=1 if len(numeric_cols) > 1 else 0,
                key="pearson_y",
                help="Second numeric variable",
                placeholder="Select Y…",
            )
        pearson_alpha = st.slider("Alpha (Pearson)", 0.01, 0.10, global_alpha, 0.01, key="pearson_alpha", help="Override global alpha for this test")
        if pearson_x == pearson_y:
            st.warning("⚠️ Choose two **different** variables.", icon="⚠️")
        else:
            with st.spinner("Running Pearson test…"):
                res = pearson_test(df, pearson_x, pearson_y, alpha=pearson_alpha)
            display_test_result(res)
            collected_results.append(res)

    st.divider()

    # Spearman
    st.subheader("2️⃣ Spearman correlation")
    st.caption("Measures **monotonic** (rank) relationship — robust to outliers & non-linearity")
    if len(numeric_cols) < 2:
        st.info("At least two numeric columns are needed for Spearman correlation.", icon="ℹ️")
    else:
        s_c1, s_c2 = st.columns(2)
        with s_c1:
            spearman_x = st.selectbox(
                "First variable (Spearman)",
                numeric_cols,
                key="spearman_x",
                help="Numeric or ordinal variable",
                placeholder="Select X…",
            )
        with s_c2:
            spearman_y = st.selectbox(
                "Second variable (Spearman)",
                numeric_cols,
                index=1 if len(numeric_cols) > 1 else 0,
                key="spearman_y",
                help="Second variable",
                placeholder="Select Y…",
            )
        spearman_alpha = st.slider("Alpha (Spearman)", 0.01, 0.10, global_alpha, 0.01, key="spearman_alpha", help="Override global alpha")
        if spearman_x == spearman_y:
            st.warning("⚠️ Choose two **different** variables.", icon="⚠️")
        else:
            with st.spinner("Running Spearman test…"):
                res = spearman_test(df, spearman_x, spearman_y, alpha=spearman_alpha)
            display_test_result(res)
            collected_results.append(res)

    st.divider()

    # Linear regression
    st.subheader("3️⃣ Simple linear regression")
    st.caption("Model: `Y ~ X`  —  Tests if slope differs from zero")
    if len(numeric_cols) < 2:
        st.info("At least two numeric columns are needed for linear regression.", icon="ℹ️")
    else:
        lr_c1, lr_c2 = st.columns(2)
        with lr_c1:
            lr_x = st.selectbox(
                "Predictor (X)",
                numeric_cols,
                key="lr_x",
                help="Independent variable (horizontal axis)",
                placeholder="Select predictor…",
            )
        with lr_c2:
            lr_y = st.selectbox(
                "Outcome (Y)",
                numeric_cols,
                index=1 if len(numeric_cols) > 1 else 0,
                key="lr_y",
                help="Dependent variable (vertical axis)",
                placeholder="Select outcome…",
            )
        lr_alpha = st.slider("Alpha (Regression)", 0.01, 0.10, global_alpha, 0.01, key="lr_alpha", help="Override global alpha")
        if lr_x == lr_y:
            st.warning("⚠️ Choose two **different** variables.", icon="⚠️")
        else:
            with st.spinner("Fitting linear regression…"):
                res = linear_regression_test(df, lr_x, lr_y, alpha=lr_alpha)
            display_test_result(res)
            collected_results.append(res)
            if pd.notna(res.get("slope", np.nan)):
                with st.spinner("Rendering regression plot…"):
                    try:
                        temp = df[[lr_x, lr_y]].dropna()
                        fig = px.scatter(temp, x=lr_x, y=lr_y, title=f"Regression: {lr_y} ~ {lr_x}", trendline="ols")
                        st.plotly_chart(fig, width="stretch")
                        chart_png_download(fig, f"regression_{lr_x}_{lr_y}.png", f"png_reg_{lr_x}_{lr_y}")
                    except Exception as e:
                        st.warning(f"Could not plot regression line: {e}", icon="⚠️")

    st.divider()

    # Additional tests
    st.subheader("4️⃣ Additional tests")
    st.caption("Choose t-test for numeric vs. 2-group categorical, or chi-square for two categoricals")

    tab1, tab2 = st.tabs(["Independent t-test", "Chi-square test"])

    with tab1:
        st.markdown("**Independent two-sample t-test (Welch)**")
        st.caption("Compares means of a numeric variable across **exactly 2 groups**")
        if not numeric_cols:
            st.info("A numeric column is required for t-test. No numeric variables found.", icon="ℹ️")
        elif not categorical_cols:
            st.info("A categorical grouping column is required. No categorical variables found.", icon="ℹ️")
        else:
            t_num = st.selectbox(
                "Numeric outcome variable",
                numeric_cols,
                key="ttest_num",
                help="Continuous outcome (e.g., score, income)",
                placeholder="Select numeric…",
            )
            t_grp = st.selectbox(
                "Grouping variable (2 groups)",
                categorical_cols,
                key="ttest_grp",
                help="Categorical with exactly 2 levels (e.g., gender, treatment)",
                placeholder="Select group…",
            )
            t_alpha = st.slider("Alpha (t-test)", 0.01, 0.10, global_alpha, 0.01, key="ttest_alpha", help="Override global alpha")
            with st.spinner("Running t-test…"):
                res = ttest_ind_test(df, t_num, t_grp, alpha=t_alpha)
            display_test_result(res)
            collected_results.append(res)
            if "group_means" in res and pd.notna(res["statistic"]):
                st.write(f"**Group means:** {res['group_means']}")

    with tab2:
        st.markdown("**Chi-square test of independence**")
        st.caption("Tests association between two categorical variables")
        if len(categorical_cols) < 2:
            st.info(f"At least two categorical columns are needed. Found: {len(categorical_cols)}", icon="ℹ️")
        else:
            c1, c2 = st.columns(2)
            with c1:
                chi1 = st.selectbox(
                    "First categorical variable",
                    categorical_cols,
                    key="chi1",
                    help="e.g., gender, region",
                    placeholder="Select first…",
                )
            with c2:
                chi2 = st.selectbox(
                    "Second categorical variable",
                    categorical_cols,
                    index=1 if len(categorical_cols) > 1 else 0,
                    key="chi2",
                    help="e.g., preference, outcome",
                    placeholder="Select second…",
                )
            chi_alpha = st.slider("Alpha (Chi-square)", 0.01, 0.10, global_alpha, 0.01, key="chi_alpha", help="Override global alpha")
            if chi1 == chi2:
                st.warning("⚠️ Choose two **different** categorical variables.", icon="⚠️")
            else:
                with st.spinner("Running chi-square test…"):
                    res = chi2_test(df, chi1, chi2, alpha=chi_alpha)
                display_test_result(res)
                collected_results.append(res)
                if "contingency" in res and isinstance(res["contingency"], pd.DataFrame):
                    st.write("**Observed frequencies**")
                    st.dataframe(res["contingency"], width="stretch")
                    if res.get("expected") is not None and not isinstance(res["expected"], float):
                        try:
                            exp_df = pd.DataFrame(res["expected"], index=res["contingency"].index, columns=res["contingency"].columns)
                            st.write("**Expected frequencies** (what H₀ predicts)")
                            st.dataframe(exp_df.round(2), width="stretch")
                        except Exception:
                            pass

    # Combined download
    if collected_results:
        st.divider()
        st.subheader("📥 Export all test results")
        with st.spinner("Preparing combined CSV…"):
            try:
                combined_csv = stats_results_combined_csv_bytes(collected_results)
                st.download_button(
                    label="⬇️ Download all statistical test results (CSV)",
                    data=combined_csv,
                    file_name="statlab_all_test_results.csv",
                    mime="text/csv",
                    help="One row per test with all reporting fields",
                )
            except Exception as e:
                st.error(f"Could not generate combined CSV: {e}", icon="❌")


# ============================================================
# 5. DATA QUALITY
# ============================================================
elif page == "Data Quality":
    st.header("🧹 Data Quality")
    st.caption("Detect missing data, duplicates, outliers, and high-cardinality categories.")

    with st.spinner("Analyzing data quality…"):
        quality_summary = data_quality_summary(df)
        type_summary = column_type_summary(df)
        outlier_flags = basic_outlier_flags(df)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Rows", quality_summary["n_rows"], help="Total observations")
    col2.metric("Columns", quality_summary["n_columns"], help="Total variables")
    col3.metric("Duplicate rows", quality_summary["duplicate_rows"], help="Exact duplicate rows")
    col4.metric("Missing %", f"{quality_summary['total_missing_pct']}%", help="Cells that are empty")
    col5, col6 = st.columns(2)
    col5.metric("Empty columns", quality_summary["empty_columns"], help="Columns with all missing")
    col6.metric("Constant columns", quality_summary["constant_columns"], help="Columns with single value")

    if quality_summary["total_missing_values"] == 0:
        st.success("✅ No missing values detected.", icon="✅")
    else:
        st.warning(f"⚠️ Found **{quality_summary['total_missing_values']}** missing values in columns: {', '.join(quality_summary['columns_with_missing'])}", icon="⚠️")

    st.subheader("📋 Column type summary")
    st.caption("Inferred types: numeric, categorical, date, bool, text")
    st.dataframe(type_summary, width="stretch")

    st.subheader("🚩 Outlier flags (IQR method)")
    st.caption("Counts per numeric column: `Q1 − 1.5·IQR` to `Q3 + 1.5·IQR`")
    if outlier_flags.empty:
        st.info("No numeric columns found for outlier detection.", icon="ℹ️")
    else:
        st.dataframe(outlier_flags, width="stretch")
        if (outlier_flags["outlier_count"] > 0).any():
            st.warning("Some numeric columns have outliers. Check boxplots in Visualizations.", icon="⚠️")

    if quality_summary["high_cardinality_columns"]:
        st.warning(
            f"High-cardinality categorical columns (>50 unique values): **{', '.join(quality_summary['high_cardinality_columns'])}**. "
            "Consider grouping rare categories.",
            icon="⚠️",
        )

    st.divider()
    st.subheader("📥 Exports")

    # Data quality exports (Milestone 9)
    type_csv = column_type_summary_csv_bytes(type_summary)
    st.download_button(
        label="⬇️ Download column quality summary (CSV)",
        data=type_csv,
        file_name="statlab_column_quality_summary.csv",
        mime="text/csv",
        help="Per-column metrics including types, missing, unique counts",
    )
    summary_csv = data_quality_summary_csv_bytes(quality_summary)
    st.download_button(
        label="⬇️ Download data quality summary (metrics CSV)",
        data=summary_csv,
        file_name="statlab_data_quality_summary.csv",
        mime="text/csv",
        help="High-level metrics: rows, columns, duplicates, missing %, etc.",
    )
    if not outlier_flags.empty:
        outlier_csv = outlier_flags.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Download outlier flags (CSV)",
            data=outlier_csv,
            file_name="statlab_outlier_flags.csv",
            mime="text/csv",
            help="Outlier counts per numeric column",
        )
