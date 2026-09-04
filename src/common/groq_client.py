"""
Groq Chat Completions API için ince bir istemci.

Ücretsiz kaynak kısıtı (brief madde 2) gereği Groq'un ücretsiz kademesi
kullanılıyor. API key .env'den (GROQ_API_KEY) okunur.
"""
from __future__ import annotations

import json
import os
import re
import time

import requests

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-oss-20b"


class GroqError(Exception):
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
    reasoning_effort: str | None,
) -> str:
    """Ortak istek mantığı; ham metin (content) döner. Rate limit (429)
    durumunda Groq'un döndürdüğü bekleme süresini bekleyip tekrar dener."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise GroqError(
            "GROQ_API_KEY tanımlı değil. .env dosyasına ekleyin "
            "(https://console.groq.com/keys adresinden ücretsiz alınabilir)."
        )

    model = model or os.environ.get("GROQ_MODEL", DEFAULT_MODEL)

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_completion_tokens": max_tokens,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    if "gpt-oss" in model and reasoning_effort:
        payload["reasoning_effort"] = reasoning_effort

    for attempt in range(max_retries + 1):
        resp = requests.post(
            GROQ_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=timeout,
        )
        if resp.status_code == 429:
            wait_s = _parse_retry_wait_seconds(resp.text) or 5.0
            if attempt < max_retries:
                time.sleep(wait_s + 0.5)
                continue
        if resp.status_code != 200:
            raise GroqError(f"Groq API hatası ({resp.status_code}): {resp.text[:500]}")

        data = resp.json()
        return data["choices"][0]["message"]["content"]

    raise GroqError("Groq rate limit: birden fazla denemeden sonra başarısız oldu.")


def chat_completion_json(
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
    temperature: float = 0.0,
    timeout: float = 30.0,
    max_retries: int = 4,
) -> dict:
    """Kapalı-uçlu sınıflandırma gibi görevler için — yanıtın JSON olmasını
    ister, parse edip dict döner."""
    content = _request(
        system_prompt,
        user_prompt,
        model,
        temperature,
        timeout,
        max_retries,
        max_tokens=350,
        json_mode=True,
        # gpt-oss gibi "reasoning" modelleri kısa sınıflandırma görevinde
        # gereksiz yere uzun düşünüp token/hız limitini tüketebilir.
        reasoning_effort="low",
    )
    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise GroqError(f"Groq yanıtı geçerli JSON değil: {content[:300]}") from exc


def chat_completion_text(
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
    temperature: float = 0.1,
    timeout: float = 60.0,
    max_retries: int = 4,
    max_tokens: int = 1000,
    reasoning_effort: str | None = None,
) -> str:
    """Serbest metin üretimi için (Faz 8: cevap üretme). Ham metin döner."""
    return _request(
        system_prompt,
        user_prompt,
        model,
        temperature,
        timeout,
        max_retries,
        max_tokens=max_tokens,
        json_mode=False,
        # Cevap üretimi daha fazla akıl yürütme gerektirebilir; "low" yerine
        # varsayılanı (None -> API'nin kendi varsayılanı) kullanıyoruz.
        reasoning_effort=reasoning_effort,
    )


def _parse_retry_wait_seconds(error_text: str) -> float | None:
    match = re.search(r"try again in ([\d.]+)s", error_text)
    if match:
        return float(match.group(1))
    return None
