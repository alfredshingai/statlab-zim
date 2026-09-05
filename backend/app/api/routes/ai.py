"""AI endpoints — Version 3.

Strict pipeline: question → interpretation → candidate selection → Python verification → AI explanation → answer.
AI never calculates; all numbers from verified engine.
Features: NL questions, suggestions, explanations, cleaning assistant, local-first.
"""

import math

import numpy as np
import pandas as pd

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.ai.service import (
    build_explanation_prompt,
    interpret_question,
    suggest_analyses,
    verify_and_calculate,
)
from app.ai.llm import generate
from app.store.memory import get_dataframe, get_dataset

router = APIRouter(prefix="/ai", tags=["ai"])


class AskRequest(BaseModel):
    dataset_id: str
    question: str = Field(..., examples=["Which product has the highest average sales?", "Is satisfaction different between age groups?"])
    alpha: float = Field(0.05, ge=0.001, le=0.5)


class SuggestRequest(BaseModel):
    dataset_id: str
    question: str | None = None
    alpha: float = 0.05


class ExplainRequest(BaseModel):
    dataset_id: str
    test_type: str
    x_col: str | None = None
    y_col: str | None = None
    numeric_col: str | None = None
    group_col: str | None = None
    col1: str | None = None
    col2: str | None = None
    alpha: float = 0.05


def _sanitize(value: Any) -> Any:
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        if np.isnan(value) or np.isinf(value):
            return None
        return float(value)
    if isinstance(value, np.ndarray):
        return [_sanitize(v) for v in value.tolist()]
    if isinstance(value, pd.DataFrame):
        return value.where(pd.notna(value), None).to_dict()
    if isinstance(value, dict):
        return {k: _sanitize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize(v) for v in value]
    if isinstance(value, tuple):
        return tuple(_sanitize(v) for v in value)
    return value


def _sanitize_result(result: dict) -> dict:
    # handle DataFrames/ndarrays inside result
    clean = {}
    for k, v in result.items():
        try:
            if isinstance(v, pd.DataFrame):
                v = v.where(pd.notna(v), None).to_dict()
            elif isinstance(v, np.ndarray):
                v = v.tolist()
        except Exception:
            pass
        clean[k] = _sanitize(v)
    return clean


def _get_df(dataset_id: str):
    rec = get_dataset(dataset_id)
    if not rec:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")
    df = get_dataframe(dataset_id)
    if df is None:
        raise HTTPException(status_code=404, detail="Dataset has no data")
    return df


@router.post("/ask", summary="Ask NL question — full pipeline")
async def ask(payload: AskRequest):
    df = _get_df(payload.dataset_id)
    interpretation = interpret_question(payload.question)
    candidates = suggest_analyses(payload.question, df, alpha=payload.alpha)

    # Verify each candidate (Python) — take first feasible for detailed answer
    verified = []
    for cand in candidates[:3]:  # limit to 3 to keep latency low
        v = verify_and_calculate(df, cand, alpha=payload.alpha)
        # sanitize for JSON
        if "result" in v and isinstance(v["result"], dict):
            v["result"] = _sanitize_result(v["result"])
        v = _sanitize(v)
        verified.append(v)

    # Pick primary verified (first verified True)
    primary = next((v for v in verified if v.get("verified")), verified[0] if verified else None)

    # Build explanation prompt only if verified result exists
    explanation = None
    llm_meta = None
    if primary and primary.get("verified"):
        prompt = build_explanation_prompt(payload.question, candidates[0] if candidates else {}, primary)
        llm_resp = await generate(
            prompt,
            system="You are StatLab AI. Explain verified stats, never invent numbers. Communicate uncertainty. Cite assumptions.",
        )
        explanation = llm_resp.text
        llm_meta = {"provider": llm_resp.provider, "model": llm_resp.model}

    return {
        "dataset_id": payload.dataset_id,
        "question": payload.question,
        "interpretation": interpretation,
        "candidates": candidates,
        "verified": verified,
        "primary_verified": primary,
        "explanation": explanation,
        "llm_meta": llm_meta,
        "pipeline": "question → interpretation → candidate selection → Python verification → AI explanation → answer",
        "provenance": "All numeric results from Python (src/stats_tests.py et al.); AI only explains.",
    }


