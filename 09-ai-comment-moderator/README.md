# AI Comment Moderator

API-сервис для автоматической модерации комментариев с использованием LLM. Классифицирует комментарии как ok, spam, toxic или needs_review с логированием решений в SQLite.

## Возможности

- REST API для модерации комментариев
- Классификация: ok / spam / toxic / needs_review
- Оценка уверенности (confidence score)
- Логирование всех решений в SQLite
- Статистика модерации
- История решений с фильтрацией
- Health check endpoint
- Легкое развертывание

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

4. (Опционально) Настройте порт и режим отладки:
```bash
export PORT=5000
export DEBUG=false
```

## Получение API ключа

1. Перейдите на https://aistudio.google.com
2. Войдите с помощью Google аккаунта
3. Нажмите "Get API Key"
4. Создайте новый ключ и скопируйте его

## Запуск

```bash
python moderator.py
```

Сервер запустится на `http://localhost:5000`

## API Endpoints

### POST /moderate

Модерирует комментарий.

**Request:**
```json
{
  "text": "Текст комментария для модерации",
  "metadata": {
    "user_id": "123",
    "post_id": "456"
  }
}
```

**Response:**
```json
{
  "id": 1,
  "category": "ok",
  "confidence": 0.95,
  "reason": "Комментарий содержит конструктивную критику",
  "approved": true,
  "timestamp": "2026-05-06T10:30:00.000Z"
}
```

**Категории:**
- `ok` - Комментарий приемлем
- `spam` - Спам или реклама
- `toxic` - Токсичный контент (оскорбления, угрозы)
- `needs_review` - Требует ручной проверки

### GET /stats

Возвращает статистику модерации.

**Response:**
```json
{
  "total_moderated": 1523,
  "by_category": {
    "ok": 1200,
    "spam": 150,
    "toxic": 100,
    "needs_review": 73
  },
  "last_24h": 245,
  "avg_confidence": 0.87
}
```

### GET /history

Возвращает историю модерации.

**Query Parameters:**
- `limit` - Количество записей (по умолчанию: 50)
- `category` - Фильтр по категории (ok/spam/toxic/needs_review)

**Examples:**
```bash
GET /history?limit=10
GET /history?category=toxic&limit=20
```

**Response:**
```json
{
  "history": [
    {
      "id": 1,
      "text": "Отличная статья!",
      "category": "ok",
      "confidence": 0.98,
      "reason": "Позитивный комментарий",
      "timestamp": "2026-05-06T10:30:00"
    }
  ],
  "count": 1
}
```

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "service": "AI Comment Moderator"
}
```

## Примеры использования

### cURL

```bash
# Модерация комментария
curl -X POST http://localhost:5000/moderate \
  -H "Content-Type: application/json" \
  -d '{"text": "Отличная статья, спасибо!"}'

# Получить статистику
curl http://localhost:5000/stats

# Получить историю
curl http://localhost:5000/history?limit=10

# Health check
curl http://localhost:5000/health
```

### Python

```python
import requests

# Модерация комментария
response = requests.post('http://localhost:5000/moderate', json={
    'text': 'Отличная статья, спасибо!',
    'metadata': {
        'user_id': '123',
        'post_id': '456'
    }
})

result = response.json()
print(f"Категория: {result['category']}")
print(f"Одобрен: {result['approved']}")
print(f"Уверенность: {result['confidence']}")
print(f"Причина: {result['reason']}")
```

### JavaScript

```javascript
// Модерация комментария
fetch('http://localhost:5000/moderate', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    text: 'Отличная статья, спасибо!',
    metadata: {
      user_id: '123',
      post_id: '456'
    }
  })
})
.then(response => response.json())
.then(data => {
  console.log('Категория:', data.category);
  console.log('Одобрен:', data.approved);
  console.log('Уверенность:', data.confidence);
  console.log('Причина:', data.reason);
});
```

## Примеры модерации

### Пример 1: Нормальный комментарий

**Request:**
```json
{
  "text": "Отличная статья! Очень полезная информация, спасибо автору."
}
```

**Response:**
```json
{
  "id": 1,
  "category": "ok",
  "confidence": 0.98,
  "reason": "Позитивный конструктивный комментарий",
  "approved": true,
  "timestamp": "2026-05-06T10:30:00.000Z"
}
```

### Пример 2: Спам

**Request:**
```json
{
  "text": "ЗАРАБОТАЙ 1000000 РУБ БЕЗ ВЛОЖЕНИЙ!!! ПЕРЕХОДИ ПО ССЫЛКЕ!!!"
}
```

**Response:**
```json
{
  "id": 2,
  "category": "spam",
  "confidence": 0.99,
  "reason": "Рекламный текст с призывом к действию и ссылкой",
  "approved": false,
  "timestamp": "2026-05-06T10:31:00.000Z"
}
```

### Пример 3: Токсичный контент

**Request:**
```json
{
  "text": "Автор идиот, статья полная чушь!"
}
```

**Response:**
```json
{
  "id": 3,
  "category": "toxic",
  "confidence": 0.95,
  "reason": "Содержит оскорбления и агрессивный тон",
  "approved": false,
  "timestamp": "2026-05-06T10:32:00.000Z"
}
```

### Пример 4: Требует проверки

**Request:**
```json
{
  "text": "Не согласен с автором. Есть другие исследования на эту тему."
}
```

**Response:**
```json
{
  "id": 4,
  "category": "needs_review",
  "confidence": 0.65,
  "reason": "Критика без оскорблений, но может требовать контекста",
  "approved": false,
  "timestamp": "2026-05-06T10:33:00.000Z"
}
```

## Интеграция

### Express.js (Node.js)

```javascript
const express = require('express');
const axios = require('axios');

