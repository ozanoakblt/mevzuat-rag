from pathlib import Path

p1 = Path("src/common/groq_client.py")
s1 = p1.read_text(encoding="utf-8")

old1 = """        data = resp.json()
        return data["choices"][0]["message"]["content"]"""
new1 = """        data = resp.json()
        choice = data["choices"][0]
        return choice["message"]["content"], choice.get("finish_reason")"""
assert old1 in s1, "groq_client.py: _request donus satiri bulunamadi"
s1 = s1.replace(old1, new1)

old2 = """    content = _request(
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
    )"""
new2 = """    content, _finish_reason = _request(
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
    )"""
assert old2 in s1, "groq_client.py: chat_completion_json govde bulunamadi"
s1 = s1.replace(old2, new2)

old3 = """    reasoning_effort: str | None = None,
) -> str:
    \"\"\"Serbest metin üretimi için (Faz 8: cevap üretme). Ham metin döner.\"\"\"
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
    )"""
new3 = """    reasoning_effort: str | None = None,
    return_finish_reason: bool = False,
):
    \"\"\"Serbest metin üretimi için (Faz 8: cevap üretme). Ham metin döner.
    return_finish_reason=True ise (icerik, finish_reason) tuple'i doner -
    finish_reason == "length" cevabin max_tokens'a carpip kesildigini,
    yani alinti bolumune hic ulasamamis olabilecegini gosterir.
    \"\"\"
    content, finish_reason = _request(
        system_prompt,
        user_prompt,
        model,
        temperature,
        timeout,
        max_retries,
        max_tokens=max_tokens,
        json_mode=False,
        reasoning_effort=reasoning_effort,
    )
    if return_finish_reason:
        return content, finish_reason
    return content"""
assert old3 in s1, "groq_client.py: chat_completion_text govde bulunamadi"
s1 = s1.replace(old3, new3)
p1.write_text(s1, encoding="utf-8")

p2 = Path("src/generation/answer_generator.py")
s2 = p2.read_text(encoding="utf-8")

old4 = """def generate_answer(
    query: str,
    chunks: list[dict],
    doc_titles: dict[str, str] | None = None,
    model: str | None = None,
    max_tokens: int = 3200,
) -> str:"""
new4 = """def generate_answer(
    query: str,
    chunks: list[dict],
    doc_titles: dict[str, str] | None = None,
    model: str | None = None,
    max_tokens: int = 3200,
    return_finish_reason: bool = False,
):"""
assert old4 in s2, "answer_generator.py: fonksiyon imzasi bulunamadi"
s2 = s2.replace(old4, new4)

old5 = """    if not chunks:
        return (
            "Verilen kaynaklarda bu soruyla ilgili hiçbir pasaj bulunamadı. "
            "Lütfen sorunuzu farklı bir şekilde ifade etmeyi deneyin ya da "
            "resmî EPDK/mevzuat.gov.tr kaynaklarını doğrudan kontrol edin."
        )

    context = _format_context(chunks, doc_titles)
    user_prompt = f"KAYNAK PASAJLAR:\\n\\n{context}\\n\\nSORU: {query}"

    return chat_completion_text(SYSTEM_PROMPT, user_prompt, model=model, max_tokens=max_tokens, temperature=0.0, reasoning_effort="low")"""
new5 = """    if not chunks:
        text = (
            "Verilen kaynaklarda bu soruyla ilgili hiçbir pasaj bulunamadı. "
            "Lütfen sorunuzu farklı bir şekilde ifade etmeyi deneyin ya da "
            "resmî EPDK/mevzuat.gov.tr kaynaklarını doğrudan kontrol edin."
        )
        return (text, "no_chunks") if return_finish_reason else text

    context = _format_context(chunks, doc_titles)
    user_prompt = f"KAYNAK PASAJLAR:\\n\\n{context}\\n\\nSORU: {query}"

    return chat_completion_text(
        SYSTEM_PROMPT, user_prompt, model=model, max_tokens=max_tokens,
        temperature=0.0, reasoning_effort="low", return_finish_reason=return_finish_reason,
    )"""
assert old5 in s2, "answer_generator.py: govde bulunamadi"
s2 = s2.replace(old5, new5)
p2.write_text(s2, encoding="utf-8")

p3 = Path("scripts/run_eval.py")
s3 = p3.read_text(encoding="utf-8")

old6 = """    if with_generation:
        answer = generate_answer(q_text, reranked, doc_titles=DOC_TITLES)
        guard = run_guard(answer, reranked)
        result["guard_low_confidence"] = guard.is_low_confidence
        result["ungrounded_citation_count"] = sum(
            1 for c in guard.citation_checks if not c.grounded
        )
        result["total_citation_count"] = len(guard.citation_checks)"""
new6 = """    if with_generation:
        answer, finish_reason = generate_answer(
            q_text, reranked, doc_titles=DOC_TITLES, return_finish_reason=True
        )
        guard = run_guard(answer, reranked)
        result["guard_low_confidence"] = guard.is_low_confidence
        result["ungrounded_citation_count"] = sum(
            1 for c in guard.citation_checks if not c.grounded
        )
        result["total_citation_count"] = len(guard.citation_checks)
        result["finish_reason"] = finish_reason
        result["answer_text"] = answer"""
assert old6 in s3, "run_eval.py: with_generation blogu bulunamadi"
s3 = s3.replace(old6, new6)
p3.write_text(s3, encoding="utf-8")

print("Tamamlandi: finish_reason ve answer_text artik results.json'a kaydediliyor.")
