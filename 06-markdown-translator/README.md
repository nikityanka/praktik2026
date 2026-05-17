# Markdown Translator

Переводчик markdown-файлов с сохранением форматирования. Переводит только текст, не трогая код, ссылки, HTML-теги и frontmatter.

## Возможности

- Перевод markdown-файлов на 10+ языков
- Сохранение всей markdown разметки
- Не переводит код в блоках и инлайн
- Не переводит URL и пути к файлам
- Не переводит HTML теги
- Сохраняет frontmatter без изменений
- Переводит alt-текст в изображениях
- Переводит текст ссылок, сохраняя URL
- Рекурсивная обработка директорий
- Автоматическое определение исходного языка

## Установка

1. Клонируйте репозиторий или скопируйте файлы

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Создайте файл `.env` на основе `.env.example`:
```bash
# Linux/Mac
cp .env.example .env

# Windows (PowerShell)
Copy-Item .env.example .env

# Windows (CMD)
copy .env.example .env
```

4. Откройте `.env` и добавьте ваш API ключ:
```
GEMINI_API_KEY=your_api_key_here
```

Альтернативно, можно установить переменную окружения:
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

### Базовое использование

```bash
# Перевести файл на русский
python md-translate.py README.md --target ru

# Перевести на испанский с указанием исходного языка
python md-translate.py docs/guide.md --target es --source en

# Указать выходной файл
python md-translate.py README.md --target fr --output README.fr.md
```

### Обработка директорий

```bash
# Перевести все .md файлы в директории
python md-translate.py docs/ --target de

# Рекурсивно обработать все поддиректории
python md-translate.py docs/ --target ru --recursive
```

### Дополнительные опции

```bash
# Перезаписать существующие файлы без подтверждения
python md-translate.py README.md --target ru --overwrite

# Сокращенные формы флагов
python md-translate.py README.md -t ru -s en -o README.ru.md
```

## Поддерживаемые языки

| Код | Язык |
|-----|------|
| en  | English |
| ru  | Russian |
| es  | Spanish |
| fr  | French |
| de  | German |
| it  | Italian |
| pt  | Portuguese |
| zh  | Chinese |
| ja  | Japanese |
| ko  | Korean |

## Примеры

### Исходный файл (README.md)

```markdown
---
title: My Project
author: John Doe
---

# Getting Started

This is a **simple** guide to get you started.

## Installation

Run the following command:

```bash
npm install my-package
```

## Usage

Here's how to use it:

```javascript
const pkg = require('my-package');
pkg.init();
```

For more info, see the [documentation](https://example.com/docs).

![Logo](./logo.png)
```

### Команда

```bash
python md-translate.py README.md --target ru
```

### Результат (README.ru.md)

```markdown
---
title: My Project
author: John Doe
---

# Начало работы

Это **простое** руководство для начала работы.

## Установка

Выполните следующую команду:

```bash
npm install my-package
```

## Использование

Вот как это использовать:

```javascript
const pkg = require('my-package');
pkg.init();
```

Для получения дополнительной информации см. [документацию](https://example.com/docs).

![Логотип](./logo.png)
```

### Что сохранилось

- ✓ Frontmatter не изменен
- ✓ Заголовки (# ##) сохранены
- ✓ Жирный текст (**) сохранен
- ✓ Код блоки не переведены
- ✓ URL в ссылке сохранен
- ✓ Путь к изображению сохранен
- ✓ Alt-текст изображения переведен
- ✓ Текст ссылки переведен

## Флаги командной строки

```
input                 Путь к markdown файлу или директории (обязательный)
--target, -t          Целевой язык перевода (обязательный)
--source, -s          Исходный язык (опционально)
--output, -o          Путь для сохранения перевода
--recursive, -r       Рекурсивно обрабатывать все .md файлы
--overwrite           Перезаписать существующие файлы без подтверждения
--help, -h            Показать справку
```

## Технические детали

### Парсинг markdown

Инструмент использует регулярные выражения для идентификации:
- Код блоков (` ``` ... ``` `)
- Инлайн кода (`` `code` ``)
- HTML тегов (`<tag>`)
- Изображений (`![alt](url)`)
- Ссылок (`[text](url)`)

### Стратегия перевода

1. **Извлечение frontmatter**: Сохраняется без изменений
2. **Парсинг структуры**: Разделение на переводимые и непереводимые узлы
3. **Перевод узлов**: Каждый переводимый узел обрабатывается отдельно
4. **Сборка результата**: Объединение переведенных и оригинальных частей

### Что переводится

- ✓ Обычный текст
- ✓ Заголовки
- ✓ Текст в списках
- ✓ Текст в таблицах
- ✓ Текст ссылок
- ✓ Alt-текст изображений
- ✓ Цитаты

### Что НЕ переводится

- ✗ Frontmatter (YAML между `---`)
- ✗ Код блоки (` ``` ... ``` `)
- ✗ Инлайн код (`` `code` ``)
- ✗ HTML теги
- ✗ URL и пути к файлам
- ✗ Markdown символы (`*`, `_`, `#`, и т.д.)

## Формат выходных файлов

По умолчанию, переведенные файлы сохраняются с языковым суффиксом:

```
README.md          → README.ru.md
guide.md           → guide.es.md
docs/tutorial.md   → docs/tutorial.fr.md
```

Можно указать собственный путь с помощью `--output`.

## Рекомендации

### Для лучших результатов

1. **Используйте правильную markdown разметку**: Инструмент полагается на корректный синтаксис
2. **Указывайте исходный язык**: Это улучшает качество перевода
3. **Проверяйте результаты**: LLM может иногда ошибаться
4. **Делайте резервные копии**: Особенно при использовании `--overwrite`

### Обработка больших файлов

Для файлов с большим количеством текста:
- Перевод может занять несколько минут
- Файл разбивается на части для перевода
- Прогресс отображается в консоли

### Обработка специальных случаев

**Таблицы**: Переводятся корректно, структура сохраняется
```markdown
| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |
```

**Списки**: Переводятся с сохранением маркеров
```markdown
- Item 1
- Item 2
  - Nested item
```

**Цитаты**: Переводятся с сохранением `>`
```markdown
> This is a quote
```

## Ограничения

- Google AI Studio (Gemini): ~1500 запросов/день
- Сложные вложенные структуры могут требовать ручной проверки
- Технические термины могут переводиться некорректно
- Смешанный контент (код + текст в одной строке) может обрабатываться неточно

## Устранение неполадок

### Неправильный перевод кода

Если код переводится, проверьте:
- Код должен быть в блоках ` ``` ` или инлайн `` `code` ``
- Нет пробелов перед/после обратных кавычек

### Сломанная разметка

Если разметка нарушена:
- Проверьте исходный файл на корректность
- Убедитесь, что все блоки кода закрыты
- Проверьте парные символы (`*`, `_`, `[`, `]`)

### Медленная обработка

Для ускорения:
- Обрабатывайте файлы по одному
- Разбейте большие файлы на части
- Используйте более быстрый API провайдер (Groq)

## Интеграция в CI/CD

Пример GitHub Actions для автоматического перевода:

```yaml
name: Translate Docs

on:
  push:
    paths:
      - 'docs/**/*.md'

jobs:
  translate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Translate to Russian
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: python md-translate.py docs/ -t ru -r --overwrite
      - name: Commit translations
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add docs/**/*.ru.md
          git commit -m "Update Russian translations" || exit 0
          git push
```

## Лицензия

MIT
