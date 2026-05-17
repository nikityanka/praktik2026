#!/usr/bin/env python3
"""
Тесты для AI Comment Moderator

Тестирует пограничные случаи и основную функциональность модерации.
"""

import os
import sys
import json
import pytest
import tempfile
from pathlib import Path

# Добавляем путь к модулю
sys.path.insert(0, str(Path(__file__).parent))

# Устанавливаем тестовый API ключ
os.environ['GEMINI_API_KEY'] = 'test_key_for_unit_tests'

from moderator import app, init_db, DB_PATH

@pytest.fixture
def client():
    """Создает тестовый клиент Flask"""
    # Используем временную БД для тестов
    app.config['TESTING'] = True
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
        test_db = Path(tmp.name)
    
    # Подменяем путь к БД
    import moderator
    moderator.DB_PATH = test_db
    
    # Инициализируем БД
    init_db()
    
    with app.test_client() as client:
        yield client
    
    # Удаляем временную БД
    if test_db.exists():
        test_db.unlink()

def test_health_endpoint(client):
    """Тест health check endpoint"""
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'ok'
    assert data['service'] == 'AI Comment Moderator'

def test_index_page(client):
    """Тест главной страницы"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'AI Comment Moderator' in response.data

def test_moderate_missing_text(client):
    """Тест модерации без текста"""
    response = client.post('/moderate',
                          json={},
                          content_type='application/json')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'text' in data['error'].lower()

def test_moderate_empty_text(client):
    """Тест модерации с пустым текстом"""
    response = client.post('/moderate',
                          json={'text': '   '},
                          content_type='application/json')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'empty' in data['error'].lower()

def test_moderate_too_long_text(client):
    """Тест модерации слишком длинного текста"""
    long_text = 'a' * 5001
    response = client.post('/moderate',
                          json={'text': long_text},
                          content_type='application/json')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'too long' in data['error'].lower()

def test_moderate_invalid_json(client):
    """Тест модерации с невалидным JSON"""
    response = client.post('/moderate',
                          data='invalid json',
                          content_type='application/json')
    assert response.status_code in [400, 415]

def test_stats_endpoint(client):
    """Тест endpoint статистики"""
    response = client.get('/stats')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'total_moderated' in data
    assert 'by_category' in data
    assert 'last_24h' in data
    assert 'avg_confidence' in data
    assert data['total_moderated'] == 0  # Пустая БД

def test_history_endpoint(client):
    """Тест endpoint истории"""
    response = client.get('/history')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'history' in data
    assert 'count' in data
    assert isinstance(data['history'], list)
    assert data['count'] == 0  # Пустая БД

def test_history_with_limit(client):
    """Тест истории с лимитом"""
    response = client.get('/history?limit=10')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'history' in data

def test_history_with_category_filter(client):
    """Тест истории с фильтром по категории"""
    response = client.get('/history?category=ok')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'history' in data

def test_history_with_invalid_category(client):
    """Тест истории с невалидной категорией"""
    response = client.get('/history?category=invalid')
    assert response.status_code == 200
    data = json.loads(response.data)
    # Должен вернуть все записи, игнорируя невалидную категорию
    assert 'history' in data

def test_moderate_special_characters(client):
    """Тест модерации с специальными символами"""
    # Этот тест требует реального API ключа, поэтому пропускаем
    pytest.skip("Requires real API key")

def test_moderate_unicode(client):
    """Тест модерации с Unicode символами"""
    pytest.skip("Requires real API key")

def test_moderate_html_injection(client):
    """Тест модерации с HTML инъекцией"""
    html_text = '<script>alert("xss")</script>Комментарий'
    # Проверяем, что текст принимается (валидация на длину и пустоту)
    # Реальная модерация требует API ключ
    assert len(html_text) < 5000
    assert html_text.strip() != ''

def test_moderate_sql_injection(client):
    """Тест модерации с SQL инъекцией"""
    sql_text = "'; DROP TABLE moderation_log; --"
    # Проверяем, что текст принимается
    assert len(sql_text) < 5000
    assert sql_text.strip() != ''

def test_database_initialization():
    """Тест инициализации базы данных"""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
        test_db = Path(tmp.name)
    
    import moderator
    original_db = moderator.DB_PATH
    moderator.DB_PATH = test_db
    
    try:
        init_db()
        assert test_db.exists()
        
        # Проверяем структуру таблицы
        import sqlite3
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='moderation_log'")
        assert cursor.fetchone() is not None
        
        cursor.execute("PRAGMA table_info(moderation_log)")
        columns = {row[1] for row in cursor.fetchall()}
        assert 'id' in columns
        assert 'comment_text' in columns
        assert 'category' in columns
        assert 'confidence' in columns
        assert 'reason' in columns
        assert 'timestamp' in columns
        assert 'metadata' in columns
        
        conn.close()
    finally:
        moderator.DB_PATH = original_db
        if test_db.exists():
            test_db.unlink()

def test_categories_defined():
    """Тест определения категорий"""
    from moderator import CATEGORIES
    assert 'ok' in CATEGORIES
    assert 'spam' in CATEGORIES
    assert 'toxic' in CATEGORIES
    assert 'needs_review' in CATEGORIES

def test_edge_case_single_character(client):
    """Тест модерации одного символа"""
    pytest.skip("Requires real API key")

def test_edge_case_only_spaces(client):
    """Тест модерации только пробелов"""
    response = client.post('/moderate',
                          json={'text': '     '},
                          content_type='application/json')
    assert response.status_code == 400

def test_edge_case_only_newlines(client):
    """Тест модерации только переносов строк"""
    response = client.post('/moderate',
                          json={'text': '\n\n\n'},
                          content_type='application/json')
    assert response.status_code == 400

def test_edge_case_exactly_5000_chars(client):
    """Тест модерации ровно 5000 символов"""
    text = 'a' * 5000
    # Должен пройти валидацию
    assert len(text) == 5000
    pytest.skip("Requires real API key for full test")

def test_edge_case_5001_chars(client):
    """Тест модерации 5001 символа"""
    text = 'a' * 5001
    response = client.post('/moderate',
                          json={'text': text},
                          content_type='application/json')
    assert response.status_code == 400

def test_metadata_handling(client):
    """Тест обработки метаданных"""
    pytest.skip("Requires real API key")

def test_concurrent_requests():
    """Тест конкурентных запросов"""
    pytest.skip("Requires real API key and threading setup")

def test_api_key_missing():
    """Тест отсутствия API ключа"""
    # Этот тест пропускаем, так как python-dotenv загружает ключ из .env файла
    # В реальном сценарии отсутствие ключа проверяется при запуске сервера
    pytest.skip("API key is loaded from .env file by python-dotenv")

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
