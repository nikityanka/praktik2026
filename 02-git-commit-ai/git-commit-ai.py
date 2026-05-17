#!/usr/bin/env python3

import os
import sys
import subprocess
import argparse
import json
from typing import Optional
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

COMMIT_TYPES = {
    'feat': 'Новая функциональность',
    'fix': 'Исправление бага',
    'docs': 'Изменения в документации',
    'style': 'Форматирование, отсутствие изменений в коде',
    'refactor': 'Рефакторинг кода',
    'perf': 'Улучшение производительности',
    'test': 'Добавление или изменение тестов',
    'build': 'Изменения в системе сборки или зависимостях',
    'ci': 'Изменения в CI конфигурации',
    'chore': 'Другие изменения, не затрагивающие src или тесты',
    'revert': 'Откат предыдущего коммита'
}

def get_git_diff() -> Optional[str]:
    try:
        result = subprocess.run(
            ['git', 'diff', '--staged'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при выполнении git diff: {e}", file=sys.stderr)
        return None
    except FileNotFoundError:
        print("Git не найден. Убедитесь, что git установлен и доступен в PATH.", file=sys.stderr)
        return None

def check_git_repo() -> bool:
    try:
        subprocess.run(
            ['git', 'rev-parse', '--git-dir'],
            capture_output=True,
            encoding='utf-8',
            errors='replace',
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        return False

def has_staged_changes() -> bool:
    try:
        result = subprocess.run(
            ['git', 'diff', '--staged', '--quiet'],
            capture_output=True,
            encoding='utf-8',
            errors='replace'
        )
        return result.returncode != 0
    except subprocess.CalledProcessError:
        return False

def truncate_diff(diff: str, max_lines: int = 500) -> str:
    lines = diff.split('\n')
    if len(lines) <= max_lines:
        return diff
    
    truncated = '\n'.join(lines[:max_lines])
    truncated += f"\n\n... (обрезано {len(lines) - max_lines} строк)"
    return truncated

def generate_commit_message(diff: str, commit_type: Optional[str] = None, 
                           scope: Optional[str] = None) -> str:
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY не установлен в переменных окружения")
    
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    diff = truncate_diff(diff)
    
    type_constraint = ""
    if commit_type:
        type_constraint = f"Используй тип коммита: {commit_type}"
    
    scope_constraint = ""
    if scope:
        scope_constraint = f"Используй scope: {scope}"
    
    prompt = f"""Проанализируй следующий git diff и создай commit-сообщение в формате Conventional Commits.

Формат: <type>(<scope>): <subject>

Где:
- type: один из {', '.join(COMMIT_TYPES.keys())}
- scope: опциональная область изменений (компонент, модуль, файл)
- subject: краткое описание изменений (до 50 символов, начинается с маленькой буквы, без точки в конце)

{type_constraint}
{scope_constraint}

Правила:
1. Определи тип изменений (feat, fix, refactor и т.д.)
2. Если изменения касаются конкретного компонента/модуля, укажи scope
3. Опиши ЧТО изменилось и ЗАЧЕМ, а не КАК
4. Используй повелительное наклонение ("add", а не "added" или "adds")
5. Сообщение должно быть на английском языке
6. Не используй точку в конце subject

Git diff:
```
{diff}
```

Верни ТОЛЬКО commit-сообщение в формате Conventional Commits, без дополнительных объяснений."""

    try:
        response = model.generate_content(prompt)
        commit_msg = response.text.strip()
        
        if commit_msg.startswith('```'):
            lines = commit_msg.split('\n')
            commit_msg = '\n'.join(lines[1:-1]) if len(lines) > 2 else commit_msg
        
        return commit_msg.strip()
    
    except Exception as e:
        raise Exception(f"Ошибка при генерации commit-сообщения: {str(e)}")

def validate_commit_message(message: str) -> bool:
    if not message:
        return False
    
    first_line = message.split('\n')[0]
    has_type = any(first_line.startswith(f"{t}(") or first_line.startswith(f"{t}:") 
                   for t in COMMIT_TYPES.keys())
    
    return has_type

def main():
    parser = argparse.ArgumentParser(
        description='AI-powered Git Commit Message Generator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Примеры использования:
  %(prog)s                          # Генерация commit-сообщения
  %(prog)s --type feat              # Указать тип коммита
  %(prog)s --type fix --scope auth  # Указать тип и scope
  %(prog)s --dry-run                # Показать сообщение без коммита

Доступные типы коммитов:
{chr(10).join(f"  {k:12} - {v}" for k, v in COMMIT_TYPES.items())}
        """
    )
    
    parser.add_argument(
        '--type', '-t',
        choices=list(COMMIT_TYPES.keys()),
        help='Тип коммита (feat, fix, refactor и т.д.)'
    )
    
    parser.add_argument(
        '--scope', '-s',
        help='Область изменений (компонент, модуль)'
    )
    
    parser.add_argument(
        '--dry-run', '-d',
        action='store_true',
        help='Показать сгенерированное сообщение без создания коммита'
    )
    
    parser.add_argument(
        '--output', '-o',
        choices=['text', 'json'],
        default='text',
        help='Формат вывода (по умолчанию: text)'
    )
    
    args = parser.parse_args()
    
    if not check_git_repo():
        print("Ошибка: текущая директория не является git-репозиторием", file=sys.stderr)
        sys.exit(1)
    
    if not has_staged_changes():
        print("Нет проиндексированных изменений. Используйте 'git add' для добавления файлов.", 
              file=sys.stderr)
        sys.exit(1)
    
    print("Анализирую изменения...", file=sys.stderr)
    diff = get_git_diff()
    
    if not diff:
        print("Не удалось получить git diff", file=sys.stderr)
        sys.exit(1)
    
    print("Генерирую commit-сообщение...", file=sys.stderr)
    try:
        commit_message = generate_commit_message(diff, args.type, args.scope)
    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)
    
    if not validate_commit_message(commit_message):
        print("Предупреждение: сгенерированное сообщение может не соответствовать формату Conventional Commits",
              file=sys.stderr)
    
    if args.output == 'json':
        output = {
            'message': commit_message,
            'type': args.type,
            'scope': args.scope,
            'dry_run': args.dry_run
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print("\n" + "="*60)
        print("Сгенерированное commit-сообщение:")
        print("="*60)
        print(commit_message)
        print("="*60 + "\n")
    
    if args.dry_run:
        print("Режим dry-run: коммит не создан", file=sys.stderr)
        sys.exit(0)
    
    try:
        response = input("Создать коммит с этим сообщением? [y/N]: ").strip().lower()
        if response not in ('y', 'yes', 'д', 'да'):
            print("Коммит отменён", file=sys.stderr)
            sys.exit(0)
    except KeyboardInterrupt:
        print("\nКоммит отменён", file=sys.stderr)
        sys.exit(0)
    
    try:
        subprocess.run(
            ['git', 'commit', '-m', commit_message],
            encoding='utf-8',
            errors='replace',
            check=True
        )
        print("✓ Коммит успешно создан", file=sys.stderr)
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при создании коммита: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
