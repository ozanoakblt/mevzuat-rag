"""
Groq -> Gemini fallback yonlendiricisi.

answer_generator.py ve query_expansion.py, dogrudan groq_client'i degil bu
modulu cagirir. Groq basarisiz olursa (kota, 429, key eksik vb.) otomatik
olarak Gemini'ye duser - hangisinin cevapladigini gizlemeden, her dususte
konsola bir UYARI yazar (sessiz fallback yok, run_eval.py ciktisinda goze
carpsin diye).

Ikisi de basarisiz olursa LLMError firlatilir.
"""
from __future__ import annotations

from . import gemini_client, groq_client


class LLMError(Exception):
    """Hem Groq hem Gemini basarisiz oldugunda firlatilir."""


def chat_completion_text(
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
    temperature: float = 0.1,
    timeout: float = 60.0,
    max_retries: int = 4,
    max_tokens: int = 1000,
    reasoning_effort: str | None = None,
    return_finish_reason: bool = False,
):
    try:
        return groq_client.chat_completion_text(
            system_prompt, user_prompt, model=model, temperature=temperature,
            timeout=timeout, max_retries=max_retries, max_tokens=max_tokens,
            reasoning_effort=reasoning_effort, return_finish_reason=return_finish_reason,
        )
    except groq_client.GroqError as groq_err:
        print(f"UYARI: Groq basarisiz oldu ({groq_err}) - Gemini'ye dusuluyor...")
        try:
            return gemini_client.chat_completion_text(
                system_prompt, user_prompt, temperature=temperature,
                timeout=timeout, max_retries=max_retries, max_tokens=max_tokens,
                return_finish_reason=return_finish_reason,
            )
        except gemini_client.GeminiError as gemini_err:
            raise LLMError(
                f"Hem Groq hem Gemini basarisiz oldu. Groq: {groq_err} | Gemini: {gemini_err}"
            ) from gemini_err


def chat_completion_json(
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
    temperature: float = 0.0,
    timeout: float = 30.0,
    max_retries: int = 4,
) -> dict:
    try:
        return groq_client.chat_completion_json(
            system_prompt, user_prompt, model=model, temperature=temperature,
            timeout=timeout, max_retries=max_retries,
        )
    except groq_client.GroqError as groq_err:
        print(f"UYARI: Groq basarisiz oldu ({groq_err}) - Gemini'ye dusuluyor...")
        try:
            return gemini_client.chat_completion_json(
                system_prompt, user_prompt, temperature=temperature,
                timeout=timeout, max_retries=max_retries,
            )
        except gemini_client.GeminiError as gemini_err:
            raise LLMError(
                f"Hem Groq hem Gemini basarisiz oldu. Groq: {groq_err} | Gemini: {gemini_err}"
            ) from gemini_err
