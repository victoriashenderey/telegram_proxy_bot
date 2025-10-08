import os
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# === Настройки из переменных окружения ===
BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_USER_ID = int(os.environ["ADMIN_USER_ID"])

# Для Render.com
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
PORT = int(os.environ.get("PORT", 10000))

# Хранилище состояний пользователей
user_states = {}
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Привет! Напишите сообщение — оно будет отправлено администратору.")

def handle_message(update: Update, context: CallbackContext):
    if not update.message or not update.message.text:
        return
        
    user = update.effective_user
    user_id = user.id

    if user_id == ADMIN_USER_ID:
        # Админ должен ответить на пересланное сообщение
        if not update.message.reply_to_message:
            update.message.reply_text("❌ Ответьте на сообщение пользователя, чтобы отправить ответ.")
            return

        # Ищем пользователя по ID сообщения
        target_user_id = None
        for uid, data in user_states.items():
            if data.get("admin_message_id") == update.message.reply_to_message.message_id:
                target_user_id = uid
                break

        if not target_user_id:
            update.message.reply_text("❌ Не удалось найти пользователя для этого сообщения.")
            return

        try:
            context.bot.send_message(
                chat_id=target_user_id,
                text=f"📨 Ответ от администратора:\n\n{update.message.text}"
            )
            update.message.reply_text("✅ Ответ отправлен пользователю!")
        except Exception as e:
            logger.error(f"Ошибка отправки: {e}")
            update.message.reply_text("❌ Не удалось отправить сообщение.")

    else:
        # Обычный пользователь — пересылаем админу
        try:
            username = user.username or f"{user.first_name or ''} {user.last_name or ''}".strip()
            user_info = f"👤 От: @{username} (ID: {user_id})"
            message_text = f"{user_info}\n\n💬 Сообщение:\n{update.message.text}"

            sent_message = context.bot.send_message(
                chat_id=ADMIN_USER_ID,
                text=message_text
            )

            # Сохраняем связь: пользователь → ID сообщения у админа
            user_states[user_id] = {
                "admin_message_id": sent_message.message_id,
                "username": username
            }

            update.message.reply_text("✅ Ваше сообщение отправлено администратору! Ожидайте ответа.")
            
        except Exception as e:
            logger.error(f"Ошибка пересылки админу: {e}")
            update.message.reply_text("❌ Произошла ошибка при отправке.")

def handle_non_text(update: Update, context: CallbackContext):
    """Обработчик для не-текстовых сообщений"""
    if update.effective_user and update.effective_user.id != ADMIN_USER_ID:
        update.message.reply_text("❌ Бот принимает только текстовые сообщения.")

def error_handler(update: Update, context: CallbackContext):
    logger.error(f"Exception while handling an update: {context.error}")

def main():
    try:
        # Используем Updater для версии 13.15
        updater = Updater(BOT_TOKEN, use_context=True)
        dispatcher = updater.dispatcher

        # Обработчики
        dispatcher.add_handler(CommandHandler("start", start))
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
        dispatcher.add_handler(MessageHandler(Filters.all & ~Filters.text & ~Filters.command, handle_non_text))
        dispatcher.add_error_handler(error_handler)

        # Определяем режим запуска
        if RENDER_EXTERNAL_HOSTNAME:
            # Production: Render.com с webhook
            webhook_url = f"https://{RENDER_EXTERNAL_HOSTNAME}/{BOT_TOKEN}"
            
            logger.info(f"Starting webhook on port {PORT}: {webhook_url}")
            
            updater.start_webhook(
                listen="0.0.0.0",
                port=PORT,
                url_path=BOT_TOKEN,
                webhook_url=webhook_url
            )
            logger.info("Webhook started successfully!")
        else:
            # Локальная разработка с polling
            logger.info("Starting polling locally...")
            updater.start_polling()
            logger.info("Polling started successfully!")
            
        updater.idle()
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise

if __name__ == "__main__":
    main()
