"""
Gemini (Google AI Studio) icin ince bir istemci.

groq_client.py ile ayni arayuzu (chat_completion_text / chat_completion_json)
sunar - llm_router.py, Groq gunluk kotasi (TPD) tukendiginde otomatik olarak
buraya duser.

ONEMLI: Google 2026'da API key formatini "AIza..." (Standard key) yerine
"AQ.Ab..." (Auth key) olarak degistirdi; AI Studio artik sadece bu yeni
formati veriyor. Yeni format, OpenAI-uyumlu endpoint'i (Authorization:
Bearer basligi) desteklemiyor - 401 ACCESS_TOKEN_TYPE_UNSUPPORTED donuyor.
Bu yuzden burada Gemini'nin NATIVE endpoint'i kullaniliyor (x-goog-api-key
basligi ile), her iki key formati da bu yolla calisiyor.

API key .env'den (GEMINI_API_KEY) okunur - kart eklenmediyse ucretsiz
kademede kalinir, kota asimi sadece 429 doner, ucretlendirme olmaz.
"""
from __future__ import annotations

import json
import os
import time

import requests
from requests.exceptions import ConnectionError, Timeout

from .usage_logger import log_usage

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
DEFAULT_MODEL = "gemini-3.5-flash-lite"

_FINISH_REASON_MAP = {
    "STOP": "stop",
    "MAX_TOKENS": "length",
    "SAFETY": "content_filter",
    "RECITATION": "content_filter",
}


class GeminiError(Exception):
    pass


def _request(
    system_prompt: str,
    user_prompt: str,
    model: str | None,
    temperature: float,
    timeout: float,
    max_retries: int,
    max_tokens: int,
    json_mode: bool,
) -> tuple[str, str | None]:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise GeminiError(
            "GEMINI_API_KEY tanimli degil. .env dosyasina ekleyin "
            "(https://aistudio.google.com/apikey adresinden ucretsiz alinabilir)."
        )

    model = model or os.environ.get("GEMINI_MODEL", DEFAULT_MODEL)
    url = f"{GEMINI_API_BASE}/{model}:generateContent"

    generation_config: dict = {
        "temperature": temperature,
        "maxOutputTokens": max_tokens,
    }
    if json_mode:
        generation_config["responseMimeType"] = "application/json"

    payload = {
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "generationConfig": generation_config,
    }

    last_error_text = ""
    for attempt in range(max_retries + 1):
        try:
            resp = requests.post(
                url,
                headers={
                    "x-goog-api-key": api_key,
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=timeout,
            )
        except (Timeout, ConnectionError) as network_exc:
            last_error_text = str(network_exc)
            if attempt < max_retries:
                time.sleep(5.0 + attempt * 3.0)
                continue
            raise GeminiError(f"Gemini baglanti hatasi: {last_error_text}") from network_exc

        if resp.status_code in (429, 503):
            # 429 = kota/rate-limit, 503 = "yuksek talep, gecici" sunucu
            # hatasi - ikisi de gecici, tekrar denemeye deger.
            last_error_text = resp.text[:500]
            if attempt < max_retries:
                time.sleep(5.0 + attempt * 3.0)
                continue
            raise GeminiError(f"Gemini API hatasi ({resp.status_code}): {last_error_text}")
        if resp.status_code != 200:
            raise GeminiError(f"Gemini API hatasi ({resp.status_code}): {resp.text[:500]}")

        data = resp.json()
        usage = data.get("usageMetadata") or {}
        log_usage(
            "gemini", model,
            usage.get("promptTokenCount"), usage.get("candidatesTokenCount"), usage.get("totalTokenCount"),
        )
        candidate = data["candidates"][0]
        parts = candidate.get("content", {}).get("parts", [])
        content = "".join(p.get("text", "") for p in parts)
        raw_finish_reason = candidate.get("finishReason")
        finish_reason = _FINISH_REASON_MAP.get(raw_finish_reason, raw_finish_reason)
        return content, finish_reason

    raise GeminiError(f"Gemini rate limit: birden fazla denemeden sonra basarisiz oldu. {last_error_text}")


def chat_completion_json(
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
    temperature: float = 0.0,
    timeout: float = 30.0,
    max_retries: int = 4,
) -> dict:
    content, _finish_reason = _request(
        system_prompt, user_prompt, model, temperature, timeout, max_retries,
        max_tokens=350, json_mode=True,
    )
    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise GeminiError(f"Gemini yaniti gecerli JSON degil: {content[:300]}") from exc


def chat_completion_text(
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
    temperature: float = 0.1,
    timeout: float = 60.0,
    max_retries: int = 4,
    max_tokens: int = 1000,
    return_finish_reason: bool = False,
):
    content, finish_reason = _request(
        system_prompt, user_prompt, model, temperature, timeout, max_retries,
        max_tokens=max_tokens, json_mode=False,
    )
    if return_finish_reason:
        return content, finish_reason
    return content
