#!/usr/bin/env python3
"""
Bug Screenshot Analyzer - Telegram Bot

Telegram-бот для анализа скриншотов ошибок.
Пользователь отправляет изображение, бот анализирует и возвращает описание проблемы.
"""

import os
import logging
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai
from io import BytesIO
from dotenv import load_dotenv

# Загружаем .env из папки со скриптом
load_dotenv(dotenv_path=Path(__file__).parent / '.env')

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Инициализация Gemini API
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text(
        "👋 Привет! Я бот для анализа скриншотов ошибок.\n\n"
        "Отправь мне скриншот ошибки (терминал, IDE, браузер), "
        "и я опишу проблему и предложу решение.\n\n"
        "Команды:\n"
        "/start - показать это сообщение\n"
        "/help - помощь"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    await update.message.reply_text(
        "📖 Как использовать бота:\n\n"
        "1. Сделайте скриншот ошибки\n"
        "2. Отправьте изображение боту\n"
        "3. Опционально: добавьте описание к фото\n"
        "4. Получите анализ проблемы и шаги решения\n\n"
        "Поддерживаются скриншоты:\n"
        "• Терминала (ошибки компиляции, runtime)\n"
        "• IDE (синтаксические ошибки)\n"
        "• Браузера (JavaScript ошибки, 404, 500)\n"
        "• Приложений (UI баги, краши)\n\n"
        "Анализ занимает 10-20 секунд."
    )

async def analyze_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик изображений"""
    # Получаем изображение
    photo = update.message.photo[-1]  # Берем самое большое разрешение
    
    # Получаем caption если есть
    caption = update.message.caption or ""
    
    # Отправляем сообщение о начале обработки
    processing_msg = await update.message.reply_text("🔍 Анализирую скриншот...")
    
    try:
        # Скачиваем изображение
        file = await photo.get_file()
        image_bytes = BytesIO()
        await file.download_to_memory(image_bytes)
        image_data = image_bytes.getvalue()
        
        await processing_msg.edit_text("🤖 Анализирую ошибку с помощью AI...")
        
        # Формируем промпт
        context_text = f"\n\nКонтекст от пользователя: {caption}" if caption else ""
        
        prompt = f"""Проанализируй этот скриншот ошибки и предоставь краткий анализ.

{context_text}

Формат ответа:

🔴 **Проблема**
[Краткое описание ошибки]

📋 **Категория**
[Тип ошибки: синтаксическая, runtime, сеть, UI, конфигурация, и т.д.]

💡 **Возможные причины**
• [Причина 1]
• [Причина 2]
• [Причина 3]

✅ **Решение**
1. [Шаг 1]
2. [Шаг 2]
3. [Шаг 3]

⚠️ **Рекомендации**
[Советы по предотвращению]

Будь конкретным и кратким. Используй эмодзи для структурирования."""

        # Отправляем запрос к Gemini
        response = model.generate_content([
            prompt,
            {'mime_type': 'image/jpeg', 'data': image_data}
        ])
        
        analysis = response.text
        
        # Отправляем результат
        await processing_msg.edit_text(analysis, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error analyzing image: {str(e)}")
        await processing_msg.edit_text(
            f"❌ Произошла ошибка при анализе:\n{str(e)}\n\n"
            "Попробуйте:\n"
            "• Отправить более четкий скриншот\n"
            "• Убедиться, что текст ошибки читаем\n"
            "• Повторить попытку позже"
        )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    await update.message.reply_text(
        "Пожалуйста, отправьте скриншот ошибки.\n"
        "Используйте /help для получения дополнительной информации."
    )

def main():
    """Запуск бота"""
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set!")
        return
    
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY not set!")
        return
    
    # Создаем приложение
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.PHOTO, analyze_image))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # Запускаем бота
    logger.info("Bot started!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()


