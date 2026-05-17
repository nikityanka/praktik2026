#!/usr/bin/env python3
"""
RAG Documentation Search

Система поиска по документации с использованием Retrieval-Augmented Generation (RAG).
Индексирует документы, создает embeddings и отвечает на вопросы с указанием источников.
"""

import os
import sys
import argparse
import hashlib
import time
from pathlib import Path
from typing import List, Dict
import google.generativeai as genai
import chromadb
from dotenv import load_dotenv

# Загружаем .env из папки со скриптом
load_dotenv(dotenv_path=Path(__file__).parent / '.env')

# Проверка ключа
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    print("Ошибка: GEMINI_API_KEY не найден. Создайте файл .env с ключом или установите переменную окружения.", file=sys.stderr)
    sys.exit(1)

DB_PATH = Path.home() / '.rag-docs-search' / 'chroma_db'

class DocumentChunk:
    """Класс для представления чанка документа"""
    def __init__(self, content: str, source: str, chunk_id: int):
        self.content = content
        self.source = source
        self.chunk_id = chunk_id
        self.metadata = {
            'source': source,
            'chunk_id': chunk_id,
            'length': len(content)
        }

def read_document(file_path: Path) -> str:
    """Читает содержимое документа"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        for encoding in ['latin-1', 'cp1252']:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        raise Exception(f"Не удалось прочитать файл {file_path}")

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Разбивает текст на чанки с перекрытием."""
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        if end < len(text):
            search_start = max(end - 100, start)
            sentence_end = text.rfind('.', search_start, end)
            if sentence_end != -1 and sentence_end > start:
                end = sentence_end + 1

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = end - overlap

    return chunks

def get_embedding(text: str, task_type: str = "retrieval_document") -> List[float]:
    """Получает embedding для текста через Gemini API."""
    genai.configure(api_key=GEMINI_API_KEY)

    if len(text) > 10000:
        text = text[:10000]

    max_retries = 3
    for attempt in range(max_retries):
        try:
            result = genai.embed_content(
                model="models/gemini-embedding-001",
                content=text,
                task_type=task_type
            )
            return result['embedding']
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower() or "rate" in str(e).lower():
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    print(f"  Rate limit достигнут, жду {wait_time} сек...", file=sys.stderr)
                    time.sleep(wait_time)
                    continue
            raise Exception(f"Ошибка при получении embedding: {e}")

def get_query_embedding(text: str) -> List[float]:
    """Получает embedding для поискового запроса."""
    return get_embedding(text, task_type="retrieval_query")

def index_documents(docs_path: Path, collection_name: str = "docs",
                   chunk_size: int = 1000, overlap: int = 200):
    """Индексирует документы в векторную БД."""
    DB_PATH.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(DB_PATH))

    try:
        client.delete_collection(name=collection_name)
    except:
        pass

    collection = client.create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )

    supported_extensions = ['.md', '.txt', '.rst']
    doc_files = []
    for ext in supported_extensions:
        doc_files.extend(docs_path.rglob(f'*{ext}'))

    if not doc_files:
        print(f"Не найдено документов в {docs_path}", file=sys.stderr)
        return

    print(f"Найдено {len(doc_files)} документов", file=sys.stderr)
    total_chunks = 0

    for i, doc_file in enumerate(doc_files, 1):
        print(f"[{i}/{len(doc_files)}] Обрабатываю {doc_file.name}...", file=sys.stderr)

        try:
            content = read_document(doc_file)
            chunks = chunk_text(content, chunk_size, overlap)
            print(f"  Создано {len(chunks)} чанков", file=sys.stderr)

            for j, chunk in enumerate(chunks):
                print(f"  Обрабатываю чанк {j+1}/{len(chunks)}...", end='\r', file=sys.stderr)
                embedding = get_embedding(chunk)
                chunk_id = hashlib.md5(f"{doc_file}{j}".encode()).hexdigest()

                collection.add(
                    embeddings=[embedding],
                    documents=[chunk],
                    metadatas=[{
                        'source': str(doc_file.relative_to(docs_path)),
                        'chunk_id': j,
                        'total_chunks': len(chunks)
                    }],
                    ids=[chunk_id]
                )
                total_chunks += 1

            print(f"  ✓ Обработано {len(chunks)} чанков" + " " * 20, file=sys.stderr)

        except Exception as e:
            print(f"  ✗ Ошибка: {e}", file=sys.stderr)
            continue

    print(f"\n✓ Индексирование завершено: {total_chunks} чанков из {len(doc_files)} документов", file=sys.stderr)

