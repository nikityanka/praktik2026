# GitHub Issue Matcher

Анализирует GitHub-профиль разработчика, определяет его технологический стек и подбирает релевантные issues с лейблом `good-first-issue`. Использует LLM для интеллектуального ранжирования.

## Возможности

- Анализ GitHub-профиля и репозиториев
- Автоматическое определение технологического стека
- Поиск issues с лейблом `good-first-issue`
- Интеллектуальное ранжирование по релевантности
- Обоснование релевантности каждого issue
- Экспорт в text, markdown, JSON
- Кэширование для экономии API запросов

## Установка

1. Клонируйте репозиторий или скопируйте файлы

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Установите переменные окружения:
```bash
# Обязательно
export GEMINI_API_KEY=your_gemini_api_key_here

# Опционально (для увеличения rate limit GitHub API)
export GITHUB_TOKEN=your_github_token_here

# Windows (PowerShell)
$env:GEMINI_API_KEY="your_gemini_api_key_here"
$env:GITHUB_TOKEN="your_github_token_here"
```

## Получение API ключей

### Gemini API Key
1. Перейдите на https://aistudio.google.com
2. Войдите с помощью Google аккаунта
3. Нажмите "Get API Key"
4. Создайте новый ключ и скопируйте его

### GitHub Token (опционально)
1. Перейдите на https://github.com/settings/tokens
2. Нажмите "Generate new token (classic)"
3. Выберите scope: `public_repo`
4. Создайте токен и скопируйте его

## Использование

### Базовое использование

```bash
# Найти issues для пользователя
python issue_matcher.py torvalds

# Топ-5 issues
python issue_matcher.py torvalds --top 5

# Топ-20 issues
python issue_matcher.py torvalds --top 20
```

### Форматы вывода

```bash
# Markdown формат
python issue_matcher.py torvalds --format markdown

# JSON формат
python issue_matcher.py torvalds --format json

# Сохранить в файл
python issue_matcher.py torvalds --format markdown --output issues.md
```

## Примеры

### Пример 1: Базовый поиск

**Команда:**
```bash
python issue_matcher.py torvalds
```

**Вывод:**
```
Анализирую профиль @torvalds...
✓ Найдено 25 репозиториев
✓ Определен стек:
  Языки: C, Shell, Makefile, Python, Assembly
  Технологии: linux, kernel, operating-system

Ищу подходящие issues...
✓ Найдено 47 issues с good-first-issue

Ранжирую issues по релевантности...
✓ Ранжирование завершено

======================================================================
РЕКОМЕНДОВАННЫЕ GITHUB ISSUES
======================================================================

1. Fix memory leak in driver subsystem
   Репозиторий: https://github.com/torvalds/linux
   Issue: https://github.com/torvalds/linux/issues/12345
   Labels: good-first-issue, C, kernel
   Релевантность: 9/10
   Обоснование: Отлично подходит - работа с C и ядром Linux

2. Add documentation for new syscall
   Репозиторий: https://github.com/torvalds/linux
   Issue: https://github.com/torvalds/linux/issues/12346
   Labels: good-first-issue, documentation
   Релевантность: 8/10
   Обоснование: Документирование системных вызовов, требует знания архитектуры

...

======================================================================
```

### Пример 2: Markdown формат

**Команда:**
```bash
python issue_matcher.py octocat --format markdown --output issues.md --top 5
```

**Результат (issues.md):**
```markdown
# Рекомендованные GitHub Issues

## 1. Add dark mode support to dashboard

**Репозиторий:** [https://github.com/octocat/Hello-World](https://github.com/octocat/Hello-World)

**Issue:** https://github.com/octocat/Hello-World/issues/123

**Labels:** `good-first-issue`, `enhancement`, `css`

**Релевантность:** 9/10

**Обоснование:** Отличное совпадение со стеком - работа с CSS и JavaScript, улучшение UI

---

## 2. Fix typo in README

**Репозиторий:** [https://github.com/octocat/Spoon-Knife](https://github.com/octocat/Spoon-Knife)

**Issue:** https://github.com/octocat/Spoon-Knife/issues/456

**Labels:** `good-first-issue`, `documentation`

**Релевантность:** 7/10

**Обоснование:** Простая задача для начала, работа с документацией

---

...
```

### Пример 3: JSON формат

**Команда:**
```bash
python issue_matcher.py torvalds --format json --top 3
```

**Результат:**
```json
[
  {
    "title": "Add dark mode support to dashboard",
    "url": "https://github.com/octocat/Hello-World/issues/123",
    "repository": "https://github.com/octocat/Hello-World",
    "labels": ["good-first-issue", "enhancement", "css"],
    "relevance_score": 9,
    "relevance_reason": "Отличное совпадение со стеком - работа с CSS и JavaScript"
  },
  {
    "title": "Fix typo in README",
    "url": "https://github.com/octocat/Spoon-Knife/issues/456",
    "repository": "https://github.com/octocat/Spoon-Knife",
    "labels": ["good-first-issue", "documentation"],
    "relevance_score": 7,
    "relevance_reason": "Простая задача для начала, работа с документацией"
  },
  {
    "title": "Refactor authentication module",
    "url": "https://github.com/octocat/git-consortium/issues/789",
    "repository": "https://github.com/octocat/git-consortium",
    "labels": ["good-first-issue", "refactoring", "javascript"],
    "relevance_score": 8,
    "relevance_reason": "Рефакторинг JavaScript кода, соответствует опыту"
  }
]
```

