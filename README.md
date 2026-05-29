# parser_wordstat

Python-клиент для получения статистики запросов через **Yandex Wordstat API** (Yandex Cloud Search API v2).

---

## Что умеет

- Получать топ фраз, содержащих заданное слово (`/v2/wordstat/topRequests`)
- Показывать ассоциативные запросы
- Сохранять полный ответ API в `output/response.json`
- Выводить читаемый лог запроса и ответа в консоль

---

## Структура проекта

```
parser_wordstat/
├── src/
│   └── client.py        # тестовый клиент
├── output/              # ответы API (в .gitignore)
├── .env                 # ключи (создать из .env.example, в .gitignore)
├── .env.example         # шаблон переменных окружения
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Быстрый старт

### 1. Установить зависимости

```bash
pip install -r requirements.txt
```

### 2. Создать `.env`

```bash
cp .env.example .env
```

Вставить API Key (см. раздел «Настройка доступа»):

```env
YANDEX_API_KEY=AQVNz...ваш_ключ
```

### 3. Запустить

```bash
python src/client.py
```

---

## Настройка доступа к Wordstat API — пошаговая инструкция

> Задокументировано по результатам реального подключения. Официальная документация:
> https://aistudio.yandex.ru/docs/ru/search-api/concepts/wordstat.html

### Шаг 1. Создать аккаунт в Yandex Cloud

Зайти на [console.yandex.cloud](https://console.yandex.cloud) и войти через Яндекс ID.

### Шаг 2. Привязать платёжный аккаунт и пополнить баланс

**Это обязательный шаг.** Без активного биллинг-аккаунта Search API возвращает `403 Permission denied` даже при корректном ключе.

- Yandex Cloud Console → Биллинг → Создать платёжный аккаунт
- Привязать банковскую карту
- Пополнить баланс (достаточно минимальной суммы — API в Preview работает за копейки или бесплатно)

### Шаг 3. Создать API Key в AI Studio

1. Зайти на [aistudio.yandex.ru](https://aistudio.yandex.ru)
2. Нажать **«Создать API-ключ»** (кнопка в правом верхнем углу)
3. Задать срок действия или выбрать «Бессрочный»
4. Сохранить **секретный ключ** — он показывается только один раз

> При создании API Key система автоматически создаёт сервисный аккаунт с ролью
> `search-api.webSearch.user`. Этой роли достаточно для Wordstat API.

### Шаг 4. Вставить ключ в `.env`

```env
YANDEX_API_KEY=ваш_ключ_из_шага_3
```

**Важно:** `YANDEX_FOLDER_ID` указывать **не нужно** — он не нужен и вызывает 403.

---

## API — техническая справка

### Endpoint

```
POST https://searchapi.api.cloud.yandex.net/v2/wordstat/topRequests
```

### Заголовки

```http
Authorization: Api-Key <API_KEY>
Content-Type: application/json
```

> Тип авторизации — именно `Api-Key`, не `Bearer` (OAuth-токен не подходит).

### Тело запроса

```json
{
  "phrase": "ппр",
  "numPhrases": 50
}
```

| Параметр | Тип | Обязательный | Описание |
|---|---|---|---|
| `phrase` | string | ✅ | Ключевая фраза (макс. 400 символов) |
| `numPhrases` | int | — | Количество фраз в ответе (1–2000, по умолчанию 50) |
| `regions` | array | — | ID регионов из `/v1/getRegionsTree` |
| `devices` | array | — | `DEVICE_ALL`, `DEVICE_DESKTOP`, `DEVICE_PHONE`, `DEVICE_TABLET` |
| `folderId` | string | ❌ | **НЕ передавать** — вызывает 403. API Key уже привязан к каталогу |

### Формат ответа

```json
{
  "totalCount": "268782",
  "results": [
    { "phrase": "ппр строительство", "count": "13600" },
    { "phrase": "ппр на монтаж",     "count": "9800" }
  ],
  "associations": [
    { "phrase": "проект производства работ", "count": "45000" }
  ]
}
```

| Поле | Описание |
|---|---|
| `totalCount` | Общая частотность исходной фразы за 30 дней |
| `results[].count` | Частотность фразы, содержащей ключ |
| `associations[].count` | Частотность похожего запроса |

### Остальные методы

| Endpoint | Назначение | Квота |
|---|---|---|
| `POST /v2/wordstat/topRequests` | Топ фраз с ключом (30 дней) | 1 ед. |
| `POST /v2/wordstat/getDynamics` | Динамика по датам | 1 ед. |
| `POST /v2/wordstat/getRegionsDistribution` | Распределение по регионам | 2 ед. |

**Лимиты:** 10 запросов/сек · 1000 запросов/сутки

---

## Диагностика частых ошибок

| Ошибка | Причина | Решение |
|---|---|---|
| `403 Permission denied` | Не активирован биллинг | Пополнить баланс в Yandex Cloud |
| `403 Permission denied` | Передан `folderId` | Убрать `folderId` из тела запроса |
| `403 Permission denied` | Неверный тип авторизации | Использовать `Api-Key`, не `Bearer` |
| `401 Unauthorized` | Истёкший токен | Создать новый API Key в AI Studio |

---

## Следующие шаги (архитектура основного парсера)

```
src/
├── client.py        # HTTP-клиент (готово)
├── wordstat.py      # бизнес-логика: сбор по списку фраз, фильтрация
├── exporter.py      # экспорт в JSON / CSV
└── run.py           # точка входа

input/
└── phrases.txt      # список фраз для проверки (по одной на строку)
```

Логика: читает `input/phrases.txt` → запрашивает частотность каждой фразы →
фильтрует по минус-словам → сохраняет результат с полем `freq` в JSON.
