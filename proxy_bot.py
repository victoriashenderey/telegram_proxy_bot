import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_USER_ID = int(os.environ["ADMIN_USER_ID"])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

user_chats = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Напишите сообщение для администратора")

async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_USER_ID:
        return
    
    user_chats[user_id] = update.effective_chat.id
    
    await context.bot.send_message(
        chat_id=ADMIN_USER_ID,
        text=f"Сообщение от {user_id}:\n{update.message.text}"
    )
    await update.message.reply_text("✅ Отправлено!")

async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_USER_ID:
        return
        
    if update.message.reply_to_message:
        reply_text = update.message.reply_to_message.text
        if "Сообщение от" in reply_text:
            try:
                user_id = int(reply_text.split("Сообщение от ")[1].split(":")[0])
                await context.bot.send_message(
                    chat_id=user_chats.get(user_id, user_id),
                    text=f"📨 Ответ:\n{update.message.text}"
                )
                await update.message.reply_text("✅ Ответ отправлен!")
            except Exception as e:
                await update.message.reply_text("❌ Ошибка")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_message))
    
    # Для Render
    if 'RENDER_EXTERNAL_HOSTNAME' in os.environ:
        hostname = os.environ['RENDER_EXTERNAL_HOSTNAME']
        port = int(os.environ.get('PORT', 10000))
        
        app.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=BOT_TOKEN,
            webhook_url=f"https://{hostname}/{BOT_TOKEN}"
        )
    else:
        # Локально
        app.run_polling()

if __name__ == "__main__":
    main()
