import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests
from bs4 import BeautifulSoup
from readability import Document
import google.generativeai as genai

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

def extract_article_text(url: str) -> tuple[str, str]:
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        doc = Document(response.text)
        title = doc.title()
        soup = BeautifulSoup(doc.summary(), 'html.parser')
        text = soup.get_text(separator='\n', strip=True)
        
        return title, text
    except requests.exceptions.Timeout:
        raise Exception("Превышено время ожидания ответа от сервера")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Ошибка при загрузке страницы: {str(e)}")
    except Exception as e:
        raise Exception(f"Ошибка при обработке страницы: {str(e)}")

def chunk_text(text: str, max_length: int = 30000) -> list[str]:
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    words = text.split()
    current_chunk = []
    current_length = 0
    
    for word in words:
        word_length = len(word) + 1
        if current_length + word_length > max_length:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_length = word_length
        else:
            current_chunk.append(word)
            current_length += word_length
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks

def summarize_text(title: str, text: str) -> str:
    chunks = chunk_text(text)
    
    if len(chunks) == 1:
        prompt = f"""Прочитай следующую статью и создай краткое содержание в виде 5 ключевых пунктов.
Каждый пункт должен быть информативным и содержательным.

Заголовок: {title}

Текст статьи:
{text}

Формат ответа:
1. [Первый ключевой пункт]
2. [Второй ключевой пункт]
3. [Третий ключевой пункт]
4. [Четвертый ключевой пункт]
5. [Пятый ключевой пункт]"""
    else:
        summaries = []
        for i, chunk in enumerate(chunks):
            prompt = f"""Кратко изложи основные идеи следующего фрагмента статьи (часть {i+1} из {len(chunks)}):

{chunk}

Выдели 2-3 ключевые мысли."""
            response = model.generate_content(prompt)
            summaries.append(response.text)
        
        combined_summary = '\n\n'.join(summaries)
        prompt = f"""На основе следующих кратких изложений частей статьи "{title}", создай общее краткое содержание в виде 5 ключевых пунктов:

{combined_summary}

Формат ответа:
1. [Первый ключевой пункт]
2. [Второй ключевой пункт]
3. [Третий ключевой пункт]
4. [Четвертый ключевой пункт]
5. [Пятый ключевой пункт]"""
    
    response = model.generate_content(prompt)
    return response.text

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот для создания кратких содержаний статей.\n\n"
        "Отправь мне ссылку на статью, и я создам краткое содержание в 5 пунктах.\n\n"
        "Команды:\n"
        "/start - показать это сообщение\n"
        "/help - помощь"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Как использовать бота:\n\n"
        "1. Отправьте ссылку на статью (начинается с http:// или https://)\n"
        "2. Подождите, пока бот обработает статью\n"
        "3. Получите краткое содержание в 5 пунктах\n\n"
        "Поддерживаются большинство новостных сайтов и блогов.\n"
        "Обработка может занять 10-30 секунд в зависимости от размера статьи."
    )

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if not url.startswith(('http://', 'https://')):
        await update.message.reply_text(
            "Пожалуйста, отправьте корректную ссылку, начинающуюся с http:// или https://"
        )
        return
    
    processing_msg = await update.message.reply_text("⏳ Загружаю и обрабатываю статью...")
    
    try:
        title, text = extract_article_text(url)
        
        if not text or len(text) < 100:
            await processing_msg.edit_text(
                "❌ Не удалось извлечь достаточно текста из статьи. "
                "Возможно, сайт защищен от парсинга или требует авторизацию."
            )
            return
        
        await processing_msg.edit_text("🤖 Создаю краткое содержание...")
        
        summary = summarize_text(title, text)
        response = f"📰 **{title}**\n\n{summary}\n\n🔗 [Читать полностью]({url})"
        
        await processing_msg.edit_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error processing URL {url}: {str(e)}")
        await processing_msg.edit_text(
            f"❌ Произошла ошибка при обработке статьи:\n{str(e)}\n\n"
            "Попробуйте другую ссылку или повторите попытку позже."
        )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Пожалуйста, отправьте ссылку на статью.\n"
        "Используйте /help для получения дополнительной информации."
    )

def main():
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set!")
        return
    
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY not set!")
        return
    
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^https?://'), handle_url))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    logger.info("Bot started!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
