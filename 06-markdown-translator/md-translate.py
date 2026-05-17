#!/usr/bin/env python3
"""
Markdown Translator

Переводит markdown-файлы с сохранением форматирования.
Переводит только текст, не трогая код, ссылки, HTML-теги и frontmatter.
"""

import os
import sys
import argparse
import re
import time
from pathlib import Path
from typing import List, Dict, Optional
import google.generativeai as genai
from dotenv import load_dotenv

# Загружаем .env из папки со скриптом
load_dotenv(dotenv_path=Path(__file__).parent / '.env')

# Конфигурация
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Поддерживаемые языки
LANGUAGES = {
    'en': 'English',
    'ru': 'Russian',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'it': 'Italian',
    'pt': 'Portuguese',
    'zh': 'Chinese',
    'ja': 'Japanese',
    'ko': 'Korean'
}

class MarkdownNode:
    """Узел markdown документа"""
    def __init__(self, node_type: str, content: str, translate: bool = False):
        self.node_type = node_type
        self.content = content
        self.translate = translate

def extract_frontmatter(content: str) -> tuple[Optional[str], str]:
    """Извлекает frontmatter из markdown"""
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            return parts[1], parts[2]
    return None, content

def parse_markdown_structure(content: str) -> List[MarkdownNode]:
    """
    Парсит markdown и разделяет на узлы для перевода и не для перевода.
    """
    nodes = []
    
    # Регулярные выражения для различных элементов
    patterns = [
        # Код блоки (```...```)
        (r'```[\s\S]*?```', 'code_block', False),
        # Инлайн код (`...`)
        (r'`[^`\n]+`', 'inline_code', False),
        # HTML теги
        (r'<[^>]+>', 'html_tag', False),
        # Изображения ![alt](url)
        (r'!\[([^\]]*)\]\([^\)]+\)', 'image', True),  # Переводим только alt текст
        # Ссылки [text](url)
        (r'\[([^\]]+)\]\([^\)]+\)', 'link', True),  # Переводим только текст ссылки
    ]
    
    # Создаем комбинированный паттерн
    combined_pattern = '|'.join(f'({pattern})' for pattern, _, _ in patterns)
    
    last_end = 0
    for match in re.finditer(combined_pattern, content):
        # Добавляем текст перед совпадением
        if match.start() > last_end:
            text = content[last_end:match.start()]
            if text.strip():
                nodes.append(MarkdownNode('text', text, translate=True))
        
        # Определяем тип узла
        matched_text = match.group(0)
        
        if matched_text.startswith('```'):
            nodes.append(MarkdownNode('code_block', matched_text, translate=False))
        elif matched_text.startswith('`'):
            nodes.append(MarkdownNode('inline_code', matched_text, translate=False))
        elif matched_text.startswith('<'):
            nodes.append(MarkdownNode('html_tag', matched_text, translate=False))
        elif matched_text.startswith('!['):
            # Для изображений сохраняем структуру, но помечаем alt для перевода
            nodes.append(MarkdownNode('image', matched_text, translate=True))
        elif matched_text.startswith('['):
            # Для ссылок сохраняем структуру, но помечаем текст для перевода
            nodes.append(MarkdownNode('link', matched_text, translate=True))
        
        last_end = match.end()
    
    # Добавляем оставшийся текст
    if last_end < len(content):
        text = content[last_end:]
        if text.strip():
            nodes.append(MarkdownNode('text', text, translate=True))
    
    return nodes

def translate_text(text: str, target_lang: str, source_lang: Optional[str] = None) -> str:
    """Переводит текст с помощью Gemini API"""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY не установлен в переменных окружения")
    
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    target_language = LANGUAGES.get(target_lang, target_lang)
    source_language = LANGUAGES.get(source_lang, 'auto-detect') if source_lang else 'auto-detect'
    
    prompt = f"""Переведи следующий текст на {target_language}.

Правила:
1. Переводи ТОЛЬКО текст, сохраняя всю markdown разметку
2. НЕ переводи код в обратных кавычках
3. НЕ переводи URL и пути к файлам
4. НЕ переводи HTML теги
5. Сохраняй все символы markdown (*, _, #, -, и т.д.)
6. Сохраняй переносы строк и форматирование
7. Верни ТОЛЬКО переведенный текст без объяснений

Текст для перевода:
{text}

Перевод:"""

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower() or "rate" in str(e).lower():
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    print(f"  Rate limit достигнут, жду {wait_time} сек...", file=sys.stderr)
                    time.sleep(wait_time)
                    continue
            raise Exception(f"Ошибка при переводе: {e}")

def translate_markdown_node(node: MarkdownNode, target_lang: str, source_lang: Optional[str] = None) -> str:
    """Переводит отдельный узел markdown"""
    if not node.translate:
        return node.content
    
    if node.node_type == 'text':
        # Обычный текст - переводим полностью
        return translate_text(node.content, target_lang, source_lang)
    
    elif node.node_type == 'link':
        # Ссылка [text](url) - переводим только text
        match = re.match(r'\[([^\]]+)\]\(([^\)]+)\)', node.content)
        if match:
            link_text = match.group(1)
            url = match.group(2)
            translated_text = translate_text(link_text, target_lang, source_lang)
            return f'[{translated_text}]({url})'
        return node.content
    
    elif node.node_type == 'image':
        # Изображение ![alt](url) - переводим только alt
        match = re.match(r'!\[([^\]]*)\]\(([^\)]+)\)', node.content)
        if match:
            alt_text = match.group(1)
            url = match.group(2)
            if alt_text:
                translated_alt = translate_text(alt_text, target_lang, source_lang)
                return f'![{translated_alt}]({url})'
        return node.content
    
    return node.content

