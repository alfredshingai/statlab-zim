"""Statistical tests utilities for StatLab Zim."""

from __future__ import annotations

import warnings
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr, ttest_ind, chi2_contingency
from scipy import stats


def _decision(p_value: float, alpha: float = 0.05) -> str:
    if np.isnan(p_value):
        return "Inconclusive"
    return "Reject H0" if p_value < alpha else "Fail to reject H0"


def pearson_test(
    df: pd.DataFrame, x_col: str, y_col: str, alpha: float = 0.05
) -> dict:
    """
    Pearson correlation test.
    Returns dict with test_name, variables, hypotheses, statistic, p_value, alpha, decision, interpretation, assumptions, warnings
    """
    warnings_list = []
    if x_col == y_col:
        warnings_list.append("Variables must be different.")
    s = df[[x_col, y_col]].dropna()
    n = len(s)
    if n < 3:
        return {
            "test_name": "Pearson correlation",
            "variables": (x_col, y_col),
            "hypotheses": {
                "H0": "No linear correlation (r = 0)",
                "H1": "Linear correlation exists (r != 0)",
            },
            "statistic": np.nan,
            "p_value": np.nan,
            "alpha": alpha,
            "n": n,
            "decision": "Inconclusive",
            "interpretation": f"Insufficient data: need at least 3 complete observations, found {n}.",
            "assumptions": "Bivariate normality, linearity, no outliers, independent observations.",
            "warnings": warnings_list + [f"Only {n} complete observations."] if n < 3 else warnings_list,
            "effect_size": np.nan,
        }

    x = pd.to_numeric(s[x_col], errors="coerce")
    y = pd.to_numeric(s[y_col], errors="coerce")
    # check constant
    if x.nunique() <= 1 or y.nunique() <= 1:
        warnings_list.append("One variable is constant; correlation undefined.")

    try:
        r, p = pearsonr(x, y)
    except Exception as e:
        warnings_list.append(str(e))
        r, p = np.nan, np.nan

    decision = _decision(p, alpha)
    if np.isnan(r):
        interpretation = "Correlation could not be computed."
    elif decision == "Reject H0":
        direction = "positive" if r > 0 else "negative"
        interpretation = f"Significant {direction} linear correlation (r={r:.3f}, p={p:.4f} < {alpha})."
    else:
        interpretation = f"No significant linear correlation (r={r:.3f}, p={p:.4f} >= {alpha})."

    return {
        "test_name": "Pearson correlation",
        "variables": (x_col, y_col),
        "hypotheses": {
            "H0": "No linear correlation (r = 0)",
            "H1": "Linear correlation exists (r != 0)",
        },
        "statistic": float(r) if not np.isnan(r) else np.nan,
        "p_value": float(p) if not np.isnan(p) else np.nan,
        "alpha": alpha,
        "n": n,
        "decision": decision,
        "interpretation": interpretation,
        "assumptions": "Bivariate normality, linear relationship, independent observations, no extreme outliers. Check scatter plot.",
        "warnings": warnings_list,
        "effect_size": float(r) if not np.isnan(r) else np.nan,
    }


def spearman_test(
    df: pd.DataFrame, x_col: str, y_col: str, alpha: float = 0.05
) -> dict:
    """Spearman rank correlation."""
    warnings_list = []
    if x_col == y_col:
        warnings_list.append("Variables must be different.")
    s = df[[x_col, y_col]].dropna()
    n = len(s)
    if n < 3:
        return {
            "test_name": "Spearman correlation",
            "variables": (x_col, y_col),
            "hypotheses": {"H0": "No monotonic association (rho = 0)", "H1": "Monotonic association exists (rho != 0)"},
            "statistic": np.nan,
            "p_value": np.nan,
            "alpha": alpha,
            "n": n,
            "decision": "Inconclusive",
            "interpretation": f"Insufficient data: need at least 3 observations, found {n}.",
            "assumptions": "Ordinal or continuous variables, monotonic relationship, independent observations.",
            "warnings": warnings_list + [f"Only {n} observations."],
            "effect_size": np.nan,
        }

    x = pd.to_numeric(s[x_col], errors="coerce")
    y = pd.to_numeric(s[y_col], errors="coerce")
    if x.nunique() <= 1 or y.nunique() <= 1:
        warnings_list.append("One variable is constant; correlation undefined.")

    try:
        rho, p = spearmanr(x, y)
    except Exception as e:
        warnings_list.append(str(e))
        rho, p = np.nan, np.nan

    decision = _decision(p, alpha)
    if np.isnan(rho):
        interpretation = "Spearman correlation could not be computed."
    elif decision == "Reject H0":
        direction = "positive" if rho > 0 else "negative"
        interpretation = f"Significant {direction} monotonic association (rho={rho:.3f}, p={p:.4f} < {alpha})."
    else:
        interpretation = f"No significant monotonic association (rho={rho:.3f}, p={p:.4f} >= {alpha})."

    return {
        "test_name": "Spearman correlation",
        "variables": (x_col, y_col),
        "hypotheses": {"H0": "No monotonic association (rho = 0)", "H1": "Monotonic association exists (rho != 0)"},
        "statistic": float(rho) if not np.isnan(rho) else np.nan,
        "p_value": float(p) if not np.isnan(p) else np.nan,
        "alpha": alpha,
        "n": n,
        "decision": decision,
        "interpretation": interpretation,
        "assumptions": "Monotonic relationship, independent observations, ordinal/continuous data; robust to outliers vs Pearson.",
        "warnings": warnings_list,
        "effect_size": float(rho) if not np.isnan(rho) else np.nan,
    }


