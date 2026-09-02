import streamlit as st
import pandas as pd
import plotly.express as px
from scipy.stats import pearsonr
from scipy.stats import ttest_ind
from scipy.stats import chi2_contingency
from scipy.stats import f_oneway

st.set_page_config(
    page_title="StatLab Zim",
    page_icon="📊",
    layout="wide",
)

st.title("StatLab Zim")

st.write(
    "A practical statistical analysis tool for students, researchers, "
    "and businesses."
)

uploaded_file = st.file_uploader(
    "Upload a CSV dataset",
    type=["csv"],
)

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    st.success("File uploaded successfully.")

    dataset_csv = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download uploaded dataset",
        data=dataset_csv,
        file_name="statlab_uploaded_dataset.csv",
        mime="text/csv",
    )

    st.subheader("Dataset overview")

    total_rows = df.shape[0]
    total_columns = df.shape[1]
    total_missing_values = int(df.isna().sum().sum())

    column1, column2, column3 = st.columns(3)

    column1.metric("Rows", total_rows)
    column2.metric("Columns", total_columns)
    column3.metric("Missing values", total_missing_values)

    st.subheader("Dataset preview")

    st.dataframe(
        df.head(10),
        width="stretch",
    )


    st.subheader("Column information")

    column_information = pd.DataFrame({
        "Column": df.columns,
        "Data type": df.dtypes.astype(str).values,
        "Missing values": df.isna().sum().values,
        "Unique values": df.nunique().values,
    })

    st.dataframe(
        column_information,
        width="stretch",
    )

    column_information_csv = column_information.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        label="Download column information",
        data=column_information_csv,
        file_name="statlab_column_information.csv",
        mime="text/csv",
    )





    st.subheader("Descriptive statistics")


    numeric_data = df.select_dtypes(include="number")

    if numeric_data.empty:
        st.info("No numeric columns were found in this dataset.")
    else:
        descriptive_statistics = numeric_data.describe().transpose()

        st.dataframe(
            descriptive_statistics,
            width="stretch",
        )

        descriptive_statistics_csv = (
            descriptive_statistics.to_csv().encode("utf-8")
        )

        st.download_button(
            label="Download descriptive statistics",
            data=descriptive_statistics_csv,
            file_name="statlab_descriptive_statistics.csv",
            mime="text/csv",
        )

    st.subheader("Categorical summaries")

    categorical_data = df.select_dtypes(exclude="number")

    if categorical_data.empty:
        st.info("No categorical columns were found in this dataset.")
    else:
        selected_column = st.selectbox(
            "Choose a categorical column",
            categorical_data.columns,
        )

        category_counts = (
            categorical_data[selected_column]
            .value_counts(dropna=False)
            .rename_axis("Category")
            .reset_index(name="Count")
        )

        category_counts["Proportion"] = (
            category_counts["Count"] / len(df)
        )

        category_counts["Percentage"] = (
            category_counts["Proportion"] * 100
        ).round(2)

        st.dataframe(
            category_counts,
            width="stretch",
        )

    st.subheader("Visualizations")

    if numeric_data.empty:
        st.info("No numeric columns are available for visualization.")
    else:
        selected_numeric_column = st.selectbox(
            "Choose a numeric column for a histogram",
            numeric_data.columns,
        )

        histogram = px.histogram(
            df,
            x=selected_numeric_column,
            title=f"Distribution of {selected_numeric_column}",
            labels={
                selected_numeric_column: selected_numeric_column,
                "count": "Frequency",
            },
        )

        st.plotly_chart(
            histogram,
            width="stretch",
        )

        boxplot = px.box(
            df,
            y=selected_numeric_column,
            title=f"Spread of {selected_numeric_column}",
            labels={
                selected_numeric_column: selected_numeric_column,
            },
        )

        st.plotly_chart(
            boxplot,
            width="stretch",
        )

    if categorical_data.empty:
        st.info("No categorical columns are available for a bar chart.")
    else:
        selected_category_column = st.selectbox(
            "Choose a categorical column for a bar chart",
            categorical_data.columns,
        )

        category_chart_data = (
            df[selected_category_column]
            .fillna("Missing")
            .value_counts()
            .rename_axis(selected_category_column)
            .reset_index(name="Count")
        )

        bar_chart = px.bar(
            category_chart_data,
            x=selected_category_column,
            y="Count",
            title=f"Categories in {selected_category_column}",
        )

        st.plotly_chart(
            bar_chart,
            width="stretch",
        )
        st.subheader("Numeric relationship")

    if len(numeric_data.columns) < 2:
        st.info("At least two numeric columns are needed for a scatter plot.")
    else:
        scatter_column1, scatter_column2 = st.columns(2)

        with scatter_column1:
            x_column = st.selectbox(
                "Choose the x-axis column",
                numeric_data.columns,
            )

        with scatter_column2:
            y_column = st.selectbox(
                "Choose the y-axis column",
                numeric_data.columns,
                index=1,
            )

        scatter_plot = px.scatter(
            df,
            x=x_column,
            y=y_column,
            title=f"{y_column} against {x_column}",
        )

        st.plotly_chart(
            scatter_plot,
            width="stretch",
        )

    st.subheader("Correlation matrix")

    if len(numeric_data.columns) < 2:
        st.info("At least two numeric columns are needed for a correlation matrix.")
    else:
        correlation_matrix = numeric_data.corr()

        correlation_heatmap = px.imshow(
            correlation_matrix,
            text_auto=True,
            color_continuous_scale="RdBu_r",
            zmin=-1,
            zmax=1,
            title="Correlation between numeric variables",
        )

        st.plotly_chart(
            correlation_heatmap,
            width="stretch",
        )

    st.subheader("Pearson correlation test")

    if len(numeric_data.columns) < 2:
        st.info("At least two numeric columns are needed for Pearson correlation.")
    else:
        pearson_column1, pearson_column2 = st.columns(2)

        with pearson_column1:
            pearson_x = st.selectbox(
                "Choose the first variable",
                numeric_data.columns,
                key="pearson_x",
            )

        with pearson_column2:
            pearson_y = st.selectbox(
                "Choose the second variable",
                numeric_data.columns,
                index=1,
                key="pearson_y",
            )

        pearson_data = df[[pearson_x, pearson_y]].dropna()

        if len(pearson_data) < 3:
            st.warning(
                "At least three complete observations are needed "
                "for Pearson correlation."
            )
        elif pearson_x == pearson_y:
            st.warning("Choose two different variables.")
        else:
            correlation, p_value = pearsonr(
                pearson_data[pearson_x],
                pearson_data[pearson_y],
            )

            result_column1, result_column2 = st.columns(2)

            result_column1.metric(
                "Correlation coefficient",
                f"{correlation:.3f}",
            )

            result_column2.metric(
                "P-value",
                f"{p_value:.4f}",
            )

            st.write(
                f"The Pearson correlation between **{pearson_x}** and "
                f"**{pearson_y}** is **{correlation:.3f}**."
            )

    st.subheader("Independent two-sample t-test")

    if numeric_data.empty:
        st.info("A numeric column is required for a t-test.")
    elif categorical_data.empty:
        st.info("A categorical grouping column is required for a t-test.")
    else:
        ttest_numeric_column = st.selectbox(
            "Choose a numeric outcome variable",
            numeric_data.columns,
            key="ttest_numeric_column",
        )

        ttest_group_column = st.selectbox(
            "Choose a grouping variable",
            categorical_data.columns,
            key="ttest_group_column",
        )

        ttest_data = df[
            [ttest_numeric_column, ttest_group_column]
        ].dropna()

        groups = ttest_data[ttest_group_column].unique()

        if len(groups) != 2:
            st.warning(
                "The selected grouping column must contain exactly two groups."
            )
        else:
            first_group = ttest_data[
                ttest_data[ttest_group_column] == groups[0]
            ][ttest_numeric_column]

            second_group = ttest_data[
                ttest_data[ttest_group_column] == groups[1]
            ][ttest_numeric_column]

            if len(first_group) < 2 or len(second_group) < 2:
                st.warning(
                    "Each group needs at least two observations "
                    "for this test."
                )
            else:
                t_statistic, ttest_p_value = ttest_ind(
                    first_group,
                    second_group,
                    equal_var=False,
                )

                ttest_result_column1, ttest_result_column2 = st.columns(2)

                ttest_result_column1.metric(
                    "T-statistic",
                    f"{t_statistic:.3f}",
                )

                ttest_result_column2.metric(
                    "P-value",
                    f"{ttest_p_value:.4f}",
                )

                st.write(
                    f"Groups compared: **{groups[0]}** and **{groups[1]}**"
                )

                st.write(
                    f"Mean of **{groups[0]}**: "
                    f"**{first_group.mean():.3f}**"
                )

                st.write(
                    f"Mean of **{groups[1]}**: "
                    f"**{second_group.mean():.3f}**"
                )

    st.subheader("Chi-square test of independence")

    if len(categorical_data.columns) < 2:
        st.info(
            "At least two categorical columns are needed "
            "for a chi-square test."
        )
    else:
        chi_column1, chi_column2 = st.columns(2)

        with chi_column1:
            chi_square_column1 = st.selectbox(
                "Choose the first categorical variable",
                categorical_data.columns,
                key="chi_square_column1",
            )

        with chi_column2:
            chi_square_column2 = st.selectbox(
                "Choose the second categorical variable",
                categorical_data.columns,
                index=1,
                key="chi_square_column2",
            )

        if chi_square_column1 == chi_square_column2:
            st.warning("Choose two different categorical variables.")
        else:
            chi_square_data = df[
                [chi_square_column1, chi_square_column2]
            ].dropna()

            contingency_table = pd.crosstab(
                chi_square_data[chi_square_column1],
                chi_square_data[chi_square_column2],
            )

            if contingency_table.shape[0] < 2 or contingency_table.shape[1] < 2:
                st.warning(
                    "Each selected variable must contain at least "
                    "two categories."
                )
            else:
                chi2_statistic, chi2_p_value, degrees_of_freedom, expected = (
                    chi2_contingency(contingency_table)
                )

                chi_result_column1, chi_result_column2 = st.columns(2)

                chi_result_column1.metric(
                    "Chi-square statistic",
                    f"{chi2_statistic:.3f}",
                )

                chi_result_column2.metric(
                    "P-value",
                    f"{chi2_p_value:.4f}",
                )

                st.write(
                    f"Degrees of freedom: **{degrees_of_freedom}**"
                )

                st.write("Observed frequencies")

                st.dataframe(
                    contingency_table,
                    width="stretch",
                )

    st.subheader("One-way ANOVA")

    if numeric_data.empty:
        st.info("A numeric column is required for ANOVA.")
    elif categorical_data.empty:
        st.info("A categorical grouping column is required for ANOVA.")
    else:
        anova_numeric_column = st.selectbox(
            "Choose a numeric outcome variable for ANOVA",
            numeric_data.columns,
            key="anova_numeric_column",
        )

        anova_group_column = st.selectbox(
            "Choose a grouping variable for ANOVA",
            categorical_data.columns,
            key="anova_group_column",
        )

        anova_data = df[
            [anova_numeric_column, anova_group_column]
        ].dropna()

        anova_groups = anova_data[anova_group_column].unique()

        if len(anova_groups) < 3:
            st.warning(
                "ANOVA requires at least three groups."
            )
        else:
            group_values = []

            for group in anova_groups:
                values = anova_data[
                    anova_data[anova_group_column] == group
                ][anova_numeric_column]

                if len(values) >= 2:
                    group_values.append(values)

            if len(group_values) < 3:
                st.warning(
                    "At least three groups need two or more observations each."
                )
            else:
                f_statistic, anova_p_value = f_oneway(*group_values)

                anova_result_column1, anova_result_column2 = st.columns(2)

                anova_result_column1.metric(
                    "F-statistic",
                    f"{f_statistic:.3f}",
                )

                anova_result_column2.metric(
                    "P-value",
                    f"{anova_p_value:.4f}",
                )

                st.write(
                    f"Groups included: **{len(group_values)}**"
                )

                st.write(
                    "ANOVA tests whether there is evidence that at least "
                    "one group mean differs from the others."
                )
else:
    st.info("Upload a CSV file to begin.")