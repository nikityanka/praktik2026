# 10 учебных проектов с ИИ через API

Коллекция из 10 практических проектов, использующих LLM API. Каждый проект можно выполнить за 1-3 дня и добавить в портфолио.

## Обзор проектов

### 1. Telegram-бот для саммаризации статей
**Директория:** `01-telegram-summarizer-bot/`

Telegram-бот, который принимает ссылку на статью и возвращает краткое содержание в 5 пунктах.

**Технологии:** Python, python-telegram-bot, BeautifulSoup, readability, Google Gemini API

**Ключевые возможности:**
- Извлечение текста из веб-страниц
- Обработка длинных статей с чанкингом
- Обработка ошибок (битые ссылки, пейволы)

---

### 2. CLI-инструмент для генерации commit-сообщений
**Директория:** `02-git-commit-ai/`

CLI-утилита для автоматической генерации commit-сообщений в формате Conventional Commits на основе `git diff --staged`.

**Технологии:** Python, Google Gemini API, Git

**Ключевые возможности:**
- Анализ git diff
- Генерация сообщений в формате Conventional Commits
- Флаги для указания типа и scope
- Режим dry-run

---

### 3. Ассистент для заметок в Obsidian/markdown-папке
**Директория:** `03-markdown-notes-assistant/`

Инструмент для анализа связей между markdown-заметками с использованием embeddings.

**Технологии:** Python, Google Gemini Embeddings API, scikit-learn, PyYAML

**Ключевые возможности:**
- Поиск смысловых связей между заметками
- Генерация summary для каждой заметки
- Вычисление косинусной близости
- Безопасная работа с файлами

---

### 4. Генератор unit-тестов по коду
**Директория:** `04-test-generator/`

Автоматический генератор unit-тестов для Python и JavaScript функций.

**Технологии:** Python, AST, Google Gemini API

**Ключевые возможности:**
- Извлечение функций с помощью AST
- Генерация тестов для pytest и Jest
- Покрытие happy path, edge cases, error handling
- Валидация синтаксиса

---

### 5. RAG-поиск по документации
**Директория:** `05-rag-docs-search/`

Система поиска по документации с использованием Retrieval-Augmented Generation.

**Технологии:** Python, Google Gemini API, ChromaDB, scikit-learn

**Ключевые возможности:**
- Индексирование документов в векторную БД
- Чанкинг с перекрытием
- Семантический поиск
- Генерация ответов с указанием источников

---

### 6. Переводчик markdown-файлов
**Директория:** `06-markdown-translator/`

Переводчик markdown-файлов с сохранением форматирования.

**Технологии:** Python, Google Gemini API, markdown

**Ключевые возможности:**
- Перевод на 10+ языков
- Сохранение markdown разметки
- Не переводит код, ссылки, HTML
- Рекурсивная обработка директорий

---

### 7. Анализатор скриншотов багов
**Директория:** `07-bug-screenshot-analyzer/`

Анализатор скриншотов ошибок с использованием vision-модели.

**Технологии:** Python, Google Gemini Vision API, Flask, python-telegram-bot

**Ключевые возможности:**
- Анализ скриншотов ошибок
- Классификация типа ошибки
- Предложение решений
- CLI и Telegram-бот интерфейсы

---

### 8. Voice-to-task
**Директория:** `08-voice-to-task/`

Конвертер голосовых заметок в структурированные задачи.

**Технологии:** Python, Google Gemini API (audio transcription)

**Ключевые возможности:**
- Транскрипция аудио
- Извлечение структуры задачи
- Определение приоритета и дедлайна
- Генерация action items

---

### 9. AI-модерация комментариев
**Директория:** `09-ai-comment-moderator/`

REST API сервис для автоматической модерации комментариев.

**Технологии:** Python, Flask, SQLite, Google Gemini API

**Ключевые возможности:**
- Классификация: ok/spam/toxic/needs_review
- Логирование решений в БД
- Статистика модерации
- REST API endpoints

---

### 10. Подбор GitHub-issues под стек разработчика
**Директория:** `10-github-issue-matcher/`

Анализирует GitHub-профиль и подбирает релевантные issues с good-first-issue.

**Технологии:** Python, GitHub API, Google Gemini API

**Ключевые возможности:**
- Анализ технологического стека
- Поиск подходящих issues
- Интеллектуальное ранжирование
- Обоснование релевантности

---

## Общие требования

### Зависимости

