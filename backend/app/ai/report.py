"""AI-assisted report generation — Version 3.

All numeric results must come from verified engine; AI only drafts prose sections.
"""

from __future__ import annotations

from typing import Any

from app.ai.llm import generate


async def draft_report(
    title: str,
    dataset_info: dict,
    methods_used: list[str],
    verified_results: list[dict],
    charts: list[dict] | None = None,
) -> dict[str, str]:
    """Draft report sections via LLM, grounded in verified_results."""

    # Build compact verified summary for prompt (no raw data)
    summary = []
    for vr in verified_results:
        res = vr.get("result", {}) if isinstance(vr.get("result"), dict) else {}
        summary.append({
            "test_type": vr.get("test_type"),
            "statistic": res.get("statistic"),
            "p_value": res.get("p_value"),
            "decision": res.get("decision"),
            "interpretation": (res.get("interpretation") or "")[:200],
        })

    prompt = (
        f"Report title: {title}\n"
        f"Dataset info: {dataset_info}\n"
        f"Methods used: {methods_used}\n"
        f"Verified results (do NOT invent, only use these): {summary}\n"
        f"Charts: {charts or []}\n\n"
        "Draft the following sections in JSON with keys: executive_summary, methods, results, limitations, recommendations.\n"
        "Each section 2-4 sentences, plain language, cite actual numbers above, communicate uncertainty, note assumptions.\n"
        "Methods must list tests and why chosen. Limitations must mention sample size, assumptions, not generalizing beyond data.\n"
        "Do not fabricate numbers."
    )

    resp = await generate(
        prompt,
        system="You are a report writer for statistics. Draft from verified results only, never invent. Be concise and honest about uncertainty.",
    )

    # Mock will return prose; for real LLM we would parse JSON, but for mock we synthesize sections
    if resp.provider == "mock":
        # Deterministic sections for tests / free deploy
        return {
            "executive_summary": f"Executive summary for '{title}': dataset with {dataset_info.get('rows', '?')} rows was analyzed using {', '.join(methods_used) or 'descriptive'}. Key findings are based on verified Python calculations.",
            "methods": f"Methods: {', '.join(methods_used)} were applied. Each test reports statistic, p-value, decision vs alpha, with assumptions noted. Calculations via scipy.stats.",
            "results": resp.text[:600],
            "limitations": "Limitations: results depend on assumptions (normality, independence, expected counts). Small samples or violated assumptions reduce reliability. Not a substitute for expert review.",
            "recommendations": "Recommendations: validate assumptions via visualizations (histogram, QQ-plot), consider larger sample or alternative tests if assumptions violated.",
            "raw_llm": resp.text,
        }

    # Try to parse LLM JSON, fallback to raw
    try:
        import json

        parsed = json.loads(resp.text)
        if isinstance(parsed, dict):
            return {
                "executive_summary": parsed.get("executive_summary", ""),
                "methods": parsed.get("methods", ""),
                "results": parsed.get("results", ""),
                "limitations": parsed.get("limitations", ""),
                "recommendations": parsed.get("recommendations", ""),
                "raw_llm": resp.text,
            }
    except Exception:
        pass

    return {
        "executive_summary": resp.text[:400],
        "methods": f"Methods: {', '.join(methods_used)}",
        "results": resp.text,
        "limitations": "See raw LLM for limitations (mock fallback).",
        "recommendations": "Review limitations and consider follow-up analyses.",
        "raw_llm": resp.text,
    }
