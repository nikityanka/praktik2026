# Git Commit AI

CLI-инструмент для автоматической генерации commit-сообщений в формате Conventional Commits с использованием Google Gemini API.

## Возможности

- Анализ `git diff --staged` и генерация осмысленных commit-сообщений
- Поддержка формата Conventional Commits (feat, fix, refactor и т.д.)
- Указание типа коммита и scope через флаги
- Режим dry-run для предварительного просмотра
- Валидация сгенерированных сообщений
- Вывод в текстовом или JSON формате

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

4. (Опционально) Сделайте скрипт исполняемым и добавьте в PATH:
```bash
# Linux/Mac
chmod +x git-commit-ai.py
sudo ln -s $(pwd)/git-commit-ai.py /usr/local/bin/git-commit-ai

# Windows
# Добавьте директорию со скриптом в PATH или создайте bat-файл
```

## Получение API ключа

1. Перейдите на https://aistudio.google.com
2. Войдите с помощью Google аккаунта
3. Нажмите "Get API Key"
4. Создайте новый ключ и скопируйте его

## Использование

### Базовое использование

```bash
# Добавьте файлы в staging area
git add .

# Сгенерируйте и создайте коммит
python git-commit-ai.py
```

### Указание типа коммита

```bash
python git-commit-ai.py --type feat
python git-commit-ai.py --type fix
python git-commit-ai.py --type refactor
```

### Указание scope

```bash
python git-commit-ai.py --type feat --scope auth
python git-commit-ai.py --type fix --scope api
```

### Режим dry-run (без создания коммита)

```bash
python git-commit-ai.py --dry-run
python git-commit-ai.py -d --type feat --scope ui
```

### Вывод в JSON формате

```bash
python git-commit-ai.py --output json
python git-commit-ai.py -o json --dry-run
```

## Примеры сгенерированных сообщений

```
feat(auth): add JWT token refresh mechanism

fix(api): handle null response in user endpoint

refactor(database): extract query builder to separate module

docs(readme): update installation instructions

test(utils): add unit tests for date formatter
```

## Типы коммитов (Conventional Commits)

- `feat` - Новая функциональность
- `fix` - Исправление бага
- `docs` - Изменения в документации
- `style` - Форматирование, отсутствие изменений в коде
- `refactor` - Рефакторинг кода
- `perf` - Улучшение производительности
- `test` - Добавление или изменение тестов
- `build` - Изменения в системе сборки или зависимостях
- `ci` - Изменения в CI конфигурации
- `chore` - Другие изменения, не затрагивающие src или тесты
- `revert` - Откат предыдущего коммита

## Флаги командной строки

```
--type, -t        Тип коммита (feat, fix, refactor и т.д.)
--scope, -s       Область изменений (компонент, модуль)
--dry-run, -d     Показать сообщение без создания коммита
--output, -o      Формат вывода: text или json (по умолчанию: text)
--help, -h        Показать справку
```

## Технические детали

- **Язык**: Python 3.7+
- **LLM**: Google Gemini 2.5 Flash
- **Формат**: Conventional Commits
- **Ограничение diff**: 500 строк (автоматическая обрезка)

## Обработка ошибок

Инструмент обрабатывает следующие ситуации:
- Отсутствие git-репозитория
- Отсутствие проиндексированных изменений
- Слишком большие diff (автоматическая обрезка)
- Ошибки API
- Отсутствие API ключа

## Интеграция с git alias

Добавьте alias в `.gitconfig`:

```bash
git config --global alias.aic '!python C:\Users\Nikita\Desktop\pp\02-git-commit-ai\git-commit-ai.py'
```

Теперь можно использовать:
```bash
git aic
git aic --type feat --scope auth
```

## Ограничения

- Google AI Studio (Gemini): ~1500 запросов/день
- Максимальный размер diff: 500 строк (обрезается автоматически)
- Требуется Python 3.7+

## Лицензия

MIT
