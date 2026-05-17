#!/usr/bin/env python3
"""
Markdown Notes Assistant

Сканирует папку с .md файлами, находит смысловые связи между заметками
с помощью embeddings и предлагает добавить ссылки между ними.
Опционально генерирует краткое summary для каждой заметки.
"""

import os
import sys
import argparse
import re
from pathlib import Path
from typing import List, Dict, Tuple
from dotenv import load_dotenv
import numpy as np
import google.generativeai as genai
from sklearn.metrics.pairwise import cosine_similarity
import yaml

load_dotenv()

# Конфигурация
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

class Note:
    """Класс для представления заметки"""
    def __init__(self, path: Path):
        self.path = path
        self.title = path.stem
        self.content = ""
        self.frontmatter = {}
        self.body = ""
        self.embedding = None
        
    def read(self):
        """Читает содержимое заметки"""
        with open(self.path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.content = content
            self._parse_frontmatter()
    
    def _parse_frontmatter(self):
        """Парсит frontmatter (YAML между ---) если есть"""
        if self.content.startswith('---'):
            parts = self.content.split('---', 2)
            if len(parts) >= 3:
                try:
                    self.frontmatter = yaml.safe_load(parts[1]) or {}
                    self.body = parts[2].strip()
                except yaml.YAMLError:
                    self.body = self.content
            else:
                self.body = self.content
        else:
            self.body = self.content
    
    def get_text_for_embedding(self) -> str:
        """Возвращает текст для создания embedding"""
        # Используем заголовок и тело без markdown разметки
        text = f"{self.title}\n\n{self.body}"
        # Убираем markdown разметку
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)  # Код блоки
        text = re.sub(r'`[^`]+`', '', text)  # Инлайн код
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # Ссылки
        text = re.sub(r'[#*_~]', '', text)  # Markdown символы
        return text.strip()
    
    def update_frontmatter(self, key: str, value: str):
        """Обновляет значение в frontmatter"""
        self.frontmatter[key] = value
    
    def save(self):
        """Сохраняет заметку с обновленным frontmatter"""
        if self.frontmatter:
            frontmatter_str = yaml.dump(self.frontmatter, allow_unicode=True, sort_keys=False)
            new_content = f"---\n{frontmatter_str}---\n\n{self.body}"
        else:
            new_content = self.body
        
        with open(self.path, 'w', encoding='utf-8') as f:
            f.write(new_content)

def find_markdown_files(directory: Path) -> List[Path]:
    """Рекурсивно находит все .md файлы в директории"""
    return list(directory.rglob('*.md'))

def get_embeddings(texts: List[str]) -> np.ndarray:
    """Получает embeddings для списка текстов через Gemini API"""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY не установлен в переменных окружения")
    
    genai.configure(api_key=GEMINI_API_KEY)
    
    embeddings = []
    for i, text in enumerate(texts):
        print(f"Получаю embedding {i+1}/{len(texts)}...", file=sys.stderr)
        # Обрезаем текст если слишком длинный
        if len(text) > 10000:
            text = text[:10000]
        
        result = genai.embed_content(
            model="models/gemini-embedding-001",
            content=text,
            task_type="retrieval_document"
        )
        embeddings.append(result['embedding'])
    
    return np.array(embeddings)

def find_similar_notes(notes: List[Note], threshold: float = 0.7) -> List[Tuple[Note, Note, float]]:
    """Находит похожие заметки на основе косинусной близости embeddings"""
    # Получаем тексты для embeddings
    texts = [note.get_text_for_embedding() for note in notes]
    
    # Получаем embeddings
    print("Получаю embeddings для заметок...", file=sys.stderr)
    embeddings = get_embeddings(texts)
    
    # Сохраняем embeddings в заметках
    for note, embedding in zip(notes, embeddings):
        note.embedding = embedding
    
    # Вычисляем косинусную близость
    similarities = cosine_similarity(embeddings)
    
    # Находим пары похожих заметок
    similar_pairs = []
    n = len(notes)
    for i in range(n):
        for j in range(i + 1, n):
            similarity = similarities[i][j]
            if similarity >= threshold:
                similar_pairs.append((notes[i], notes[j], similarity))
    
    # Сортируем по убыванию схожести
    similar_pairs.sort(key=lambda x: x[2], reverse=True)
    
    return similar_pairs

def generate_summary(note: Note) -> str:
    """Генерирует краткое summary для заметки"""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY не установлен в переменных окружения")
    
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""Прочитай следующую заметку и создай краткое описание (summary) в 1-2 предложениях.
Summary должно отражать основную идею или тему заметки.

Заголовок: {note.title}

Содержимое:
{note.body[:2000]}

