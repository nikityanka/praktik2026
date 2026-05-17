#!/usr/bin/env python3
"""
Voice to Task Converter

Конвертирует голосовые заметки в структурированные задачи.
Использует Whisper для транскрипции и LLM для структурирования.
"""

import os
import sys
import argparse
import json
import time
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime, timedelta
import google.generativeai as genai
from dotenv import load_dotenv

# Загружаем .env из папки со скриптом
load_dotenv(dotenv_path=Path(__file__).parent / '.env')

# Конфигурация
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

def transcribe_audio(audio_path: Path) -> str:
    """Транскрибирует аудио с помощью Gemini API"""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY не установлен в переменных окружения")
    
    genai.configure(api_key=GEMINI_API_KEY)
    
    # Читаем аудио файл
    with open(audio_path, 'rb') as f:
        audio_data = f.read()
    
    # Определяем MIME тип
    ext = audio_path.suffix.lower()
    mime_types = {
        '.mp3': 'audio/mp3',
        '.wav': 'audio/wav',
        '.m4a': 'audio/mp4',
        '.ogg': 'audio/ogg',
        '.flac': 'audio/flac'
    }
    mime_type = mime_types.get(ext, 'audio/mp3')
    
    # Используем Gemini для транскрипции
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = """Транскрибируй это аудио в текст. 
Верни ТОЛЬКО текст транскрипции без дополнительных комментариев."""
    
    # Retry механизм
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = model.generate_content([
                prompt,
                {'mime_type': mime_type, 'data': audio_data}
            ])
            return response.text.strip()
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower() or "rate" in str(e).lower():
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    print(f"Rate limit достигнут, жду {wait_time} сек...", file=sys.stderr)
                    time.sleep(wait_time)
                    continue
            raise Exception(f"Ошибка при транскрипции: {e}")

def parse_task(transcription: str) -> Dict:
    """Парсит транскрипцию и создает структурированную задачу"""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY не установлен в переменных окружения")
    
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""Проанализируй следующую голосовую заметку и преобразуй её в структурированную задачу.

Транскрипция:
{transcription}

Извлеки следующую информацию и верни в JSON формате:

{{
  "title": "Краткий заголовок задачи (до 50 символов)",
  "description": "Подробное описание задачи",
  "priority": "high/medium/low",
  "tags": ["тег1", "тег2", "тег3"],
  "deadline": "YYYY-MM-DD или null если не указан",
  "estimated_time": "Оценка времени в часах или null",
  "action_items": [
    "Конкретное действие 1",
    "Конкретное действие 2"
  ],
  "context": "Дополнительный контекст или заметки"
}}

Правила:
1. Заголовок должен быть кратким и информативным
2. Приоритет определяй по срочности и важности из контекста
3. Теги должны быть релевантными (проект, категория, тип работы)
4. Дедлайн извлекай из фраз типа "до пятницы", "на следующей неделе"
5. Если дедлайн относительный (например "завтра"), вычисли конкретную дату (сегодня {datetime.now().strftime('%Y-%m-%d')})
6. Action items - конкретные шаги для выполнения задачи
7. Верни ТОЛЬКО валидный JSON без дополнительного текста

