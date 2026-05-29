"""
Тестовый клиент Yandex Wordstat API (Yandex Cloud Search API).
Endpoint: POST https://searchapi.api.cloud.yandex.net/v2/wordstat/topRequests
Auth:     Authorization: Api-Key <API_KEY>

Важно: folderId НЕ передаём — API Key уже привязан к каталогу неявно.
Передача folderId вызывает 403 Permission denied.
"""

import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

# Фикс кодировки консоли на Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

ENDPOINT = "https://searchapi.api.cloud.yandex.net/v2/wordstat/topRequests"
OUTPUT_DIR = Path(__file__).parent.parent / "output"


def get_top_requests(api_key: str, phrase: str, num_phrases: int = 50) -> dict:
    headers = {
        "Authorization": f"Api-Key {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "phrase": phrase,
        "numPhrases": num_phrases,
    }

    print("=" * 60)
    print("ЗАПРОС")
    print("=" * 60)
    print(f"Endpoint : {ENDPOINT}")
    print(f"Method   : POST")
    print("Headers  :")
    for k, v in headers.items():
        if k == "Authorization":
            print(f"  {k}: {v[:15]}***{v[-4:]}")
        else:
            print(f"  {k}: {v}")
    print(f"Body     : {json.dumps(body, ensure_ascii=False)}")
    print()

    response = requests.post(ENDPOINT, headers=headers, json=body, timeout=30)

    print("=" * 60)
    print("ОТВЕТ")
    print("=" * 60)
    print(f"Status   : {response.status_code} {response.reason}")
    print("Headers  :")
    for k, v in response.headers.items():
        print(f"  {k}: {v}")
    print()

    response.raise_for_status()
    return response.json()


def main():
    load_dotenv()

    api_key = os.getenv("YANDEX_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        print("Ошибка: YANDEX_API_KEY не задан в .env")
        sys.exit(1)

    phrase = "ппр"
    print(f"Фраза: «{phrase}»\n")

    try:
        data = get_top_requests(api_key, phrase, num_phrases=50)
    except requests.HTTPError as e:
        print(f"HTTP-ошибка: {e.response.status_code}")
        print(f"Тело: {e.response.text}")
        sys.exit(1)
    except requests.RequestException as e:
        print(f"Ошибка соединения: {e}")
        sys.exit(1)

    OUTPUT_DIR.mkdir(exist_ok=True)
    output_file = OUTPUT_DIR / "response.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Полный ответ сохранён: {output_file}\n")

    results = data.get("results", [])
    associations = data.get("associations", [])
    total = data.get("totalCount")

    print(f"Общая частотность «{phrase}»: {int(total):,}" if total else "")
    print(f"Результатов: {len(results)}  |  Ассоциаций: {len(associations)}\n")

    print("--- Топ-10 results (фразы содержащие ключ) ---")
    for i, item in enumerate(results[:10], 1):
        print(f"  {i:2}. {int(item.get('count', 0)):>8,}  {item.get('phrase')}")

    if associations:
        print("\n--- Топ-5 associations (похожие запросы) ---")
        for i, item in enumerate(associations[:5], 1):
            print(f"  {i:2}. {int(item.get('count', 0)):>8,}  {item.get('phrase')}")


if __name__ == "__main__":
    main()
