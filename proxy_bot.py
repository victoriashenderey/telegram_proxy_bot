import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройки
BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_USER_ID = int(os.environ["ADMIN_USER_ID"])
WEBHOOK_URL = os.environ["WEBHOOK_URL"]
PORT = int(os.environ.get("PORT", 10000))  # Render использует 10000 по умолчанию

user_message_map = {}
logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Напишите сообщение — оно будет отправлено администратору.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id == ADMIN_USER_ID:
        target = user_message_map.get(ADMIN_USER_ID)
        if not target:
            await update.message.reply_text("Нет активного диалога.")
            return
        # Отправляем админский ответ
        await context.bot.copy_message(chat_id=target, from_chat_id=ADMIN_USER_ID, message_id=update.message.message_id)
        await update.message.reply_text(f"✅ Ответ отправлен {target}.")
    else:
        # Пересылаем сообщение админу
        user_message_map[ADMIN_USER_ID] = user.id
        await context.bot.copy_message(chat_id=ADMIN_USER_ID, from_chat_id=update.effective_chat.id, message_id=update.message.message_id)
        await update.message.reply_text("Ваше сообщение отправлено администратору!")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL,
        secret_token=None,
    )

if __name__ == "__main__":
    main()
