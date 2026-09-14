import os
import logging
import sqlite3
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from google import genai
from gtts import gTTS

# ڕێکخستنی لاگین (Logging)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ADMIN_CHAT_ID = "5523037776"
CHANNEL_USERNAME = "@The_Penalty_System"

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

def init_db():
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_user(user_id: int, username: str, full_name: str):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (user_id, username, full_name) VALUES (?, ?, ?)',
                   (user_id, username, full_name))
    conn.commit()
    conn.close()

init_db()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id, user.username, user.full_name)
    
    welcome_message = (
        f"سڵاو {user.full_name}!\n"
        f"بەخێربێیت بۆ بۆتی ئەرکان. دەتوانیت هەر پرسیارێک یان نامەیەکت هەبێت بنێریت، یان وێنەیەکم بۆ بنێریت!"
    )
    await update.message.reply_text(welcome_message)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message_text = update.message.text
    
    add_user(user.id, user.username, user.full_name)
    
    # ئامادەکردنی زانیاریەکانی بەکارهێنەر بۆ بەڕێوەبەر (وەک شێوازی تابلۆی ناو و ئایدی)
    admin_log = (
        f"📩 نامەیەکی نوێ:\n"
        f"👤 ناو: {user.full_name}\n"
        f"🔗 یوزەرنەیب: @{user.username if user.username else 'نییە'}\n"
        f"🆔 ئایدی: {user.id}\n"
        f"💬 دەق: {message_text}"
    )
    
    # ناردنی وێنەی پرۆفایلی بەکارهێنەر بۆ بەڕێوەبەر (ئەگەر هەبێت)
    try:
        photos = await context.bot.get_user_profile_photos(user.id, limit=1)
        if photos.total_count > 0:
            file_id = photos.photos[0][-1].file_id
            await context.bot.send_photo(
                chat_id=ADMIN_CHAT_ID,
                photo=file_id,
                caption=admin_log
            )
        else:
            await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_log)
    except Exception as e:
        # ئەگەر کێشەیەک هەبوو لە وێنەکە، تەنها تێکستەکە بنێرە
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_log)
    
    # وەڵامدانەوە بە یارمەتی جیمینای و دروستکردنی دەنگ بۆ بەکارهێنەر
    if client:
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=message_text,
            )
            reply_text = response.text
            
            await update.message.reply_text(reply_text)
            
            # دروستکردنی دەنگ بە gTTS
            tts = gTTS(text=reply_text, lang='en')
            voice_path = "response.mp3"
            tts.save(voice_path)
            
            with open(voice_path, 'rb') as voice:
                await update.message.reply_voice(voice=voice)
                
            if os.path.exists(voice_path):
                os.remove(voice_path)
                
        except Exception as e:
            await update.message.reply_text("ببوورە، کێشەیەک ڕویدا لە وەڵامدانەوەدا.")
    else:
        await update.message.reply_text("بۆتەکە لە ئێستادا کلیلی جیمینای نییە.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id, user.username, user.full_name)
    
    photo = update.message.photo[-1]
    file_id = photo.file_id
    
    caption_text = (
        f"📸 وێنەیەکی نوێ نێردرا:\n"
        f"👤 ناو: {user.full_name}\n"
        f"🔗 یوزەرنەیب: @{user.username if user.username else 'نییە'}\n"
        f"🆔 ئایدی: {user.id}"
    )
    
    # ناردنی وێنەکە بۆ بەڕێوەبەر لەگەڵ زانیارییەکان
    await context.bot.send_photo(
        chat_id=ADMIN_CHAT_ID,
        photo=file_id,
        caption=caption_text
    )
    
    await update.message.reply_text("وێنەکەت بە سەرکەوتوویی گەیشت و بۆ بەڕێوەبەر نێردرا! سوپاس.")

def main():
    if not TOKEN:
        print("Error: BOT_TOKEN is not set.")
        return
        
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    print("بۆتی ئەرکان دەستی بە کارکردن کرد...")
    application.run_polling()

if __name__ == '__main__':
    main()

