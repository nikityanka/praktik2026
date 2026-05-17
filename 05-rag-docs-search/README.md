# RAG Documentation Search

Система поиска по документации с использованием Retrieval-Augmented Generation (RAG). Индексирует документы, создает векторные представления и отвечает на вопросы с указанием источников.

## Возможности

- Индексирование документов (.md, .txt, .rst) в векторную БД
- Разбиение документов на чанки с перекрытием
- Создание embeddings через Google Gemini API
- Хранение векторов в локальной ChromaDB
- Семантический поиск по документации
- Генерация ответов на основе найденных документов
- Указание источников информации

## Установка

1. Клонируйте репозиторий или скопируйте файлы

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Установите переменную окружения с API ключом:
```bash
# Linux/Mac
export GEMINI_API_KEY=your_api_key_here

# Windows (PowerShell)
$env:GEMINI_API_KEY="your_api_key_here"

# Windows (CMD)
set GEMINI_API_KEY=your_api_key_here
```

## Получение API ключа

1. Перейдите на https://aistudio.google.com
2. Войдите с помощью Google аккаунта
3. Нажмите "Get API Key"
4. Создайте новый ключ и скопируйте его

## Использование

### 1. Индексирование документов

```bash
# Базовое индексирование (текущая директория)
python rag-search.py index .

# Индексирование конкретной папки
python rag-search.py index C:\Users\Nikita\Documents\my-docs

# С указанием имени коллекции
python rag-search.py index . --collection my_docs

# Настройка размера чанков
python rag-search.py index . --chunk-size 1500 --overlap 300
```

### 2. Поиск в документации

```bash
# Базовый поиск с генерацией ответа
python rag-search.py search "How to install the package?"

# Поиск с большим количеством результатов
python rag-search.py search "API reference" --top-k 10

# Только поиск без генерации ответа
python rag-search.py search "configuration options" --no-answer

# Поиск в конкретной коллекции
python rag-search.py search "deployment guide" --collection my_docs
```

## Примеры

### Индексирование документации проекта

```bash
# Структура проекта
my-project/
├── docs/
│   ├── getting-started.md
│   ├── api-reference.md
│   ├── tutorials/
│   │   ├── tutorial-1.md
│   │   └── tutorial-2.md
│   └── README.md

# Индексирование
python rag-search.py index my-project/docs

# Вывод:
# Найдено 5 документов
# [1/5] Обрабатываю getting-started.md...
#   Создано 3 чанков
#   ✓ Обработано 3 чанков
# [2/5] Обрабатываю api-reference.md...
#   Создано 8 чанков
#   ✓ Обработано 8 чанков
# ...
# ✓ Индексирование завершено: 25 чанков из 5 документов
```

### Поиск и получение ответа

```bash
python rag-search.py search "How do I authenticate users?"

# Вывод:
# Поиск: How do I authenticate users?
# Ищу релевантные документы...
# Генерирую ответ...
#
# ======================================================================
# Ответ:
# ======================================================================
# To authenticate users, you need to:
#
# 1. Import the authentication module:
#    ```python
#    from myapp import auth
#    ```
#
# 2. Create an authentication instance with your credentials:
#    ```python
#    authenticator = auth.Authenticator(api_key="your_key")
#    ```
#
# 3. Call the authenticate method with user credentials:
#    ```python
#    result = authenticator.authenticate(username, password)
#    ```
#
# The method returns a token that should be included in subsequent requests.
#
# ======================================================================
# Источники:
# ======================================================================
# - api-reference.md
# - getting-started.md
```

### Поиск без генерации ответа

```bash
python rag-search.py search "configuration" --no-answer --top-k 3