def linear_regression_test(
    df: pd.DataFrame, x_col: str, y_col: str, alpha: float = 0.05
) -> dict:
    """
    Simple linear regression: y ~ x
    Returns slope, intercept, r_squared, p_value, etc.
    """
    warnings_list = []
    s = df[[x_col, y_col]].dropna()
    n = len(s)
    if n < 3:
        return {
            "test_name": "Simple linear regression",
            "variables": (x_col, y_col),
            "hypotheses": {"H0": "Slope = 0 (no linear relationship)", "H1": "Slope != 0"},
            "statistic": np.nan,
            "p_value": np.nan,
            "alpha": alpha,
            "n": n,
            "decision": "Inconclusive",
            "interpretation": f"Insufficient data: need at least 3 observations, found {n}.",
            "assumptions": "Linearity, independence, homoscedasticity, normality of residuals.",
            "warnings": warnings_list + [f"Only {n} observations."],
            "slope": np.nan,
            "intercept": np.nan,
            "r_squared": np.nan,
            "r_value": np.nan,
            "std_err": np.nan,
        }

    x = pd.to_numeric(s[x_col], errors="coerce").to_numpy()
    y = pd.to_numeric(s[y_col], errors="coerce").to_numpy()

    if np.unique(x).size <= 1:
        warnings_list.append("X is constant; regression undefined.")

    try:
        lin = stats.linregress(x, y)
        slope = float(lin.slope)
        intercept = float(lin.intercept)
        r_value = float(lin.rvalue)
        r_squared = float(lin.rvalue ** 2)
        p = float(lin.pvalue)
        std_err = float(lin.stderr)
        statistic = float(lin.slope / lin.stderr) if lin.stderr != 0 else np.nan
    except Exception as e:
        warnings_list.append(str(e))
        slope = intercept = r_value = r_squared = p = std_err = statistic = np.nan

    decision = _decision(p, alpha)
    if np.isnan(slope):
        interpretation = "Regression could not be computed."
    elif decision == "Reject H0":
        interpretation = f"Significant linear relationship (slope={slope:.3f}, p={p:.4f} < {alpha}, R²={r_squared:.3f})."
    else:
        interpretation = f"No significant linear relationship (slope={slope:.3f}, p={p:.4f} >= {alpha}, R²={r_squared:.3f})."

    return {
        "test_name": "Simple linear regression",
        "variables": (x_col, y_col),
        "hypotheses": {"H0": "Slope = 0 (no linear relationship)", "H1": "Slope != 0"},
        "statistic": statistic,
        "p_value": p,
        "alpha": alpha,
        "n": n,
        "decision": decision,
        "interpretation": interpretation,
        "assumptions": "Linearity, independence, homoscedasticity, normality of residuals, no influential outliers. Check residual plots.",
        "warnings": warnings_list,
        "slope": slope,
        "intercept": intercept,
        "r_value": r_value,
        "r_squared": r_squared,
        "std_err": std_err,
        "equation": f"y = {slope:.3f} * x + {intercept:.3f}" if not np.isnan(slope) else "N/A",
    }