## Как это работает

1. **Анализ профиля**: Получает список репозиториев пользователя через GitHub API
2. **Определение стека**: Анализирует языки программирования и топики репозиториев
3. **Поиск issues**: Ищет открытые issues с лейблом `good-first-issue` в проектах с похожим стеком
4. **Ранжирование**: Использует LLM для оценки релевантности каждого issue
5. **Вывод результатов**: Показывает топ-N наиболее подходящих issues с обоснованием

## Критерии ранжирования

LLM оценивает релевантность на основе:

- **Совпадение языков программирования** (9-10 баллов)
- **Совпадение технологий и фреймворков** (7-9 баллов)
- **Сложность задачи** (подходит для уровня разработчика)
- **Тип задачи** (bug fix, feature, documentation)
- **Активность проекта** (последние обновления)

## Флаги командной строки

```
username              GitHub username (обязательный)
--top, -t             Количество issues в результате (по умолчанию: 10)
--format, -f          Формат вывода: text, markdown, json
--output, -o          Сохранить результат в файл
--help, -h            Показать справку
```

## Технические детали

- **GitHub API**: REST API v3
- **Rate Limits**: 
  - Без токена: 60 запросов/час
  - С токеном: 5000 запросов/час
- **LLM**: Google Gemini 2.5 Flash
- **Анализируемые репозитории**: До 100 последних обновленных

## Ограничения

- GitHub API rate limits (используйте GITHUB_TOKEN для увеличения)
- Google AI Studio (Gemini): ~1500 запросов/день
- Анализируются только публичные репозитории
- Максимум 100 репозиториев на пользователя
- Ранжируются топ-20 найденных issues

## Рекомендации

### Для лучших результатов

1. **Активный профиль**: Больше репозиториев = точнее определение стека
2. **Используйте топики**: Добавляйте топики к своим репозиториям
3. **GitHub Token**: Используйте токен для избежания rate limits
4. **Регулярное использование**: Новые issues появляются постоянно

### Интерпретация оценок

- **9-10 баллов**: Отличное совпадение, рекомендуется начать с этих
- **7-8 баллов**: Хорошее совпадение, подходит для расширения опыта
- **5-6 баллов**: Среднее совпадение, может потребовать изучения новых технологий
- **1-4 балла**: Слабое совпадение, не рекомендуется для начала

## Интеграция

### Еженедельная рассылка

```bash
#!/bin/bash
# weekly-issues.sh

GITHUB_USERNAME="torvalds"
EMAIL="your@email.com"

# Получаем issues
python issue_matcher.py $GITHUB_USERNAME --format markdown --output issues.md --top 5

# Отправляем email
mail -s "Рекомендованные GitHub Issues" $EMAIL < issues.md
```

### Telegram-бот

```python
import subprocess
from telegram import Update
from telegram.ext import Application, CommandHandler

async def find_issues(update: Update, context):
    username = context.args[0] if context.args else update.effective_user.username
    
    # Запускаем скрипт
    result = subprocess.run(
        ['python', 'issue_matcher.py', username, '--format', 'markdown', '--top', '5'],
        capture_output=True,
        text=True
    )
    
    await update.message.reply_text(result.stdout, parse_mode='Markdown')

app = Application.builder().token("YOUR_TOKEN").build()
app.add_handler(CommandHandler("issues", find_issues))
app.run_polling()
```

### GitHub Action

```yaml
name: Weekly Issue Recommendations

on:
  schedule:
    - cron: '0 9 * * 1'  # Каждый понедельник в 9:00

jobs:
  recommend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Find issues
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python issue_matcher.py ${{ github.actor }} \
            --format markdown \
            --output issues.md \
            --top 10
      
      - name: Create issue
        uses: peter-evans/create-issue-from-file@v4
        with:
          title: Weekly Issue Recommendations
          content-filepath: issues.md
          labels: recommendations
```

## Устранение неполадок

### "User not found"
Проверьте правильность написания username.

### "Rate limit exceeded"
Установите GITHUB_TOKEN для увеличения лимита.

### "No issues found"
- Попробуйте расширить стек (добавьте топики к репозиториям)
- Проверьте, что у вас есть публичные репозитории
- Возможно, нет открытых good-first-issue в проектах с вашим стеком

### Медленная работа
- Ранжирование 20 issues занимает 10-30 секунд
- Используйте `--top` с меньшим значением для ускорения

## Примеры использования

### Для новичков в Open Source

```bash
# Найти простые задачи для начала
python issue_matcher.py torvalds --top 5
```

### Для изучения новых технологий

```bash
# Найти больше issues для разнообразия
python issue_matcher.py torvalds --top 20
```

### Для команды

```bash
# Создать список для всей команды
for user in alice bob charlie; do
  python issue_matcher.py $user --format markdown --output "${user}-issues.md"
done
```

## Лицензия

MIT