@router.post("/suggest", summary="Suggest analyses for dataset/question")
async def suggest(payload: SuggestRequest):
    df = _get_df(payload.dataset_id)
    q = payload.question or "Suggest appropriate analyses for this dataset"
    candidates = suggest_analyses(q, df, alpha=payload.alpha)
    # Include mock LLM suggestions text for UI
    prompt = f"Suggest analyses for question: {q} with candidates {candidates}"
    llm_resp = await generate(prompt, system="Suggest analyses with reasons, do not invent numbers.")
    return {
        "dataset_id": payload.dataset_id,
        "question": q,
        "candidates": candidates,
        "ai_suggestions": llm_resp.text,
        "provider": llm_resp.provider,
    }


@router.post("/explain", summary="Explain a specific test result (verified)")
async def explain(payload: ExplainRequest):
    df = _get_df(payload.dataset_id)
    # Run verified test
    from app.services.analyses import run_test

    try:
        # Build kwargs from payload
        kwargs: dict[str, Any] = {}
        if payload.x_col:
            kwargs["x_col"] = payload.x_col
        if payload.y_col:
            kwargs["y_col"] = payload.y_col
        if payload.numeric_col:
            kwargs["numeric_col"] = payload.numeric_col
        if payload.group_col:
            kwargs["group_col"] = payload.group_col
        if payload.col1:
            kwargs["col1"] = payload.col1
        if payload.col2:
            kwargs["col2"] = payload.col2
        result = run_test(df, payload.test_type, alpha=payload.alpha, **kwargs)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    result = _sanitize_result(result)
    candidate = {"test_type": payload.test_type, "assumptions": result.get("assumptions", "")}
    verified = {"test_type": payload.test_type, "verified": True, "result": result}
    prompt = build_explanation_prompt(f"Explain this {payload.test_type} result", candidate, verified)
    llm_resp = await generate(prompt, system="Explain stats plainly, cover means/medians/p-values/effects/assumptions, communicate uncertainty.")

    return {
        "dataset_id": payload.dataset_id,
        "test_type": payload.test_type,
        "parameters": _sanitize(kwargs),
        "verified_result": result,
        "explanation": llm_resp.text,
        "provenance": "Verified via Python; AI explains only.",
        "provider": llm_resp.provider,
    }


class ReportRequest(BaseModel):
    dataset_id: str
    title: str = Field(..., examples=["Q1 Sales Report"])
    project_id: str | None = None
    methods: list[str] | None = None  # if None, auto-collect from candidates
    include_charts: bool = False


class CleaningSuggestRequest(BaseModel):
    dataset_id: str