const app = express();
app.use(express.json());

app.post('/api/comments', async (req, res) => {
  const { text, userId, postId } = req.body;
  
  // Модерация комментария
  const moderation = await axios.post('http://localhost:5000/moderate', {
    text: text,
    metadata: { user_id: userId, post_id: postId }
  });
  
  if (moderation.data.approved) {
    // Сохраняем комментарий
    await saveComment(text, userId, postId);
    res.json({ success: true, message: 'Комментарий опубликован' });
  } else {
    res.status(400).json({
      success: false,
      message: 'Комментарий отклонен',
      reason: moderation.data.reason
    });
  }
});
```

### Django (Python)

```python
from django.http import JsonResponse
import requests

def create_comment(request):
    text = request.POST.get('text')
    user_id = request.user.id
    post_id = request.POST.get('post_id')
    
    # Модерация комментария
    response = requests.post('http://localhost:5000/moderate', json={
        'text': text,
        'metadata': {
            'user_id': user_id,
            'post_id': post_id
        }
    })
    
    result = response.json()
    
    if result['approved']:
        # Сохраняем комментарий
        Comment.objects.create(
            text=text,
            user_id=user_id,
            post_id=post_id
        )
        return JsonResponse({'success': True})
    else:
        return JsonResponse({
            'success': False,
            'reason': result['reason']
        }, status=400)
```

### WordPress Plugin

```php
<?php
function moderate_comment_before_save($commentdata) {
    $comment_text = $commentdata['comment_content'];
    
    // Вызов API модерации
    $response = wp_remote_post('http://localhost:5000/moderate', array(
        'headers' => array('Content-Type' => 'application/json'),
        'body' => json_encode(array(
            'text' => $comment_text,
            'metadata' => array(
                'post_id' => $commentdata['comment_post_ID'],
                'author' => $commentdata['comment_author']
            )
        ))
    ));
    
    $result = json_decode(wp_remote_retrieve_body($response), true);
    
    if (!$result['approved']) {
        wp_die('Ваш комментарий не прошел модерацию: ' . $result['reason']);
    }
    
    return $commentdata;
}

add_filter('preprocess_comment', 'moderate_comment_before_save');
```

## База данных

Структура таблицы `moderation_log`:

| Поле | Тип | Описание |
|------|-----|----------|
| id | INTEGER | Уникальный ID |
| comment_text | TEXT | Текст комментария |
| category | TEXT | Категория (ok/spam/toxic/needs_review) |
| confidence | REAL | Уверенность (0.0-1.0) |
| reason | TEXT | Причина решения |
| timestamp | DATETIME | Время модерации |
| metadata | TEXT | Дополнительные данные (JSON) |

## Развертывание

### Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY moderator.py .

ENV GEMINI_API_KEY=""
ENV PORT=5000

EXPOSE 5000

CMD ["python", "moderator.py"]
```

```bash
# Сборка
docker build -t ai-moderator .

# Запуск
docker run -p 5000:5000 -e GEMINI_API_KEY=your_key ai-moderator
```

### Systemd Service

```ini
[Unit]
Description=AI Comment Moderator
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/ai-moderator
Environment="GEMINI_API_KEY=your_key"
Environment="PORT=5000"
ExecStart=/usr/bin/python3 /opt/ai-moderator/moderator.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## Производительность

- **Время ответа**: 1-3 секунды на комментарий
- **Пропускная способность**: ~20-30 запросов/минуту (ограничено API)
- **База данных**: SQLite (для production рекомендуется PostgreSQL)

## Ограничения

- Google AI Studio (Gemini): ~1500 запросов/день
- Максимальная длина комментария: 5000 символов
- SQLite не подходит для высоконагруженных систем
- Требуется интернет-соединение для работы с API

## Рекомендации

### Для production

1. Используйте PostgreSQL вместо SQLite
2. Добавьте кэширование (Redis)
3. Настройте rate limiting
4. Используйте очереди для асинхронной обработки
5. Добавьте мониторинг и алертинг
6. Настройте HTTPS
7. Добавьте аутентификацию API

### Настройка порогов

Можно настроить автоматическое одобрение на основе confidence:

```python
if result['category'] == 'ok' and result['confidence'] > 0.9:
    # Автоматически одобрить
    approve_comment()
elif result['category'] == 'needs_review' or result['confidence'] < 0.7:
    # Отправить на ручную проверку
    queue_for_review()
else:
    # Отклонить
    reject_comment()
```

## Лицензия

MIT
