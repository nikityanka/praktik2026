# 10 учебных проектов с LLM-API

Коллекция из 10 практических проектов, использующих LLM API в рамках преддипломной практики.

## Проекты

### 1. Telegram-бот для саммаризации статей
**Директория:** `01-telegram-summarizer-bot/`

Принимает ссылку на статью и возвращает краткое содержание в 5 пунктах.

**Технологии:** Python, aiogram, Trafilatura, Google Gemini API

**Файлы:**
- `bot.py` — основной код бота
- `requirements.txt` — зависимости

**Запуск:**
```bash
cd 01-telegram-summarizer-bot
pip install -r requirements.txt
python bot.py
```

---

### 2. CLI-инструмент для генерации commit-сообщений
**Директория:** `02-git-commit-ai/`

CLI-утилита для автоматической генерации commit-сообщений в формате Conventional Commits.

**Технологии:** Python, Google Gemini API, Git

**Файлы:**
- `git-commit-ai.py` — основной код
- `requirements.txt` — зависимости

**Использование:**
```bash
python git-commit-ai.py --dry-run
python git-commit-ai.py --type feat --scope auth
python git-commit-ai.py
```

---

### 3. Ассистент для заметок в Obsidian
**Директория:** `03-markdown-notes-assistant/`

Анализирует связи между markdown-заметками с использованием embeddings.

**Технологии:** Python, Google Gemini Embeddings API, scikit-learn

**Файлы:**
- `notes-assistant.py` — основной код
- `requirements.txt` — зависимости

**Запуск:**
```bash
cd 03-markdown-notes-assistant
python notes-assistant.py
```

---

### 4. Генератор unit-тестов по коду
**Директория:** `04-test-generator/`

Автоматический генератор unit-тестов для Python и JavaScript функций.

**Технологии:** Python, AST, Google Gemini API

**Файлы:**
- `test-generator.py` — основной код
- `calculator.py` — пример функции
- `requirements.txt` — зависимости

**Запуск:**
```bash
cd 04-test-generator
python test-generator.py <файл>
```

---

### 5. RAG-поиск по документации
**Директория:** `05-rag-docs-search/`

Система поиска по документации с использованием Retrieval-Augmented Generation.

**Технологии:** Python, Google Gemini API, ChromaDB, scikit-learn

**Файлы:**
- `rag-search.py` — основной код
- `requirements.txt` — зависимости
- `test_docs/` — тестовые документы

**Запуск:**
```bash
cd 05-rag-docs-search
python rag-search.py --index test_docs/
python rag-search.py --query "ваш вопрос"
```

---

### 6. Переводчик markdown-файлов
**Директория:** `06-markdown-translator/`

Переводчик markdown-файлов с сохранением форматирования.

**Технологии:** Python, Google Gemini API, Mistune

**Файлы:**
- `md-translate.py` — основной код
- `requirements.txt` — зависимости

**Использование:**
```bash
python md-translate.py --lang en input.md
python md-translate.py --lang de --output output.md input.md
```

---

### 7. Анализатор скриншотов багов
**Директория:** `07-bug-screenshot-analyzer/`

Анализатор скриншотов ошибок с использованием vision-модели.

**Технологии:** Python, Google Gemini Vision API, aiogram

**Файлы:**
- `analyze-bug.py` — основной код
- `telegram-bot.py` — Telegram-бот
- `requirements.txt` — зависимости

**Запуск:**
```bash
cd 07-bug-screenshot-analyzer
python analyze-bug.py screenshot.png
python telegram-bot.py
```

---

### 8. Преобразование голосовых заметок в задачи
**Директория:** `08-voice-to-task/`

Конвертер голосовых заметок в структурированные задачи.

**Технологии:** Python, Google Gemini API, Whisper API

**Файлы:**
- `voice-to-task.py` — основной код
- `requirements.txt` — зависимости
- `voice.mp3` — пример

**Запуск:**
```bash
cd 08-voice-to-task
python voice-to-task.py voice.mp3
```

---

### 9. AI-модерация комментариев
**Директория:** `09-ai-comment-moderator/`

REST API сервис для модерации комментариев.

**Технологии:** Python, FastAPI, SQLite, Google Gemini API

**Файлы:**
- `moderator.py` — основной код
- `test_moderator.py` — тесты
- `requirements.txt` — зависимости

**Запуск:**
```bash
cd 09-ai-comment-moderator
uvicorn moderator:app --reload
```

**Endpoints:**
- `POST /moderate` — модерация комментария
- `GET /stats` — статистика
- `GET /logs` — история

---

### 10. Подбор GitHub-issues под стек разработчика
**Директория:** `10-github-issue-matcher/`

Анализирует GitHub-профиль и подбирает релевантные issues с good-first-issue.

**Технологии:** Python, GitHub API, Google Gemini API

**Файлы:**
- `issue_matcher.py` — основной код
- `test_issue_matcher.py` — тесты
- `requirements.txt` — зависимости

**Запуск:**
```bash
cd 10-github-issue-matcher
python issue_matcher.py <username>
```

---

## Установка

Для каждого проекта:
```bash
cd <директория>
pip install -r requirements.txt
```

## API ключи

Создайте `.env` файл:
```
GEMINI_API_KEY=your_key_here
```

Ключ: https://aistudio.google.com/app/apikey

## Структура

```
pp/
├── 01-telegram-summarizer-bot/
├── 02-git-commit-ai/
├── 03-markdown-notes-assistant/
├── 04-test-generator/
├── 05-rag-docs-search/
├── 06-markdown-translator/
├── 07-bug-screenshot-analyzer/
├── 08-voice-to-task/
├── 09-ai-comment-moderator/
├── 10-github-issue-matcher/
└── README.md
```

## Лицензия

MIT