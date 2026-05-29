"""
Yandex Wordstat API — парсер по списку фраз.
Читает input/phrases.txt (одна фраза = одна строка).
Сохраняет результат в output/results.json.
"""

import json
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

ENDPOINT = "https://searchapi.api.cloud.yandex.net/v2/wordstat/topRequests"
INPUT_FILE = Path(__file__).parent.parent / "input" / "phrases.txt"
OUTPUT_DIR = Path(__file__).parent.parent / "output"


def get_frequency(api_key: str, phrase: str) -> int | None:
    """Возвращает totalCount для фразы или None при ошибке."""
    headers = {
        "Authorization": f"Api-Key {api_key}",
        "Content-Type": "application/json",
    }
    try:
        r = requests.post(
            ENDPOINT,
            headers=headers,
            json={"phrase": phrase, "numPhrases": 1},
            timeout=15,
        )
        r.raise_for_status()
        return int(r.json().get("totalCount", 0))
    except requests.HTTPError as e:
        print(f"  [HTTP {e.response.status_code}] {phrase}")
        return None
    except requests.RequestException as e:
        print(f"  [ERROR] {phrase}: {e}")
        return None


def main():
    load_dotenv()

    api_key = os.getenv("YANDEX_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        print("Ошибка: YANDEX_API_KEY не задан в .env")
        sys.exit(1)

    if not INPUT_FILE.exists():
        print(f"Ошибка: файл не найден — {INPUT_FILE}")
        sys.exit(1)

    phrases = [
        line.strip()
        for line in INPUT_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]

    print(f"Фраз для проверки: {len(phrases)}\n")

    results = []
    for i, phrase in enumerate(phrases, 1):
        freq = get_frequency(api_key, phrase)
        status = f"{freq:>8,}" if freq is not None else "  ОШИБКА"
        print(f"  [{i:02}/{len(phrases)}] {status}  {phrase}")
        results.append({"phrase": phrase, "freq": freq})
        time.sleep(0.15)  # ~6 запросов/сек — в пределах лимита

    OUTPUT_DIR.mkdir(exist_ok=True)
    output_file = OUTPUT_DIR / "results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    found = sum(1 for r in results if r["freq"])
    zeros = sum(1 for r in results if r["freq"] == 0)
    errors = sum(1 for r in results if r["freq"] is None)

    print(f"\nГотово → {output_file}")
    print(f"С частотностью: {found}  |  Нули: {zeros}  |  Ошибки: {errors}")


if __name__ == "__main__":
    main()
