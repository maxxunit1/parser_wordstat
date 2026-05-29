"""
Yandex Wordstat API — парсер по списку фраз.
Читает input/phrases.txt (одна фраза = одна строка).
Для каждой фразы получает ВСЕ связанные фразы с частотностями (до 2000).
Сохраняет результат в output/results.json и output/results.csv.
"""

import csv
import json
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv


ENDPOINT = "https://searchapi.api.cloud.yandex.net/v2/wordstat/topRequests"
INPUT_FILE = Path(__file__).parent.parent / "input" / "phrases.txt"
OUTPUT_DIR = Path(__file__).parent.parent / "output"


def get_related_phrases(api_key: str, phrase: str, num_phrases: int = 2000, retries: int = 3) -> dict | None:
    """Возвращает totalCount + полный список results[] для фразы. Retry при 429."""
    headers = {
        "Authorization": f"Api-Key {api_key}",
        "Content-Type": "application/json",
    }
    for attempt in range(1, retries + 1):
        try:
            r = requests.post(
                ENDPOINT,
                headers=headers,
                json={"phrase": phrase, "numPhrases": num_phrases},
                timeout=20,
            )
            if r.status_code == 429:
                wait = 60 * attempt
                print(f"  [429] Квота. Жду {wait}с (попытка {attempt}/{retries})...")
                time.sleep(wait)
                continue
            r.raise_for_status()
            data = r.json()
            return {
                "query": phrase,
                "total_count": int(data.get("totalCount", 0)),
                "results": [
                    {"phrase": item["phrase"], "count": int(item["count"])}
                    for item in data.get("results", [])
                ],
            }
        except requests.HTTPError as e:
            print(f"  [HTTP {e.response.status_code}] {phrase}")
            return None
        except requests.RequestException as e:
            print(f"  [ERROR] {phrase}: {e}")
            return None
    print(f"  [SKIP] Исчерпаны попытки: {phrase}")
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

    # Checkpoint: загружаем уже обработанные фразы
    checkpoint_file = OUTPUT_DIR / "results.json"
    OUTPUT_DIR.mkdir(exist_ok=True)
    all_results = []
    done_phrases = set()
    if checkpoint_file.exists():
        with open(checkpoint_file, encoding="utf-8") as f:
            all_results = json.load(f)
        done_phrases = {r["query"] for r in all_results}
        print(f"Checkpoint: уже обработано {len(done_phrases)} фраз, продолжаем.\n")

    remaining = [p for p in phrases if p not in done_phrases]
    print(f"Фраз для обработки: {len(remaining)} (из {len(phrases)} всего)\n")

    flat_rows = []

    for i, phrase in enumerate(remaining, 1):
        data = get_related_phrases(api_key, phrase)
        if data is None:
            print(f"  [{i:02}/{len(remaining)}]  ПРОПУСК  {phrase}")
            continue

        count = data["total_count"]
        related = data["results"]
        print(f"  [{i:02}/{len(remaining)}] {count:>8,}  {phrase}  → {len(related)} связанных фраз")

        all_results.append(data)

        # Сохраняем checkpoint после каждого запроса
        with open(checkpoint_file, "w", encoding="utf-8") as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)

        for item in related:
            flat_rows.append({
                "query": phrase,
                "phrase": item["phrase"],
                "count": item["count"],
            })

        time.sleep(0.2)

    OUTPUT_DIR.mkdir(exist_ok=True)

    # JSON — полная структура
    json_file = OUTPUT_DIR / "results.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    # CSV — плоская таблица из полного JSON (включая checkpoint)
    csv_file = OUTPUT_DIR / "results.csv"
    all_rows = [
        {"query": r["query"], "phrase": item["phrase"], "count": item["count"]}
        for r in all_results
        for item in r["results"]
    ]
    with open(csv_file, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["query", "phrase", "count"], delimiter=";")
        writer.writeheader()
        writer.writerows(all_rows)

    total_phrases = sum(len(r["results"]) for r in all_results)
    print(f"\nГотово:")
    print(f"  Запросов обработано : {len(all_results)}")
    print(f"  Связанных фраз всего: {total_phrases}")
    print(f"  JSON → {json_file}")
    print(f"  CSV  → {csv_file}")


if __name__ == "__main__":
    main()
