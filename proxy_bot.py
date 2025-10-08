import os
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_USER_ID = int(os.environ["ADMIN_USER_ID"])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

user_chats = {}

def start(update, context):
    update.message.reply_text("Напишите сообщение для администратора")

def handle_message(update, context):
    user_id = update.effective_user.id
    
    if user_id == ADMIN_USER_ID:
        # Админ отвечает
        if update.message.reply_to_message:
            reply_text = update.message.reply_to_message.text
            if "От пользователя" in reply_text:
                try:
                    lines = reply_text.split('\n')
                    user_id = int(lines[0].split('ID: ')[1])
                    context.bot.send_message(
                        chat_id=user_id,
                        text=f"Ответ от администратора:\n{update.message.text}"
                    )
                    update.message.reply_text("✅ Ответ отправлен!")
                except:
                    update.message.reply_text("❌ Ошибка")
        return
    
    # Пользователь пишет
    user_chats[user_id] = update.effective_chat.id
    
    context.bot.send_message(
        chat_id=ADMIN_USER_ID,
        text=f"От пользователя:\nID: {user_id}\nИмя: {update.effective_user.first_name}\n\nСообщение:\n{update.message.text}"
    )
    update.message.reply_text("✅ Сообщение отправлено администратору!")

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    
    # Webhook для Render
    updater.start_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get('PORT', 10000)),
        url_path=BOT_TOKEN,
        webhook_url=f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/{BOT_TOKEN}"
    )
    
    updater.idle()

if __name__ == "__main__":
    main()
