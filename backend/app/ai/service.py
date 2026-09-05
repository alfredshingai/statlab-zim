"""Version 3 AI service — candidate selection + verified calculation + explanation.

Architecture (strict):
User question
  → Question interpretation
  → Candidate analysis selection (with reasons)
  → Python validation and calculation (verified engine)
  → Verified statistical result
  → AI explanation (linked to actual result)
  → User-facing answer

AI never directly calculates; all numbers come from src/stats_tests.py et al.
"""

from __future__ import annotations

import re
from typing import Any

import pandas as pd

from app.services.analyses import run_test, run_descriptive
from app.services.datasets import profile_dataframe


# Keyword → candidate mapping (rule-based, testable without LLM)
_KEYWORDS = {
    "pearson": ["correlation", "linear correlation", "pearson", "relate", "relationship", "related to revenue"],
    "spearman": ["spearman", "rank", "monotonic", "ordinal"],
    "linear_regression": ["regression", "predict", "slope", "trend", "explain variation"],
    "ttest": ["different between groups", "compare means", "t-test", "average difference", "is satisfaction different"],
    "chi2": ["association", "chi-square", "categorical association", "related categories", "independence"],
    "descriptive": ["highest average", "mean", "median", "describe", "missing data", "which columns"],
    "anova": ["anova", "more than two groups", "compare groups"],
}


def interpret_question(question: str) -> dict:
    """Lightweight interpretation: lowercased, extracted keywords, inferred intent."""
    q = question.strip()
    lower = q.lower()
    detected = []
    for test, kws in _KEYWORDS.items():
        if any(kw in lower for kw in kws):
            detected.append(test)
    # Fallback: if question asks about numeric relationship, suggest pearson/spearman
    if not detected and any(w in lower for w in ["highest", "average", "mean"]):
        detected.append("descriptive")
    intent = "analysis" if detected else "general"
    return {"original": q, "lower": lower, "detected_keywords": detected, "intent": intent}


def suggest_analyses(
    question: str,
    df: pd.DataFrame,
    alpha: float = 0.05,
) -> list[dict]:
    """Rule-based candidate selection with reasons, respecting column types."""
    interpretation = interpret_question(question)
    # profile to know column types
    try:
        prof = profile_dataframe(df)
        col_types = {c["column"]: c["inferred_type"] for c in prof["column_types"]}
        numeric_cols = [c for c, t in col_types.items() if t == "numeric"]
        categorical_cols = [c for c, t in col_types.items() if t == "categorical"]
    except Exception:
        numeric_cols = []
        categorical_cols = []
        col_types = {}

    candidates: list[dict] = []

    def add(test_type: str, reason: str, required: str, assumptions: str):
        candidates.append({
            "test_type": test_type,
            "reason": reason,
            "required_columns": required,
            "assumptions": assumptions,
            "feasible": _feasible(test_type, numeric_cols, categorical_cols),
        })

    q_lower = interpretation["lower"]

    # Descriptive always feasible if asking about highest average etc.
    if "descriptive" in interpretation["detected_keywords"] or any(k in q_lower for k in ["highest average", "mean", "missing"]):
        add(
            "descriptive",
            "Question asks for summaries (means, missing, highest). Descriptive provides count/mean/median/std etc.",
            "any numeric/cat",
            "No major assumptions; handle missing via dropna.",
        )

    if any(k in q_lower for k in _KEYWORDS["pearson"]):
        add(
            "pearson",
            "Question asks about linear relationship between 2 numeric variables. Pearson tests H0: r=0.",
            "2 numeric columns",
            "Bivariate normality, linearity, no extreme outliers.",
        )
    if any(k in q_lower for k in _KEYWORDS["spearman"]):
        add(
            "spearman",
            "Monotonic/ordinal relationship; Spearman is rank-based robust to outliers.",
            "2 numeric/ordinal",
            "Monotonic relationship, ordinal or continuous.",
        )
    if any(k in q_lower for k in _KEYWORDS["linear_regression"]):
        add(
            "linear_regression",
            "Predictor → outcome linear model; tests slope !=0.",
            "X numeric → Y numeric",
            "Linearity, independence, homoscedasticity, normality of residuals.",
        )
    if any(k in q_lower for k in _KEYWORDS["ttest"]):
        add(
            "ttest",
            "Compare means across 2 groups (e.g., satisfaction between age groups). Welch t-test.",
            "1 numeric + 1 categorical (2 groups)",
            "Independent observations, normality within groups, Welch robust to unequal variance.",
        )
    if any(k in q_lower for k in _KEYWORDS["chi2"]):
        add(
            "chi2",
            "Association between 2 categorical variables.",
            "2 categorical",
            "Independent observations, expected cell counts ≥5 (warning if violated).",
        )

    # If no keywords matched but we have numeric cols, suggest exploratory
    if not candidates:
        if len(numeric_cols) >= 2:
            add("pearson", "Exploratory: dataset has ≥2 numeric columns; Pearson is common first check.", "2 numeric", "Bivariate normality, linearity.")
        if len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
            add("ttest", "Exploratory: 1 numeric + 1 categorical (if 2 groups) → t-test.", "1 numeric + 1 cat (2 groups)", "Normality per group.")
        add("descriptive", "Exploratory descriptive summary for all variables.", "any", "None.")

    return candidates


