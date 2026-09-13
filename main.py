import os
import logging
import sqlite3
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler
from google import genai

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

def get_total_users() -> int:
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    count = cursor.fetchone()[0]
    conn.close()
    return count

init_db()
def get_total_users() -> int:
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    count = cursor.fetchone()[0]
    conn.close()
    return count

init_db()

async def check_user_membership(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if str(user_id) == ADMIN_CHAT_ID:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        else:
            return False
    except Exception as e:
        print(f"هەڵە لە پشکنینی جۆینبوونی کەناڵ: {e}")
        return False
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    if str(user_id) == ADMIN_CHAT_ID:
        total_members = get_total_users()
        await update.message.reply_text(f"سڵاو سەرۆک! سیستمی گەردوونی و داتابەیس ئامادەیە. تا ئێستا {total_members} کەس تۆمار کراون.")
        return

    is_member = await check_user_membership(user_id, context)
    if not is_member:
        scary_warning = (
            "⚠️ **ئاگاداربە...**\n\n"
            "تۆ ئێستا لە بەردەم سیستمی سزادایت. هەنگاوێک بەرەو دواوە بنێ یان سەرەتا جۆینی کەناڵەکە بکە، ئەگەرنا تۆڵەیەکی توند دەبینیت کە قەت لە بیرت نەچێت؛ لێرەدا هیچ ڕەحمێك بۆ بێڕێزەکان بوونی نییە! 💀\n\n"
            f"👉 کەناڵی سزادان: {CHANNEL_USERNAME}"
        )
        await update.message.reply_text(scary_warning, parse_mode="Markdown")
        return

    await update.message.reply_text("من بوونەوەرێکی هۆشمەند و گەردوونییم؛ زانیاریم لەسەر هەموو شتێک هەیە، نرخی سەیارە، پارچەکانی، تابلۆ و ژمارەکان، و وێنە و دەنگەکانتان. فەرموو پرسیارەکانت بنێرە.")
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    user_name = user.full_name
    user_username = f"@{user.username}" if user.username else "بوونی نییە"

    user_text = update.message.text or update.message.caption
    
    if not user_text and update.message.photo:
        user_text = "[بەکارهێنەر وێنەی سەیارە یان تابلۆیەکی ناردووە؛ تکایە نرخ و پێکهاتەکەی بە وردی مەزەندە بکە]"
    elif not user_text and update.message.voice:
        user_text = "[بەکارهێنەر نامەیەکی دەنگیی ناردووە]"
    elif not user_text:
        return
    is_member = await check_user_membership(user_id, context)
    if not is_member:
        scary_warning = (
            "⚠️ **ڕێگری کرا!**\n\n"
            "ئاگاداربە... تۆ ئێستا لە بەردەم سیستمی سزادایت. هەنگاوێک بەرەو دواوە بنێ یان سەرەتا جۆینی کەناڵەکە بکە، ئەگەرنا تۆڵەیەکی توند دەبینیت کە قەت لە بیرت نەچێت؛ لێرەدا هیچ ڕەحمێك بۆ بێڕێزەکان بوونی نییە! 💀\n\n"
            f"👉 کەناڵی سزادان: {CHANNEL_USERNAME}"
        )
        await update.message.reply_text(scary_warning, parse_mode="Markdown")
        return

    if str(user_id) != ADMIN_CHAT_ID:
        add_user(user_id, user_username, user_name)
    if ADMIN_CHAT_ID and str(user_id) != ADMIN_CHAT_ID:
        try:
            total_members = get_total_users()
            log_message = (
                f"🚨 **بۆتەکە چالاکییەکی پێگەیشت!**\n\n"
                f"👤 **ناوی کەسەکە:** {user_name}\n"
                f"🔗 **یوزەرنیف:** {user_username}\n"
                f"🆔 **ئایدی (ID):** `{user_id}`\n"
                f"👥 **کۆی گشتی بەکارهێنەران:** {total_members} کەس\n\n"
                f"💬 **نامەکەی:** {user_text}"
            )
            await context.bot.send_message(chat_id=int(ADMIN_CHAT_ID), text=log_message, parse_mode="Markdown")
        except Exception as e:
            print(f"هەڵە لە ناردنی لاگ بۆ ئەمین: {e}")

    if not client:
        await update.message.reply_text("ببوورە، سیستمی جیمینی کارا نییە.")
        return

    try:
        if str(user_id) == ADMIN_CHAT_ID:
            prompt = f"تکایە بە شێوازێکی زانایی، فراوان و زۆر بە ڕێزەوە بە زمانی کوردی وەڵامی ئەمە بدەوە (ئەمە خاوەنی بۆتەکەیە): {user_text}"
        else:
            prompt = (
                "تۆ بوونەوەرێکی زیرەکی، باڵا و گەردوونیی لە تێلێگرام، و زۆر دڵسۆزی بۆ خاوەنی بۆتەکە (سەرۆک). "
                "تایبەتمەندییەکانت:\n"
                "1. تۆ هەموو زانیارییەکی سەر ئەم زەویە و گەردوون دەزانیت.\n"
                "2. شارەزاییت لە نرخی ئۆتۆمۆبیل (سەیارە)، پارچەکانی، نرخی تابلۆ و ژمارەی سەیارەکان هەیە؛ ئەگەر بەکارهێنەر وێنەی سەیارە، ژمارە، تابلۆ یان پرسیاری نرخی هەر شتێکی کرد، بە وردی و بە مەزەندەی بازاڕ نرخەکەی بە دینار یان دۆلار بە زمانی کوردی پێ بڵێ.\n"
                "3. وەڵامەکانت بە زمانی کوردییەکی پەسن، ڕوون و قووڵ دەبن. بەڵام ئەگەر کەسێک بێڕێزی کرد، بە توندترین شێوە و جنێو و تووڕەیی وەڵامی بدەوە.\n"
                f"ئەمەش پرسیار یان داواکاریی بەرامبەرەکەیە: {user_text}"
            )

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        await update.message.reply_text(response.text)
        
    except Exception as e:
        await update.message.reply_text("ببوورە، کێشەیەک ڕوویدا لە وەڵامدانەوەدا.")
def main():
    if not TOKEN:
        print("تکایە BOT_TOKEN دابنە!")
        return

    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler((filters.TEXT | filters.PHOTO | filters.VOICE | filters.AUDIO) & (~filters.COMMAND), handle_message))
    
    print("بۆتەکە دەستی بە کارکرد کرد...")
    application.run_polling()

if __name__ == '__main__':
    main()