def search_documents(query: str, collection_name: str = "docs",
                    top_k: int = 5) -> List[Dict]:
    """Ищет релевантные чанки документов."""
    client = chromadb.PersistentClient(path=str(DB_PATH))

    try:
        collection = client.get_collection(name=collection_name)
    except:
        raise Exception(f"Коллекция '{collection_name}' не найдена. Сначала проиндексируйте документы командой index.")

    query_embedding = get_query_embedding(query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    chunks = []
    for i in range(len(results['documents'][0])):
        chunks.append({
            'content': results['documents'][0][i],
            'source': results['metadatas'][0][i]['source'],
            'chunk_id': results['metadatas'][0][i]['chunk_id'],
            'distance': results['distances'][0][i] if 'distances' in results else None
        })

    return chunks

def generate_answer(query: str, context_chunks: List[Dict]) -> str:
    """Генерирует ответ на основе найденных чанков."""
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')

    context = "\n\n---\n\n".join([
        f"Источник: {chunk['source']}\n{chunk['content']}"
        for chunk in context_chunks
    ])

    prompt = f"""Ответь на вопрос пользователя на основе предоставленной документации.

Вопрос: {query}

Документация:
{context}

Инструкции:
1. Используй ТОЛЬКО информацию из предоставленной документации
2. Если в документации нет ответа на вопрос, так и скажи
3. Укажи источники информации в конце ответа
4. Будь конкретным и точным
5. Отвечай на том же языке, что и вопрос

Ответ:"""

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower() or "rate" in str(e).lower():
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    print(f"Rate limit достигнут, жду {wait_time} сек...", file=sys.stderr)
                    time.sleep(wait_time)
                    continue
            raise Exception(f"Ошибка при генерации ответа: {e}")

def main():
    parser = argparse.ArgumentParser(
        description='RAG Documentation Search',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:

  # Индексирование документов
  %(prog)s index /path/to/docs

  # Поиск в документации
  %(prog)s search "How to install the package?"

  # Поиск с большим количеством результатов
  %(prog)s search "API reference" --top-k 10

  # Только поиск без генерации ответа
  %(prog)s search "configuration" --no-answer
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Команды')

    # Команда index
    index_parser = subparsers.add_parser('index', help='Индексировать документы')
    index_parser.add_argument('path', type=Path, help='Путь к папке с документами')
    index_parser.add_argument('--collection', '-c', default='docs', help='Имя коллекции')
    index_parser.add_argument('--chunk-size', type=int, default=1000, help='Размер чанка')
    index_parser.add_argument('--overlap', type=int, default=200, help='Перекрытие чанков')

    # Команда search
    search_parser = subparsers.add_parser('search', help='Поиск в документации')
    search_parser.add_argument('query', help='Поисковый запрос')
    search_parser.add_argument('--collection', '-c', default='docs', help='Имя коллекции')
    search_parser.add_argument('--top-k', '-k', type=int, default=5, help='Количество чанков')
    search_parser.add_argument('--no-answer', action='store_true', help='Только показать чанки')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == 'index':
        if not args.path.exists():
            print(f"Ошибка: путь '{args.path}' не существует", file=sys.stderr)
            sys.exit(1)
        if not args.path.is_dir():
            print(f"Ошибка: '{args.path}' не является директорией", file=sys.stderr)
            sys.exit(1)
        index_documents(args.path, args.collection, args.chunk_size, args.overlap)

    elif args.command == 'search':
        print(f"Поиск: {args.query}", file=sys.stderr)
        print("Ищу релевантные документы...\n", file=sys.stderr)

        try:
            chunks = search_documents(args.query, args.collection, args.top_k)
        except Exception as e:
            print(f"Ошибка: {e}", file=sys.stderr)
            sys.exit(1)

        if not chunks:
            print("Не найдено релевантных документов", file=sys.stderr)
            sys.exit(0)

        if args.no_answer:
            print("="*70)
            print(f"Найдено {len(chunks)} релевантных чанков:")
            print("="*70 + "\n")
            for i, chunk in enumerate(chunks, 1):
                print(f"{i}. Источник: {chunk['source']} (чанк {chunk['chunk_id']})")
                print(f"   {chunk['content'][:200]}...")
                print()
        else:
            print("Генерирую ответ...\n", file=sys.stderr)
            answer = generate_answer(args.query, chunks)

            print("="*70)
            print("Ответ:")
            print("="*70)
            print(answer)
            print("\n" + "="*70)
            print("Источники:")
            print("="*70)
            sources = set(chunk['source'] for chunk in chunks)
            for source in sources:
                print(f"- {source}")

if __name__ == '__main__':
    main()