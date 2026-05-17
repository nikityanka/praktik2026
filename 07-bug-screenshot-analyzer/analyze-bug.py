#!/usr/bin/env python3
"""
Bug Screenshot Analyzer

Анализирует скриншоты ошибок с помощью vision-модели.
Описывает проблему, классифицирует её и предлагает шаги решения.
"""

import os
import sys
import argparse
import base64
import time
from pathlib import Path
from typing import Dict, Optional
import google.generativeai as genai
from dotenv import load_dotenv

# Загружаем .env из папки со скриптом
load_dotenv(dotenv_path=Path(__file__).parent / '.env')

# Конфигурация
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Категории ошибок
ERROR_CATEGORIES = [
    'syntax_error',
    'runtime_error',
    'network_error',
    'ui_bug',
    'configuration_error',
    'dependency_error',
    'permission_error',
    'database_error',
    'other'
]

def encode_image(image_path: Path) -> str:
    """Кодирует изображение в base64"""
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')

def analyze_screenshot(image_path: Path, context: Optional[str] = None) -> Dict:
    """Анализирует скриншот ошибки с помощью vision-модели"""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY не установлен в переменных окружения")
    
    genai.configure(api_key=GEMINI_API_KEY)
    
    # Используем модель с поддержкой vision
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # Читаем изображение
    with open(image_path, 'rb') as f:
        image_data = f.read()
    
    # Формируем промпт
    context_text = f"\n\nДополнительный контекст: {context}" if context else ""
    
    prompt = f"""Проанализируй этот скриншот ошибки и предоставь детальный анализ.

{context_text}

Предоставь анализ в следующем формате:

## Описание проблемы
[Краткое описание того, что видно на скриншоте - какая ошибка, где она произошла]

## Категория
[Выбери одну из категорий: syntax_error, runtime_error, network_error, ui_bug, configuration_error, dependency_error, permission_error, database_error, other]

## Детали ошибки
[Подробное описание ошибки, включая:
- Текст ошибки (если виден)
- Место возникновения (файл, строка)
- Контекст (что пользователь пытался сделать)]

## Возможные причины
[Список возможных причин этой ошибки]

## Шаги решения
[Пошаговые инструкции для исправления проблемы]

## Дополнительные рекомендации
[Советы по предотвращению подобных ошибок в будущем]

Будь конкретным и практичным. Если на скриншоте виден код или текст ошибки, процитируй его."""

    # Отправляем запрос с retry механизмом
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = model.generate_content([prompt, {'mime_type': 'image/jpeg', 'data': image_data}])
            analysis_text = response.text
            break
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower() or "rate" in str(e).lower():
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    print(f"Rate limit достигнут, жду {wait_time} сек...", file=sys.stderr)
                    time.sleep(wait_time)
                    continue
            raise Exception(f"Ошибка при анализе: {e}")
    
    # Извлекаем категорию из текста
    category = 'other'
    for cat in ERROR_CATEGORIES:
        if cat in analysis_text.lower():
            category = cat
            break
    
    return {
        'analysis': analysis_text,
        'category': category,
        'image_path': str(image_path)
    }

def format_analysis(result: Dict, format_type: str = 'text') -> str:
    """Форматирует результат анализа"""
    if format_type == 'json':
        import json
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    elif format_type == 'markdown':
        output = f"# Анализ скриншота ошибки\n\n"
        output += f"**Файл:** `{result['image_path']}`\n\n"
        output += f"**Категория:** `{result['category']}`\n\n"
        output += "---\n\n"
        output += result['analysis']
        return output
    
    else:  # text
        output = "=" * 70 + "\n"
        output += "АНАЛИЗ СКРИНШОТА ОШИБКИ\n"
        output += "=" * 70 + "\n\n"
        output += f"Файл: {result['image_path']}\n"
        output += f"Категория: {result['category']}\n\n"
        output += "-" * 70 + "\n\n"
        output += result['analysis']
        output += "\n\n" + "=" * 70
        return output

def main():
    parser = argparse.ArgumentParser(
        description='Bug Screenshot Analyzer - анализ скриншотов ошибок с помощью AI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s error.png
  %(prog)s screenshot.jpg --context "Ошибка при запуске приложения"
  %(prog)s bug.png --format markdown --output report.md
  %(prog)s error.png --format json

Поддерживаемые форматы изображений:
  .png, .jpg, .jpeg, .gif, .bmp, .webp
        """
    )
    
    parser.add_argument(
        'image',
        type=Path,
        help='Путь к скриншоту ошибки'
    )
    
    parser.add_argument(
        '--context', '-c',
        help='Дополнительный контекст об ошибке'
    )
    
    parser.add_argument(
        '--format', '-f',
        choices=['text', 'markdown', 'json'],
        default='text',
        help='Формат вывода (по умолчанию: text)'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=Path,
        help='Сохранить результат в файл'
    )
    
    args = parser.parse_args()
    
    # Проверяем существование файла
    if not args.image.exists():
        print(f"Ошибка: файл '{args.image}' не существует", file=sys.stderr)
        sys.exit(1)
    
    # Проверяем расширение
    supported_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']
    if args.image.suffix.lower() not in supported_extensions:
        print(f"Ошибка: неподдерживаемый формат изображения '{args.image.suffix}'", file=sys.stderr)
        print(f"Поддерживаются: {', '.join(supported_extensions)}", file=sys.stderr)
        sys.exit(1)
    
    # Анализируем скриншот
    print(f"Анализирую скриншот '{args.image.name}'...", file=sys.stderr)
    
    try:
        result = analyze_screenshot(args.image, args.context)
        print("✓ Анализ завершен\n", file=sys.stderr)
    except Exception as e:
        print(f"Ошибка при анализе: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Форматируем результат
    formatted_output = format_analysis(result, args.format)
    
    # Выводим или сохраняем
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(formatted_output)
        print(f"✓ Результат сохранен в '{args.output}'", file=sys.stderr)
    else:
        print(formatted_output)

if __name__ == '__main__':
    main()


