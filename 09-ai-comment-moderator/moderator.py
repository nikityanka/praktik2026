#!/usr/bin/env python3
"""
AI Comment Moderator

API-сервис для модерации комментариев с использованием LLM.
Классифицирует комментарии: ok / spam / toxic / needs_review.
"""

import os
import sys
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
from dotenv import load_dotenv

# Загрузка переменных окружения из .env
load_dotenv()

# Конфигурация
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
DB_PATH = Path('moderation.db')

app = Flask(__name__)

# Категории модерации
CATEGORIES = {
    'ok': 'Комментарий приемлем',
    'spam': 'Спам или реклама',
    'toxic': 'Токсичный контент (оскорбления, угрозы)',
    'needs_review': 'Требует ручной проверки'
}

def init_db():
    """Инициализирует базу данных"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS moderation_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            comment_text TEXT NOT NULL,
            category TEXT NOT NULL,
            confidence REAL,
            reason TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_category ON moderation_log(category)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_timestamp ON moderation_log(timestamp)
    ''')
    
    conn.commit()
    conn.close()

def moderate_comment(text: str) -> Dict:
    """Модерирует комментарий с помощью LLM"""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY не установлен в переменных окружения")
    
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""Проанализируй следующий комментарий и определи, является ли он приемлемым.

Комментарий:
"{text}"

Классифицируй комментарий в одну из категорий:
- ok: Нормальный комментарий, не нарушает правила
- spam: Спам, реклама, бессмысленный текст
- toxic: Токсичный контент (оскорбления, угрозы, ненависть, дискриминация)
- needs_review: Пограничный случай, требует ручной проверки

Верни ответ СТРОГО в JSON формате:
{{
  "category": "ok/spam/toxic/needs_review",
  "confidence": 0.95,
  "reason": "Краткое объяснение решения"
}}

JSON:"""

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
        result = json.loads(json_text.strip())
        
        # Валидация
        if result['category'] not in CATEGORIES:
            result['category'] = 'needs_review'
        
        if 'confidence' not in result:
            result['confidence'] = 0.5
        
        if 'reason' not in result:
            result['reason'] = 'No reason provided'
        
        return result
    
    except json.JSONDecodeError as e:
        # Fallback на needs_review при ошибке парсинга
        return {
            'category': 'needs_review',
            'confidence': 0.0,
            'reason': f'Failed to parse response: {str(e)}'
        }

def log_moderation(comment_text: str, result: Dict, metadata: Optional[Dict] = None):
    """Логирует решение модерации в БД"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO moderation_log (comment_text, category, confidence, reason, metadata)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        comment_text,
        result['category'],
        result.get('confidence', 0.0),
        result.get('reason', ''),
        json.dumps(metadata) if metadata else None
    ))
    
    conn.commit()
    log_id = cursor.lastrowid
    conn.close()
    
    return log_id

@app.route('/')
def index():
    """Главная страница с веб-интерфейсом"""
    return render_template('index.html')

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'service': 'AI Comment Moderator'})

@app.route('/moderate', methods=['POST'])
def moderate():
    """Модерирует комментарий"""
    data = request.get_json()
    
    if not data or 'text' not in data:
        return jsonify({'error': 'Missing "text" field'}), 400
    
    comment_text = data['text'].strip()
    
    if not comment_text:
        return jsonify({'error': 'Comment text is empty'}), 400
    
    if len(comment_text) > 5000:
        return jsonify({'error': 'Comment text too long (max 5000 characters)'}), 400
    
    try:
        # Модерируем комментарий
        result = moderate_comment(comment_text)
        
        # Логируем решение
        metadata = {
            'user_agent': request.headers.get('User-Agent'),
            'ip': request.remote_addr,
            'extra': data.get('metadata', {})
        }
        log_id = log_moderation(comment_text, result, metadata)
        
        # Формируем ответ
        response = {
            'id': log_id,
            'category': result['category'],
            'confidence': result['confidence'],
            'reason': result['reason'],
            'approved': result['category'] == 'ok',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify(response), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/stats', methods=['GET'])
def stats():
    """Возвращает статистику модерации"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Общая статистика
    cursor.execute('SELECT COUNT(*) FROM moderation_log')
    total = cursor.fetchone()[0]
    
    # По категориям
    cursor.execute('''
        SELECT category, COUNT(*) as count
        FROM moderation_log
        GROUP BY category
    ''')
    by_category = {row[0]: row[1] for row in cursor.fetchall()}
    
    # За последние 24 часа
    cursor.execute('''
        SELECT COUNT(*) FROM moderation_log
        WHERE timestamp > datetime('now', '-1 day')
    ''')
    last_24h = cursor.fetchone()[0]
    
    # Средняя уверенность
    cursor.execute('SELECT AVG(confidence) FROM moderation_log')
    avg_confidence = cursor.fetchone()[0] or 0.0
    
    conn.close()
    
    return jsonify({
        'total_moderated': total,
        'by_category': by_category,
        'last_24h': last_24h,
        'avg_confidence': round(avg_confidence, 2)
    })

@app.route('/history', methods=['GET'])
def history():
    """Возвращает историю модерации"""
    limit = request.args.get('limit', 50, type=int)
    category = request.args.get('category')
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if category and category in CATEGORIES:
        cursor.execute('''
            SELECT id, comment_text, category, confidence, reason, timestamp
            FROM moderation_log
            WHERE category = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (category, limit))
    else:
        cursor.execute('''
            SELECT id, comment_text, category, confidence, reason, timestamp
            FROM moderation_log
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    history = []
    for row in rows:
        history.append({
            'id': row[0],
            'text': row[1],
            'category': row[2],
            'confidence': row[3],
            'reason': row[4],
            'timestamp': row[5]
        })
    
    return jsonify({'history': history, 'count': len(history)})

def main():
    """Запуск сервера"""
    # Инициализируем БД
    init_db()
    
    # Проверяем API ключ
    if not GEMINI_API_KEY:
        print("Ошибка: GEMINI_API_KEY не установлен", file=sys.stderr)
        sys.exit(1)
    
    # Запускаем сервер
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'false').lower() == 'true'
    
    print(f"Запуск AI Comment Moderator на порту {port}...")
    print(f"Endpoints:")
    print(f"  POST /moderate - Модерация комментария")
    print(f"  GET  /stats    - Статистика")
    print(f"  GET  /history  - История модерации")
    print(f"  GET  /health   - Health check")
    
    app.run(host='0.0.0.0', port=port, debug=debug)

if __name__ == '__main__':
    main()


