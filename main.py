import os
import logging
import sqlite3
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler
from google import genai

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = "
GEMINI_API_KEY = "
GEMINI_MODEL = "gemini-2.5-flash"
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
            full_name TEXT,
            points INTEGER DEFAULT 0,
            first_seen TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            message_text TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def add_user(user_id: int, username: str, full_name: str):
    if str(user_id) == ADMIN_CHAT_ID:
        return
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (user_id, username, full_name, points, first_seen) VALUES (?, ?, ?, 0, ?)', 
                   (user_id, username, full_name, datetime.now()))
    conn.commit()
    conn.close()

def update_user_points(user_id: int, amount: int):
    if str(user_id) == ADMIN_CHAT_ID:
        return
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET points = points + ? WHERE user_id = ?', (amount, user_id))
    conn.commit()
    conn.close()

def save_message_to_db(user_id: int, text: str):
    if str(user_id) == ADMIN_CHAT_ID:
        return
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO user_messages (user_id, message_text) VALUES (?, ?)', (user_id, text))
    conn.commit()
    conn.close()

def get_user_messages_last_24h(user_id: int) -> str:
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    yesterday = datetime.now() - timedelta(days=1)
    cursor.execute('SELECT message_text, timestamp FROM user_messages WHERE user_id = ? AND timestamp >= ?', (user_id, yesterday))
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return "Hiç qse w nameyek la 24 katzhmireda nabuwa."
    
    messages_list = []
    for r in rows:
        messages_list.append(f"[{r[1]}] {r[0]}")
    return "\n".join(messages_list)

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
        print(f"Error checking membership: {e}")
        return False

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    if str(user_id) == ADMIN_CHAT_ID:
        await update.message.reply_text("Silaw Sarok! Sistemi taybati xot karaya.")
        return

    is_member = await check_user_membership(user_id, context)
    if not is_member:
        scary_warning = (
            "⚠️ **Agadarba...**\n\n"
            "To esta la bardam sistemi szadayt. Sarata joyni kanalaka bka!\n\n"
            f"👉 Kanal: {CHANNEL_USERNAME}"
        )
        await update.message.reply_text(scary_warning, parse_mode="Markdown")
        return

    await update.message.reply_text("Min bunewarێکی hoshmandm; farmu prsyarakant nira.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    user_name = user.full_name
    user_username = f"@{user.username}" if user.username else "Buni niya"

    user_text = update.message.text or update.message.caption

    if not user_text and update.message.photo:
        user_text = "[Wena]"
    elif not user_text and update.message.voice:
        user_text = "[Dangi]"
    elif not user_text:
        user_text = "[ Fayl ]"

    if str(user_id) == ADMIN_CHAT_ID:
        if update.message.forward_origin:
            forwarded = update.message.forward_origin
            if hasattr(forwarded, 'sender_user') and forwarded.sender_user:
                target_user = forwarded.sender_user
                t_id = target_user.id
                t_name = target_user.full_name
                t_username = f"@{target_user.username}" if target_user.username else "Buni niya"
                
                messages_history = get_user_messages_last_24h(t_id)
                
                report_text = (
                    f"👑 **Zanyari taybat bo Sarok:**\n\n"
                    f"👤 **Naw:** {t_name}\n"
                    f"🔗 Username: {t_username}\n"
                    f"🆔 ID: `{t_id}`\n\n"
                    f"💬 **Namakani 24 katzhmiri rabrdu:**\n{messages_history}"
                )
                
                try:
                    photos = await context.bot.get_user_profile_photos(t_id, limit=1)
                    if photos.total_count > 0:
                        file_id = photos.photos[0][-1].file_id
                        await context.bot.send_photo(chat_id=int(ADMIN_CHAT_ID), photo=file_id, caption=report_text, parse_mode="Markdown")
                    else:
                        report_text += "\n\n⚠️ *(Rasmi profile-i niya)*"
                        await context.bot.send_message(chat_id=int(ADMIN_CHAT_ID), text=report_text, parse_mode="Markdown")
                except Exception as e:
                    await context.bot.send_message(chat_id=int(ADMIN_CHAT_ID), text=report_text + f"\n\nError: {e}", parse_mode="Markdown")
                return

        if not client:
            return
        try:
            prompt = f"Walami amay ba zmani kurdi dada bawa (Ama xawani botaka - Sarok): {user_text}"
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
            )
            await update.message.reply_text(response.text)
        except Exception as e:
            print(f"Error: {e}")
            await update.message.reply_text("Bbuura Sarok, kishayak ruwida.")
        return

    is_member = await check_user_membership(user_id, context)
    if not is_member:
        await update.message.reply_text(f"Sarata joyni kanal bka: {CHANNEL_USERNAME}")
        return

    add_user(user_id, user_username, user_name)
    save_message_to_db(user_id, user_text)
    update_user_points(user_id, 1)

    notification_text = (
        f"🚨 **Bakarhenerik nama nard:**\n\n"
        f"👤 **Naw:** {user_name}\n"
        f"🔗 Username: {user_username}\n"
        f"🆔 ID: `{user_id}`\n\n"
        f"💬 **Nama:** {user_text}"
    )
    try:
        photos = await context.bot.get_user_profile_photos(user_id, limit=1)
        if photos.total_count > 0:
            file_id = photos.photos[0][-1].file_id
            await context.bot.send_photo(chat_id=int(ADMIN_CHAT_ID), photo=file_id, caption=notification_text, parse_mode="Markdown")
        else:
            notification_text += "\n\n⚠️ *(Rasmi profile-i niya)*"
            await context.bot.send_message(chat_id=int(ADMIN_CHAT_ID), text=notification_text, parse_mode="Markdown")
    except Exception as e:
        print(f"Error: {e}")

    if not client:
        return

    try:
        prompt = f"Answer this question in Kurdish clearly: {user_text}"
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )
        await update.message.reply_text(response.text)
    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text("Bbuura, kishayak ruwida.")

def main():
    if not TOKEN:
        print("Token is missing!")
        return

    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), handle_message))
    
    print("Bot is running successfully...")
    application.run_polling()

if __name__ == '__main__':
    main()