Все проекты используют Python 3.8+ и требуют:
- Google Gemini API ключ (бесплатно на https://aistudio.google.com)
- Дополнительные зависимости указаны в `requirements.txt` каждого проекта

### Установка

Для каждого проекта:

```bash
cd project-directory/
pip install -r requirements.txt
```

### API ключи

Получите бесплатный API ключ:
1. Перейдите на https://aistudio.google.com
2. Войдите с Google аккаунтом
3. Нажмите "Get API Key"
4. Установите переменную окружения:

```bash
# Linux/Mac
export GEMINI_API_KEY=your_api_key_here

# Windows (PowerShell)
$env:GEMINI_API_KEY="your_api_key_here"
```

## Структура проектов

```
pp/
├── 01-telegram-summarizer-bot/
│   ├── bot.py
│   ├── requirements.txt
│   ├── README.md
│   └── .gitignore
├── 02-git-commit-ai/
│   ├── git-commit-ai.py
│   ├── requirements.txt
│   ├── README.md
│   └── .gitignore
├── 03-markdown-notes-assistant/
│   ├── notes-assistant.py
│   ├── requirements.txt
│   ├── README.md
│   └── .gitignore
├── 04-test-generator/
│   ├── test-generator.py
│   ├── requirements.txt
│   ├── README.md
│   └── .gitignore
├── 05-rag-docs-search/
│   ├── rag-search.py
│   ├── requirements.txt
│   ├── README.md
│   └── .gitignore
├── 06-markdown-translator/
│   ├── md-translate.py
│   ├── requirements.txt
│   ├── README.md
│   └── .gitignore
├── 07-bug-screenshot-analyzer/
│   ├── analyze-bug.py
│   ├── telegram-bot.py
│   ├── requirements.txt
│   ├── README.md
│   └── .gitignore
├── 08-voice-to-task/
│   ├── voice-to-task.py
│   ├── requirements.txt
│   ├── README.md
│   └── .gitignore
├── 09-ai-comment-moderator/
│   ├── moderator.py
│   ├── requirements.txt
│   ├── README.md
│   └── .gitignore
├── 10-github-issue-matcher/
│   ├── issue_matcher.py
│   ├── requirements.txt
│   ├── README.md
│   └── .gitignore
├── ai-api-projects.pdf (файл с заданиями)
└── README.md (этот файл)
```

## Бесплатные API-сервисы

### Google AI Studio (Gemini) - рекомендуется
- **Модели:** Gemini 2.5 Flash и другие
- **Лимиты:** ~1500 запросов/день
- **Контекст:** 1M токенов
- **Поддержка:** Vision, Audio
- **Сайт:** https://aistudio.google.com

### Альтернативы

- **Groq:** Быстрый инференс, 14400 запросов/день
- **OpenRouter:** Множество моделей, 200 запросов/день
- **GitHub Models:** 45+ моделей для прототипирования
- **Hugging Face:** Тысячи open-source моделей

## Рекомендации

### Для начинающих

Начните с этих проектов:
1. **CLI-инструмент для commit-сообщений** - простой и практичный
2. **Telegram-бот для саммаризации** - знакомство с ботами
3. **Генератор unit-тестов** - полезен для разработки

### Для продвинутых

Попробуйте эти проекты:
1. **RAG-поиск по документации** - классический паттерн RAG
2. **AI-модерация комментариев** - production-подобная задача
3. **GitHub-issue matcher** - интеграция нескольких API

### Советы

1. **Начните с одного проекта** - не пытайтесь сделать все сразу
2. **Используйте .env файлы** - никогда не коммитьте API ключи
3. **Кэшируйте ответы** - экономьте лимиты при разработке
4. **Читайте README** - в каждом проекте есть подробная документация
5. **Экспериментируйте** - модифицируйте проекты под свои нужды

## Что вы освоите

### Технические навыки

- Работа с REST API
- Промпт-инжиниринг
- Обработка естественного языка
- Векторные представления (embeddings)
- Работа с базами данных
- Парсинг и обработка данных
- CLI и веб-разработка

### Паттерны разработки с ИИ

- **RAG** (Retrieval-Augmented Generation)
- **Structured Output** (JSON mode)
- **Vision Models** (анализ изображений)
- **Audio Transcription** (распознавание речи)
- **Classification** (классификация текста)
- **Ranking** (ранжирование результатов)

## Развертывание

### Локально

Все проекты работают локально без дополнительной настройки.

### Docker

Пример Dockerfile для любого проекта:

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV GEMINI_API_KEY=""
CMD ["python", "main.py"]
```

### Cloud

Проекты можно развернуть на:
- **Heroku** - для веб-сервисов
- **Railway** - для ботов и API
- **Vercel** - для serverless функций
- **AWS Lambda** - для event-driven приложений

## Ограничения

- **Google AI Studio:** ~1500 запросов/день
- **GitHub API:** 60 запросов/час без токена, 5000 с токеном
- **Размер контекста:** Зависит от модели (обычно 32K-1M токенов)
- **Скорость:** 1-5 секунд на запрос в зависимости от сложности

## Лицензия

MIT - все проекты можно свободно использовать, модифицировать и распространять.

