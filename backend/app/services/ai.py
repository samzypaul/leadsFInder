"""AI provider abstraction.

`generate_text` / `generate_json` route to Gemini or OpenAI when a key is configured, and to
a deterministic template fallback otherwise — so every higher-level feature (summaries,
proposals, outreach) works with or without API keys. Higher-level modules pass a
`fallback` callable that produces a sensible result without a model.
"""
from __future__ import annotations

import json
import logging
from collections.abc import Callable

from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings

log = logging.getLogger("leadhunter.ai")


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8), reraise=True)
def _gemini(prompt: str, *, json_mode: bool) -> str:
    import google.generativeai as genai

    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(settings.gemini_model)
    cfg = {"response_mime_type": "application/json"} if json_mode else None
    resp = model.generate_content(prompt, generation_config=cfg)
    return resp.text


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8), reraise=True)
def _openai(prompt: str, *, json_mode: bool) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    kwargs = {"response_format": {"type": "json_object"}} if json_mode else {}
    resp = client.chat.completions.create(
        model=settings.openai_model,
        messages=[{"role": "user", "content": prompt}],
        **kwargs,
    )
    return resp.choices[0].message.content or ""


def _call_model(prompt: str, *, json_mode: bool) -> str | None:
    provider = settings.ai_provider
    try:
        if provider == "gemini" and settings.gemini_api_key:
            return _gemini(prompt, json_mode=json_mode)
        if provider == "openai" and settings.openai_api_key:
            return _openai(prompt, json_mode=json_mode)
    except Exception as exc:  # noqa: BLE001
        log.warning("AI call failed (%s); using fallback: %s", provider, exc)
    return None


def generate_text(prompt: str, fallback: Callable[[], str]) -> tuple[str, bool]:
    """Return (text, ai_generated)."""
    out = _call_model(prompt, json_mode=False)
    if out:
        return out.strip(), True
    return fallback(), False


def generate_json(prompt: str, fallback: Callable[[], dict]) -> tuple[dict, bool]:
    """Return (parsed_json, ai_generated). Falls back on parse failure."""
    out = _call_model(prompt, json_mode=True)
    if out:
        try:
            return json.loads(out), True
        except json.JSONDecodeError:
            # Try to salvage a JSON object embedded in prose.
            start, end = out.find("{"), out.rfind("}")
            if start != -1 and end > start:
                try:
                    return json.loads(out[start : end + 1]), True
                except json.JSONDecodeError:
                    pass
            log.warning("AI returned non-JSON; using fallback")
    return fallback(), False