def translate_markdown_file(input_path: Path, target_lang: str, 
                           source_lang: Optional[str] = None,
                           output_path: Optional[Path] = None) -> str:
    """Переводит markdown файл"""
    
    # Читаем файл
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Извлекаем frontmatter
    frontmatter, body = extract_frontmatter(content)
    
    # Парсим структуру
    nodes = parse_markdown_structure(body)
    
    # Переводим каждый узел
    translated_nodes = []
    total = len([n for n in nodes if n.translate])
    current = 0
    
    for node in nodes:
        if node.translate:
            current += 1
            print(f"  Перевожу часть {current}/{total}...", end='\r', file=sys.stderr)
            translated = translate_markdown_node(node, target_lang, source_lang)
            translated_nodes.append(translated)
        else:
            translated_nodes.append(node.content)
    
    print(" " * 50, end='\r', file=sys.stderr)
    
    # Собираем результат
    translated_body = ''.join(translated_nodes)
    
    # Добавляем frontmatter обратно
    if frontmatter:
        result = f'---{frontmatter}---\n\n{translated_body}'
    else:
        result = translated_body
    
    return result

def main():
    parser = argparse.ArgumentParser(
        description='Markdown Translator - переводит markdown с сохранением форматирования',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Поддерживаемые языки:
{chr(10).join(f"  {code:5} - {name}" for code, name in LANGUAGES.items())}

Примеры использования:
  %(prog)s README.md --target ru
  %(prog)s docs/guide.md --target es --source en
  %(prog)s README.md --target fr --output README.fr.md
  %(prog)s docs/ --target de --recursive
        """
    )
    
    parser.add_argument(
        'input',
        type=Path,
        help='Путь к markdown файлу или директории'
    )
    
    parser.add_argument(
        '--target', '-t',
        required=True,
        choices=list(LANGUAGES.keys()),
        help='Целевой язык перевода'
    )
    
    parser.add_argument(
        '--source', '-s',
        choices=list(LANGUAGES.keys()),
        help='Исходный язык (опционально, определяется автоматически)'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=Path,
        help='Путь для сохранения перевода (по умолчанию: <filename>.<lang>.md)'
    )
    
    parser.add_argument(
        '--recursive', '-r',
        action='store_true',
        help='Рекурсивно обрабатывать все .md файлы в директории'
    )
    
    parser.add_argument(
        '--overwrite',
        action='store_true',
        help='Перезаписать существующие файлы без подтверждения'
    )
    
    args = parser.parse_args()
    
    # Проверяем существование входного пути
    if not args.input.exists():
        print(f"Ошибка: путь '{args.input}' не существует", file=sys.stderr)
        sys.exit(1)
    
    # Определяем файлы для обработки
    if args.input.is_file():
        if args.input.suffix != '.md':
            print(f"Ошибка: файл должен иметь расширение .md", file=sys.stderr)
            sys.exit(1)
        files = [args.input]
    elif args.input.is_dir():
        if args.recursive:
            files = list(args.input.rglob('*.md'))
        else:
            files = list(args.input.glob('*.md'))
        
        if not files:
            print(f"Не найдено .md файлов в '{args.input}'", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"Ошибка: '{args.input}' не является файлом или директорией", file=sys.stderr)
        sys.exit(1)
    
    print(f"Найдено {len(files)} файлов для перевода", file=sys.stderr)
    
    # Обрабатываем каждый файл
    for i, file_path in enumerate(files, 1):
        print(f"\n[{i}/{len(files)}] Обрабатываю {file_path.name}...", file=sys.stderr)
        
        # Определяем путь для сохранения
        if args.output and len(files) == 1:
            output_path = args.output
        else:
            # Создаем имя файла с языковым суффиксом
            stem = file_path.stem
            output_path = file_path.parent / f"{stem}.{args.target}.md"
        
        # Проверяем существование выходного файла
        if output_path.exists() and not args.overwrite:
            response = input(f"  Файл '{output_path}' уже существует. Перезаписать? [y/N]: ").strip().lower()
            if response not in ('y', 'yes', 'д', 'да'):
                print("  Пропущено", file=sys.stderr)
                continue
        
        try:
            # Переводим файл
            translated = translate_markdown_file(
                file_path,
                args.target,
                args.source
            )
            
            # Сохраняем результат
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(translated)
            
            print(f"  ✓ Сохранено в '{output_path}'", file=sys.stderr)
            
        except Exception as e:
            print(f"  ✗ Ошибка: {e}", file=sys.stderr)
            continue
    
    print(f"\n✓ Обработано {len(files)} файлов", file=sys.stderr)

if __name__ == '__main__':
    main()


