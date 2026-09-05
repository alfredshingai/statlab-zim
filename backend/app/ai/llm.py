"""LLM abstraction — mock (deterministic), openai, ollama.

Version 3 principle: AI never directly calculates; it only explains verified Python results.
Mock provider is used for tests and free deployment (no API key needed).
"""

from __future__ import annotations

import json
from typing import Any

from app.core.config import get_settings


class LLMResponse:
    def __init__(self, text: str, provider: str, model: str, raw: Any = None):
        self.text = text
        self.provider = provider
        self.model = model
        self.raw = raw


async def generate(
    prompt: str,
    system: str = "You are a helpful statistics assistant. Never invent numbers; only explain provided results.",
    max_tokens: int | None = None,
) -> LLMResponse:
    settings = get_settings()
    provider = settings.AI_PROVIDER.lower()
    if provider == "mock":
        return _mock_generate(prompt, system, settings)
    elif provider == "openai":
        return await _openai_generate(prompt, system, settings, max_tokens)
    elif provider == "ollama":
        return await _ollama_generate(prompt, system, settings, max_tokens)
    else:
        # fallback to mock for unknown
        return _mock_generate(prompt, system, settings)


def _mock_generate(prompt: str, system: str, settings) -> LLMResponse:
    """Deterministic mock — explains without fabricating calculations."""
    # Extract verified result if present in prompt (wrapped as JSON)
    # We produce a structured explanation template, not a hallucinated p-value.
    lower = prompt.lower()
    if "explain" in lower or "interpret" in lower:
        text = (
            "This is a mock AI explanation (no external API call). "
            "The verified statistical result (computed by Python) is shown above. "
            "Interpretation: check p-value vs alpha; if p < alpha, reject H0 and report effect size with caution about assumptions (normality, independence, sample size). "
            "Limitations: mock does not replace expert review; verify assumptions via visualizations."
        )
    elif "suggest" in lower:
        text = (
            "Mock suggestions: based on column types and question keywords, consider: "
            "Pearson if 2 numeric & linear, Spearman if monotonic/ordinal, t-test if numeric+2-group categorical, "
            "chi-square if 2 categorical, ANOVA if numeric+>2 groups, regression if predictor→outcome. "
            "Each suggestion includes reason and required assumptions."
        )
    elif "question" in lower or "ask" in lower:
        text = (
            "Mock answer: I have identified candidate analyses, run verified Python calculations, and will explain results linked to actual statistics. "
            "No numbers were invented; all numeric results come from the verified engine."
        )
    else:
        text = "Mock response — no external LLM called. Provide verified result context for detailed explanation."

    # Append truncated prompt for traceability (privacy: no raw data echoed)
    preview = prompt[:300].replace("\n", " ")
    text += f"\n\n[Mock context preview: {preview}...]"

    return LLMResponse(text=text, provider="mock", model="mock", raw={"prompt_preview": preview})


async def _openai_generate(prompt: str, system: str, settings, max_tokens: int | None) -> LLMResponse:
    try:
        from openai import AsyncOpenAI
    except ImportError:
        return _mock_generate(prompt, system, settings)

    if not settings.OPENAI_API_KEY:
        return LLMResponse(
            text="OpenAI key missing — falling back to mock explanation. Set OPENAI_API_KEY to enable.",
            provider="mock",
            model="mock",
        )
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    try:
        resp = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            max_tokens=max_tokens or settings.AI_MAX_TOKENS,
            temperature=0.2,
        )
        text = resp.choices[0].message.content or ""
        return LLMResponse(text=text, provider="openai", model=settings.OPENAI_MODEL, raw=resp)
    except Exception as e:
        return LLMResponse(text=f"OpenAI error, fallback mock: {e}", provider="mock", model="mock")


async def _ollama_generate(prompt: str, system: str, settings, max_tokens: int | None) -> LLMResponse:
    import httpx

    try:
        async with httpx.AsyncClient(timeout=30) as http:
            payload = {
                "model": settings.OLLAMA_MODEL,
                "prompt": f"System: {system}\n\nUser: {prompt}",
                "stream": False,
                "options": {"num_predict": max_tokens or settings.AI_MAX_TOKENS},
            }
            r = await http.post(f"{settings.OLLAMA_HOST}/api/generate", json=payload)
            r.raise_for_status()
            data = r.json()
            text = data.get("response", "")
            return LLMResponse(text=text, provider="ollama", model=settings.OLLAMA_MODEL, raw=data)
    except Exception as e:
        return LLMResponse(text=f"Ollama unavailable, fallback mock: {e}", provider="mock", model="mock")
