import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_USER_ID = int(os.environ["ADMIN_USER_ID"])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Простое хранилище в памяти
user_chats = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Напишите сообщение для администратора")

async def forward_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_USER_ID:
        return
    
    # Сохраняем chat_id пользователя
    user_chats[user_id] = update.effective_chat.id
    
    # Пересылаем сообщение админу
    await context.bot.send_message(
        chat_id=ADMIN_USER_ID,
        text=f"Сообщение от {user_id}:\n\n{update.message.text}"
    )
    await update.message.reply_text("Сообщение отправлено!")

async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_USER_ID:
        return
        
    if not update.message.reply_to_message:
        await update.message.reply_text("Ответьте на сообщение пользователя")
        return
        
    # Ищем пользователя по тексту сообщения
    reply_text = update.message.reply_to_message.text
    if "Сообщение от" in reply_text:
        try:
            user_id = int(reply_text.split("Сообщение от ")[1].split(":")[0])
            await context.bot.send_message(
                chat_id=user_chats.get(user_id, user_id),
                text=f"Ответ администратора:\n{update.message.text}"
            )
            await update.message.reply_text("Ответ отправлен!")
        except:
            await update.message.reply_text("Ошибка отправки")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_to_admin))
    app.add_handler(MessageHandler(filters.TEXT & filters.REPLY, admin_reply))
    
    # Для Render
    if "RENDER" in os.environ:
        app.run_webhook(
            listen="0.0.0.0",
            port=int(os.environ.get("PORT", 10000)),
            url_path=BOT_TOKEN,
            webhook_url=f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/{BOT_TOKEN}"
        )
    else:
        app.run_polling()

if __name__ == "__main__":
    main()