Верни ТОЛЬКО summary без дополнительных объяснений."""

    response = model.generate_content(prompt)
    return response.text.strip()

def suggest_link_text(note1: Note, note2: Note, similarity: float) -> str:
    """Генерирует предложение о связи между заметками"""
    return (f"Заметка '{note1.title}' похожа на '{note2.title}' "
            f"(схожесть: {similarity:.2%})")

def main():
    parser = argparse.ArgumentParser(
        description='Markdown Notes Assistant - находит связи между заметками',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'directory',
        type=Path,
        help='Путь к папке с markdown заметками'
    )
    
    parser.add_argument(
        '--threshold', '-t',
        type=float,
        default=0.7,
        help='Порог схожести для предложения связей (0.0-1.0, по умолчанию: 0.7)'
    )
    
    parser.add_argument(
        '--generate-summaries', '-s',
        action='store_true',
        help='Генерировать summary для каждой заметки и добавлять в frontmatter'
    )
    
    parser.add_argument(
        '--auto-update',
        action='store_true',
        help='Автоматически обновлять файлы без подтверждения (ОСТОРОЖНО!)'
    )
    
    parser.add_argument(
        '--max-suggestions',
        type=int,
        default=10,
        help='Максимальное количество предложений связей (по умолчанию: 10)'
    )
    
    args = parser.parse_args()
    
    # Проверяем существование директории
    if not args.directory.exists():
        print(f"Ошибка: директория '{args.directory}' не существует", file=sys.stderr)
        sys.exit(1)
    
    if not args.directory.is_dir():
        print(f"Ошибка: '{args.directory}' не является директорией", file=sys.stderr)
        sys.exit(1)
    
    # Находим все markdown файлы
    print(f"Сканирую директорию '{args.directory}'...", file=sys.stderr)
    md_files = find_markdown_files(args.directory)
    
    if not md_files:
        print("Не найдено ни одного .md файла", file=sys.stderr)
        sys.exit(1)
    
    print(f"Найдено {len(md_files)} заметок", file=sys.stderr)
    
    # Читаем заметки
    notes = []
    for md_file in md_files:
        note = Note(md_file)
        note.read()
        notes.append(note)
    
    # Генерируем summaries если требуется
    if args.generate_summaries:
        print("\nГенерирую summaries для заметок...", file=sys.stderr)
        for i, note in enumerate(notes):
            if 'summary' not in note.frontmatter:
                print(f"  [{i+1}/{len(notes)}] {note.title}", file=sys.stderr)
                try:
                    summary = generate_summary(note)
                    note.update_frontmatter('summary', summary)
                    print(f"    Summary: {summary}", file=sys.stderr)
                except Exception as e:
                    print(f"    Ошибка: {e}", file=sys.stderr)
        
        # Сохраняем заметки с summaries
        if not args.auto_update:
            response = input("\nСохранить summaries в файлы? [y/N]: ").strip().lower()
            if response not in ('y', 'yes', 'д', 'да'):
                print("Summaries не сохранены", file=sys.stderr)
            else:
                for note in notes:
                    if 'summary' in note.frontmatter:
                        note.save()
                print("Summaries сохранены", file=sys.stderr)
        else:
            for note in notes:
                if 'summary' in note.frontmatter:
                    note.save()
            print("Summaries сохранены", file=sys.stderr)
    
    # Находим похожие заметки
    print("\nАнализирую связи между заметками...", file=sys.stderr)
    similar_pairs = find_similar_notes(notes, args.threshold)
    
    if not similar_pairs:
        print(f"\nНе найдено похожих заметок с порогом схожести {args.threshold}", file=sys.stderr)
        print("Попробуйте уменьшить порог с помощью --threshold", file=sys.stderr)
        sys.exit(0)
    
    # Выводим результаты
    print(f"\n{'='*70}")
    print(f"Найдено {len(similar_pairs)} связей между заметками")
    print(f"{'='*70}\n")
    
    for i, (note1, note2, similarity) in enumerate(similar_pairs[:args.max_suggestions], 1):
        print(f"{i}. {suggest_link_text(note1, note2, similarity)}")
        print(f"   Файлы:")
        print(f"     - {note1.path.relative_to(args.directory)}")
        print(f"     - {note2.path.relative_to(args.directory)}")
        print()
    
    if len(similar_pairs) > args.max_suggestions:
        print(f"... и еще {len(similar_pairs) - args.max_suggestions} связей")
        print(f"Используйте --max-suggestions для отображения большего количества\n")
    
    print("\nРекомендации:")
    print("- Рассмотрите возможность добавления ссылок между похожими заметками")
    print("- Используйте формат [[Название заметки]] для создания ссылок в Obsidian")
    print("- Высокая схожесть может указывать на дублирование контента")

if __name__ == '__main__':
    main()



