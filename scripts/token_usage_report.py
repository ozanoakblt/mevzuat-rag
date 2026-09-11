"""
Token kullanim raporu: data/token_usage.jsonl'daki kayitlari ozetler.
"""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path(__file__).resolve().parent.parent / "data" / "token_usage.jsonl"


def main() -> None:
    if not LOG_PATH.exists():
        print("Henuz kayit yok:", LOG_PATH)
        return

    tokens_by_day_provider: dict[tuple[str, str], int] = defaultdict(int)
    calls_by_day_provider: dict[tuple[str, str], int] = defaultdict(int)

    with LOG_PATH.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            timestamp = entry.get("timestamp", "")
            day = timestamp[:10] if timestamp else "bilinmiyor"
            provider = entry.get("provider", "bilinmiyor")
            total = entry.get("total_tokens") or 0
            tokens_by_day_provider[(day, provider)] += total
            calls_by_day_provider[(day, provider)] += 1

    today = datetime.now(timezone.utc).date().isoformat()

    print(f"=== Bugun ({today}, UTC) ===")
    today_rows = [
        (provider, total, calls_by_day_provider[(day, provider)])
        for (day, provider), total in tokens_by_day_provider.items()
        if day == today
    ]
    if not today_rows:
        print("  (henuz kayit yok)")
    for provider, total, calls in sorted(today_rows):
        print(f"  {provider:10s}: {total:>8} token, {calls} cagri")

    print("\n=== Tum gunler ===")
    for (day, provider), total in sorted(tokens_by_day_provider.items()):
        calls = calls_by_day_provider[(day, provider)]
        print(f"  {day}  {provider:10s}: {total:>8} token, {calls} cagri")


if __name__ == "__main__":
    main()