@router.post("/cleaning-suggest", summary="Data-cleaning assistant suggestions")
async def cleaning_suggest(payload: CleaningSuggestRequest):
    df = _get_df(payload.dataset_id)
    # Rule-based cleaning suggestions (no destructive auto-apply)
    suggestions: list[dict] = []

    # Check for missing
    missing = df.isna().sum()
    for col in df.columns:
        if missing[col] > 0:
            suggestions.append({
                "column": col,
                "issue": "missing_values",
                "count": int(missing[col]),
                "suggestion": f"Column '{col}' has {missing[col]} missing. Consider imputation (mean/median/mode) or dropna. Requires user approval.",
                "destructive": False,
            })

    # Check for text numeric
    for col in df.columns:
        if df[col].dtype == "object":
            try:
                pd_numeric = pd.to_numeric(df[col].dropna(), errors="coerce")
                if pd_numeric.notna().sum() / max(len(df[col].dropna()), 1) > 0.8:
                    suggestions.append({
                        "column": col,
                        "issue": "text_to_numeric",
                        "suggestion": f"Column '{col}' looks numeric but stored as text. Convert to numeric with pd.to_numeric(errors='coerce'). Approve before transform.",
                        "destructive": True,
                    })
            except Exception:
                pass

    # High cardinality
    for col in df.columns:
        if df[col].nunique() > 50 and df[col].dtype == "object":
            suggestions.append({
                "column": col,
                "issue": "high_cardinality",
                "suggestion": f"High cardinality ({df[col].nunique()} uniques). Consider grouping rare categories.",
                "destructive": False,
            })

    # Date parsing
    for col in df.columns:
        if df[col].dtype == "object":
            try:
                parsed = pd.to_datetime(df[col].dropna().astype(str), errors="coerce")
                if parsed.notna().sum() / max(len(df[col].dropna()), 1) > 0.5:
                    suggestions.append({
                        "column": col,
                        "issue": "parse_dates",
                        "suggestion": f"Column '{col}' >50% parseable as dates. Parse with pd.to_datetime.",
                        "destructive": True,
                    })
            except Exception:
                pass

    prompt = f"Dataset cleaning suggestions: {suggestions[:3]} — summarize kindly, warn about destructive ops."
    llm_resp = await generate(prompt, system="You are a data-cleaning assistant. Suggest, don't auto-apply destructive transforms. Be concise.")

    return {
        "dataset_id": payload.dataset_id,
        "suggestions": suggestions,
        "ai_summary": llm_resp.text,
        "note": "User approval required before destructive transforms are applied.",
        "provider": llm_resp.provider,
    }


@router.post("/report", summary="Generate AI-assisted report (verified numbers)")
async def ai_report(payload: ReportRequest):
    """Draft report sections with verified results; optionally persist as Report if project_id provided."""
    df = _get_df(payload.dataset_id)
    dataset_info = {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "column_names": list(df.columns),
    }

    # Auto-pick methods via suggest if not provided
    methods = payload.methods
    if not methods:
        cands = suggest_analyses("Generate report for this dataset", df)
        methods = [c["test_type"] for c in cands[:4]]

    # Verify each method
    verified = []
    for m in methods[:4]:
        cand = {"test_type": m, "assumptions": ""}
        v = verify_and_calculate(df, cand)
        if "result" in v and isinstance(v["result"], dict):
            v["result"] = _sanitize_result(v["result"])
        v = _sanitize(v)
        verified.append(v)

    from app.ai.report import draft_report

    sections = await draft_report(
        title=payload.title,
        dataset_info=dataset_info,
        methods_used=methods,
        verified_results=verified,
        charts=[] if not payload.include_charts else [{"placeholder": "charts not yet auto-generated"}],
    )

    # Optionally persist if project_id + auth (but /ai/report is open for free tier demo; persist via /reports/generate separately)
    report_id = None
    if payload.project_id:
        # Try to persist if caller provides project_id and we can verify existence (no auth required for mock)
        from app.db.session import SessionLocal
        from app.db.models import Report, Project

        db = SessionLocal()
        try:
            proj = db.query(Project).filter(Project.id == payload.project_id).first()
            if proj:
                rep = Report(
                    title=payload.title,
                    dataset_info=dataset_info,
                    methods=methods,
                    results={"verified": verified, "sections": sections},
                    charts=[],
                    interpretation=sections.get("executive_summary"),
                    limitations=sections.get("limitations"),
                    project_id=payload.project_id,
                    owner_id=proj.owner_id,
                )
                db.add(rep)
                db.commit()
                db.refresh(rep)
                report_id = rep.id
        except Exception:
            pass
        finally:
            db.close()

    return {
        "dataset_id": payload.dataset_id,
        "title": payload.title,
        "dataset_info": dataset_info,
        "methods": methods,
        "verified": verified,
        "report": sections,
        "report_id": report_id,
        "provenance": "All numbers from Python verification; AI only drafted prose.",
        "note": "Executive summary/methods/results/limitations are AI-drafted but grounded in verified_results.",
    }