# Вывод:
# ======================================================================
# Найдено 3 релевантных чанков:
# ======================================================================
#
# 1. Источник: getting-started.md (чанк 2)
#    Configuration can be done through environment variables or a config file.
#    The following options are available: API_KEY, DATABASE_URL, LOG_LEVEL...
#
# 2. Источник: api-reference.md (чанк 5)
#    The Configuration class provides methods to load and validate settings.
#    Use Configuration.load() to read from the default config file...
#
# 3. Источник: tutorials/tutorial-1.md (чанк 1)
#    In this tutorial, we'll configure the application step by step.
#    First, create a .env file in the project root...
```

## Команды

### index

Индексирует документы в векторную БД.

```
python rag-search.py index <path> [options]

Аргументы:
  path                  Путь к папке с документами (обязательный)

Опции:
  --collection, -c      Имя коллекции (по умолчанию: docs)
  --chunk-size          Размер чанка в символах (по умолчанию: 1000)
  --overlap             Размер перекрытия между чанками (по умолчанию: 200)
```

### search

Ищет информацию в проиндексированных документах.

```
python rag-search.py search <query> [options]

Аргументы:
  query                 Поисковый запрос (обязательный)

Опции:
  --collection, -c      Имя коллекции (по умолчанию: docs)
  --top-k, -k           Количество релевантных чанков (по умолчанию: 5)
  --no-answer           Только показать найденные чанки без генерации ответа
```

## Технические детали

### Чанкинг

- **Размер чанка**: 1000 символов (настраивается)
- **Перекрытие**: 200 символов (настраивается)
- **Стратегия**: Разбиение по границам предложений для сохранения контекста

### Embeddings

- **Модель**: Google Gemini embedding-001
- **Размерность**: 768
- **Тип задачи**: retrieval_document для индексирования, retrieval_query для поиска

### Векторная БД

- **База данных**: ChromaDB (локальная)
- **Расположение**: `~/.rag-docs-search/chroma_db`
- **Метрика**: Косинусная близость
- **Персистентность**: Данные сохраняются между запусками

### Генерация ответов

- **Модель**: Google Gemini 2.5 Flash
- **Контекст**: Топ-K релевантных чанков
- **Язык**: Автоматическое определение языка запроса

## Поддерживаемые форматы

- `.md` - Markdown
- `.txt` - Текстовые файлы
- `.rst` - reStructuredText

## Как это работает

1. **Индексирование**:
   - Рекурсивно сканирует директорию
   - Читает содержимое документов
   - Разбивает на чанки с перекрытием
   - Создает embeddings для каждого чанка
   - Сохраняет в ChromaDB с метаданными

2. **Поиск**:
   - Создает embedding для запроса
   - Ищет наиболее похожие чанки в БД
   - Возвращает топ-K результатов

3. **Генерация ответа**:
   - Формирует контекст из найденных чанков
   - Отправляет запрос и контекст в LLM
   - Получает ответ с указанием источников

## Рекомендации

### Размер чанков

- **500-800 символов**: Для коротких документов и FAQ
- **1000-1500 символов**: Оптимально для большинства случаев
- **2000+ символов**: Для технической документации с длинными разделами

### Перекрытие

- **100-150 символов**: Минимальное перекрытие
- **200-300 символов**: Рекомендуется для сохранения контекста
- **400+ символов**: Для документов со сложными связями

### Количество результатов (top-k)

- **3-5**: Быстрые ответы на конкретные вопросы
- **5-10**: Сбалансированный вариант
- **10-20**: Для комплексных вопросов, требующих широкого контекста

## Ограничения

- Google AI Studio (Gemini): ~1500 запросов/день
- Embeddings API: ограничение на длину текста (10000 символов)
- ChromaDB: хранится локально, требует место на диске
- Поддерживаются только текстовые форматы (PDF требует дополнительной обработки)

## Устранение неполадок

### "Коллекция не найдена"
Сначала проиндексируйте документы командой `index`.

### "GEMINI_API_KEY не установлен"
Убедитесь, что переменная окружения установлена корректно.

### Медленная индексация
Уменьшите количество чанков, увеличив `--chunk-size`.

### Нерелевантные результаты
- Увеличьте `--top-k` для получения большего контекста
- Уменьшите размер чанков для более точного поиска
- Переформулируйте запрос более конкретно

## Лицензия

MIT