JSON:"""

    # Retry механизм
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            json_text = response.text.strip()
            
            # Убираем markdown блоки если есть
            if json_text.startswith('```json'):
                json_text = json_text.split('```json', 1)[1]
                json_text = json_text.rsplit('```', 1)[0]
            elif json_text.startswith('```'):
                json_text = json_text.split('```', 1)[1]
                json_text = json_text.rsplit('```', 1)[0]
            
            # Парсим JSON
            try:
                task = json.loads(json_text.strip())
                return task
            except json.JSONDecodeError as e:
                raise Exception(f"Не удалось распарсить JSON: {e}\n{json_text}")
                
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower() or "rate" in str(e).lower():
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    print(f"Rate limit достигнут, жду {wait_time} сек...", file=sys.stderr)
                    time.sleep(wait_time)
                    continue
            raise Exception(f"Ошибка при создании задачи: {e}")

def format_task(task: Dict, format_type: str = 'text') -> str:
    """Форматирует задачу в нужный формат"""
    if format_type == 'json':
        return json.dumps(task, ensure_ascii=False, indent=2)
    
    elif format_type == 'markdown':
        output = f"# {task['title']}\n\n"
        
        # Метаданные
        output += "## Метаданные\n\n"
        output += f"- **Приоритет:** {task['priority']}\n"
        if task.get('deadline'):
            output += f"- **Дедлайн:** {task['deadline']}\n"
        if task.get('estimated_time'):
            output += f"- **Оценка времени:** {task['estimated_time']} ч\n"
        if task.get('tags'):
            output += f"- **Теги:** {', '.join(f'`{tag}`' for tag in task['tags'])}\n"
        
        # Описание
        output += f"\n## Описание\n\n{task['description']}\n"
        
        # Action items
        if task.get('action_items'):
            output += "\n## Шаги выполнения\n\n"
            for item in task['action_items']:
                output += f"- [ ] {item}\n"
        
        # Контекст
        if task.get('context'):
            output += f"\n## Дополнительно\n\n{task['context']}\n"
        
        return output
    
    else:  # text
        output = "=" * 70 + "\n"
        output += f"ЗАДАЧА: {task['title']}\n"
        output += "=" * 70 + "\n\n"
        
        output += f"Приоритет: {task['priority'].upper()}\n"
        if task.get('deadline'):
            output += f"Дедлайн: {task['deadline']}\n"
        if task.get('estimated_time'):
            output += f"Оценка времени: {task['estimated_time']} ч\n"
        if task.get('tags'):
            output += f"Теги: {', '.join(task['tags'])}\n"
        
        output += "\n" + "-" * 70 + "\n"
        output += "ОПИСАНИЕ:\n"
        output += "-" * 70 + "\n"
        output += task['description'] + "\n"
        
        if task.get('action_items'):
            output += "\n" + "-" * 70 + "\n"
            output += "ШАГИ ВЫПОЛНЕНИЯ:\n"
            output += "-" * 70 + "\n"
            for i, item in enumerate(task['action_items'], 1):
                output += f"{i}. {item}\n"
        
        if task.get('context'):
            output += "\n" + "-" * 70 + "\n"
            output += "ДОПОЛНИТЕЛЬНО:\n"
            output += "-" * 70 + "\n"
            output += task['context'] + "\n"
        
        output += "\n" + "=" * 70
        return output

def main():
    parser = argparse.ArgumentParser(
        description='Voice to Task - конвертирует голосовые заметки в структурированные задачи',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s voice.mp3
  %(prog)s voice.mp3 --format markdown
  %(prog)s voice.mp3 --format json --output task.json
  %(prog)s voice.mp3 --transcription-only

Поддерживаемые форматы аудио:
  .mp3, .wav, .m4a, .ogg, .flac
        """
    )
    
    parser.add_argument(
        'audio',
        type=Path,
        help='Путь к аудио файлу с голосовой заметкой'
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
    
    parser.add_argument(
        '--transcription-only', '-t',
        action='store_true',
        help='Только транскрибировать без структурирования'
    )
    
    parser.add_argument(
        '--show-transcription',
        action='store_true',
        help='Показать транскрипцию перед задачей'
    )
    
    args = parser.parse_args()
    
    # Проверяем существование файла
    if not args.audio.exists():
        print(f"Ошибка: файл '{args.audio}' не существует", file=sys.stderr)
        sys.exit(1)
    
    # Проверяем расширение
    supported_extensions = ['.mp3', '.wav', '.m4a', '.ogg', '.flac']
    if args.audio.suffix.lower() not in supported_extensions:
        print(f"Ошибка: неподдерживаемый формат аудио '{args.audio.suffix}'", file=sys.stderr)
        print(f"Поддерживаются: {', '.join(supported_extensions)}", file=sys.stderr)
        sys.exit(1)
    
    # Транскрибируем аудио
    print(f"Транскрибирую аудио '{args.audio.name}'...", file=sys.stderr)
    
    try:
        transcription = transcribe_audio(args.audio)
        print("✓ Транскрипция завершена\n", file=sys.stderr)
    except Exception as e:
        print(f"Ошибка при транскрипции: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Если только транскрипция
    if args.transcription_only:
        print("=" * 70)
        print("ТРАНСКРИПЦИЯ:")
        print("=" * 70)
        print(transcription)
        print("=" * 70)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(transcription)
            print(f"\n✓ Транскрипция сохранена в '{args.output}'", file=sys.stderr)
        
        sys.exit(0)
    
    # Показываем транскрипцию если требуется
    if args.show_transcription:
        print("=" * 70, file=sys.stderr)
        print("ТРАНСКРИПЦИЯ:", file=sys.stderr)
        print("=" * 70, file=sys.stderr)
        print(transcription, file=sys.stderr)
        print("=" * 70 + "\n", file=sys.stderr)
    
    # Структурируем задачу
    print("Создаю структурированную задачу...", file=sys.stderr)
    
    try:
        task = parse_task(transcription)
        print("✓ Задача создана\n", file=sys.stderr)
    except Exception as e:
        print(f"Ошибка при создании задачи: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Форматируем результат
    formatted_output = format_task(task, args.format)
    
    # Выводим или сохраняем
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(formatted_output)
        print(f"✓ Задача сохранена в '{args.output}'", file=sys.stderr)
    else:
        print(formatted_output)

if __name__ == '__main__':
    main()