def ttest_ind_test(
    df: pd.DataFrame, numeric_col: str, group_col: str, alpha: float = 0.05, equal_var: bool = False
) -> dict:
    """Independent two-sample t-test (Welch by default)."""
    warnings_list = []
    s = df[[numeric_col, group_col]].dropna()
    groups = s[group_col].unique()
    if len(groups) != 2:
        return {
            "test_name": "Independent two-sample t-test",
            "variables": (numeric_col, group_col),
            "hypotheses": {"H0": "Group means are equal", "H1": "Group means differ"},
            "statistic": np.nan,
            "p_value": np.nan,
            "alpha": alpha,
            "decision": "Inconclusive",
            "interpretation": f"Grouping column must have exactly 2 groups, found {len(groups)}: {list(groups)}.",
            "assumptions": "Independent observations, normality within groups, equal or unequal variances (Welch).",
            "warnings": warnings_list + [f"Found {len(groups)} groups."],
            "groups": list(groups),
            "n": len(s),
        }

    g1 = s[s[group_col] == groups[0]][numeric_col]
    g2 = s[s[group_col] == groups[1]][numeric_col]
    n1, n2 = len(g1), len(g2)
    if n1 < 2 or n2 < 2:
        warnings_list.append("Each group needs at least 2 observations.")

    if g1.nunique() <= 1 or g2.nunique() <= 1:
        warnings_list.append("One group is constant; t-test may be unreliable.")

    try:
        stat, p = ttest_ind(g1, g2, equal_var=equal_var, nan_policy="omit")
        stat = float(stat)
        p = float(p)
    except Exception as e:
        warnings_list.append(str(e))
        stat, p = np.nan, np.nan

    decision = _decision(p, alpha)
    if np.isnan(stat):
        interpretation = "t-test could not be computed."
    elif decision == "Reject H0":
        interpretation = f"Significant mean difference between {groups[0]} and {groups[1]} (t={stat:.3f}, p={p:.4f} < {alpha})."
    else:
        interpretation = f"No significant mean difference (t={stat:.3f}, p={p:.4f} >= {alpha})."

    return {
        "test_name": "Independent two-sample t-test (Welch)" if not equal_var else "Independent two-sample t-test",
        "variables": (numeric_col, group_col),
        "hypotheses": {"H0": "Group means are equal", "H1": "Group means differ"},
        "statistic": stat,
        "p_value": p,
        "alpha": alpha,
        "decision": decision,
        "interpretation": interpretation,
        "assumptions": "Independent observations, approximately normal distribution within each group, homogeneity of variance if equal_var=True; Welch robust to unequal variances.",
        "warnings": warnings_list,
        "groups": list(groups),
        "group_means": {str(groups[0]): float(g1.mean()), str(groups[1]): float(g2.mean())},
        "n": len(s),
        "n_per_group": {str(groups[0]): int(n1), str(groups[1]): int(n2)},
    }


def chi2_test(
    df: pd.DataFrame, col1: str, col2: str, alpha: float = 0.05
) -> dict:
    """Chi-square test of independence."""
    warnings_list = []
    if col1 == col2:
        warnings_list.append("Variables must be different.")
    s = df[[col1, col2]].dropna()
    n = len(s)
    if n == 0:
        return {
            "test_name": "Chi-square test of independence",
            "variables": (col1, col2),
            "hypotheses": {"H0": "Variables are independent", "H1": "Variables are associated"},
            "statistic": np.nan,
            "p_value": np.nan,
            "alpha": alpha,
            "decision": "Inconclusive",
            "interpretation": "No data after dropping missing values.",
            "assumptions": "Independent observations, expected cell counts >=5 (warning if violated).",
            "warnings": warnings_list + ["No data."],
            "n": n,
            "degrees_of_freedom": np.nan,
        }

    contingency = pd.crosstab(s[col1], s[col2])
    if contingency.shape[0] < 2 or contingency.shape[1] < 2:
        return {
            "test_name": "Chi-square test of independence",
            "variables": (col1, col2),
            "hypotheses": {"H0": "Variables are independent", "H1": "Variables are associated"},
            "statistic": np.nan,
            "p_value": np.nan,
            "alpha": alpha,
            "decision": "Inconclusive",
            "interpretation": "Each variable must have at least 2 categories.",
            "assumptions": "Independent observations, expected counts >=5.",
            "warnings": warnings_list + [f"Contingency shape {contingency.shape}."],
            "n": n,
            "degrees_of_freedom": np.nan,
            "contingency": contingency,
        }

    try:
        chi2, p, dof, expected = chi2_contingency(contingency)
        # check expected counts
        if (expected < 5).any():
            warnings_list.append("Some expected cell counts <5; chi-square approximation may be inaccurate. Consider Fisher's exact test for 2x2.")
        chi2 = float(chi2)
        p = float(p)
        dof = int(dof)
    except Exception as e:
        warnings_list.append(str(e))
        chi2, p, dof, expected = np.nan, np.nan, np.nan, None

    decision = _decision(p, alpha)
    if np.isnan(chi2):
        interpretation = "Chi-square could not be computed."
    elif decision == "Reject H0":
        interpretation = f"Significant association between {col1} and {col2} (chi2={chi2:.3f}, dof={dof}, p={p:.4f} < {alpha})."
    else:
        interpretation = f"No significant association (chi2={chi2:.3f}, dof={dof}, p={p:.4f} >= {alpha})."

    return {
        "test_name": "Chi-square test of independence",
        "variables": (col1, col2),
        "hypotheses": {"H0": "Variables are independent", "H1": "Variables are associated"},
        "statistic": chi2,
        "p_value": p,
        "alpha": alpha,
        "decision": decision,
        "interpretation": interpretation,
        "assumptions": "Independent observations, expected cell counts >=5 in at least 80% of cells and no cell with expected <1.",
        "warnings": warnings_list,
        "n": n,
        "degrees_of_freedom": dof,
        "contingency": contingency,
        "expected": expected,
    }