def _feasible(test_type: str, numeric_cols: list[str], categorical_cols: list[str]) -> bool:
    if test_type in ("pearson", "spearman", "linear_regression"):
        return len(numeric_cols) >= 2
    if test_type == "ttest":
        return len(numeric_cols) >= 1 and len(categorical_cols) >= 1
    if test_type == "chi2":
        return len(categorical_cols) >= 2
    if test_type == "descriptive":
        return True
    if test_type == "anova":
        return len(numeric_cols) >= 1 and len(categorical_cols) >= 1
    return False


def verify_and_calculate(
    df: pd.DataFrame,
    candidate: dict,
    alpha: float = 0.05,
) -> dict:
    """Run verified Python calculation for a candidate; never use LLM numbers."""
    test_type = candidate["test_type"]
    # For descriptive, run descriptive engine
    if test_type == "descriptive":
        result = run_descriptive(df)
        return {
            "test_type": "descriptive",
            "verified": True,
            "engine": "python (src/descriptive.py)",
            "result": result,
            "warnings": [],
        }
    # For others, need columns — pick first feasible pair
    try:
        prof = profile_dataframe(df)
        col_types = {c["column"]: c["inferred_type"] for c in prof["column_types"]}
        numeric = [c for c, t in col_types.items() if t == "numeric"]
        categorical = [c for c, t in col_types.items() if t == "categorical"]
    except Exception:
        numeric = []
        categorical = []

    # Auto-pick columns for verification (deterministic)
    kwargs: dict[str, Any] = {}
    try:
        if test_type in ("pearson", "spearman", "linear_regression"):
            if len(numeric) < 2:
                raise ValueError("Need 2 numeric columns")
            kwargs = {"x_col": numeric[0], "y_col": numeric[1]}
        elif test_type == "ttest":
            if not numeric or not categorical:
                raise ValueError("Need 1 numeric + 1 categorical")
            kwargs = {"numeric_col": numeric[0], "group_col": categorical[0]}
        elif test_type == "chi2":
            if len(categorical) < 2:
                raise ValueError("Need 2 categorical")
            kwargs = {"col1": categorical[0], "col2": categorical[1]}
        else:
            raise ValueError(f"Unsupported {test_type}")

        raw = run_test(df, test_type, alpha=alpha, **kwargs)
        # Sanitize for JSON (NaN → None handled by service layer)
        return {
            "test_type": test_type,
            "verified": True,
            "engine": f"python (src/stats_tests.py:{test_type})",
            "parameters": kwargs,
            "result": raw,
            "warnings": raw.get("warnings", []),
        }
    except Exception as e:
        return {
            "test_type": test_type,
            "verified": False,
            "engine": "python",
            "parameters": kwargs,
            "error": str(e),
            "warnings": [str(e)],
        }


def build_explanation_prompt(
    question: str,
    candidate: dict,
    verified: dict,
) -> str:
    """Prompt that forces LLM to explain verified result, not invent."""
    result = verified.get("result", {})
    # Summarize verified result for LLM context (no raw data dump for privacy)
    summary = {
        "test_type": verified.get("test_type"),
        "statistic": result.get("statistic") if isinstance(result, dict) else None,
        "p_value": result.get("p_value") if isinstance(result, dict) else None,
        "decision": result.get("decision") if isinstance(result, dict) else None,
        "interpretation": result.get("interpretation") if isinstance(result, dict) else None,
        "assumptions": result.get("assumptions") if isinstance(result, dict) else candidate.get("assumptions"),
    }
    return (
        f"User question: {question}\n\n"
        f"Candidate analysis: {candidate}\n\n"
        f"Verified Python result (DO NOT invent new numbers, only explain this):\n"
        f"{summary}\n\n"
        f"Task: Explain in plain language what this result means, including:\n"
        f"- What the test does and H0/H1\n"
        f"- What statistic and p-value indicate (vs alpha)\n"
        f"- Practical significance vs statistical significance\n"
        f"- Assumptions and limitations\n"
        f"- Do not fabricate calculations. Link explanation to the actual numbers above. Communicate uncertainty clearly."
    )
