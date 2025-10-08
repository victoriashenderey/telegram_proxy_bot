import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# === Настройки из переменных окружения ===
BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_USER_ID = int(os.environ["ADMIN_USER_ID"])

# Для Render.com
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
PORT = int(os.environ.get("PORT", 10000))

# Автоматическое формирование webhook URL для Render
if RENDER_EXTERNAL_HOSTNAME:
    WEBHOOK_URL = f"https://{RENDER_EXTERNAL_HOSTNAME}/{BOT_TOKEN}"
else:
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "").rstrip("/")

# Хранилище состояний пользователей
user_states = {}
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Напишите сообщение — оно будет отправлено администратору.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Игнорируем служебные сообщения
    if not update.message or not update.message.text:
        return
        
    user = update.effective_user
    user_id = user.id

    if user_id == ADMIN_USER_ID:
        # Админ должен ответить на пересланное сообщение
        if not update.message.reply_to_message:
            await update.message.reply_text("❌ Ответьте на сообщение пользователя, чтобы отправить ответ.")
            return

        # Ищем пользователя по ID сообщения
        target_user_id = None
        for uid, data in user_states.items():
            if data.get("admin_message_id") == update.message.reply_to_message.message_id:
                target_user_id = uid
                break

        if not target_user_id:
            await update.message.reply_text("❌ Не удалось найти пользователя для этого сообщения.")
            return

        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"📨 Ответ от администратора:\n\n{update.message.text}"
            )
            await update.message.reply_text("✅ Ответ отправлен пользователю!")
        except Exception as e:
            logger.error(f"Ошибка отправки админу: {e}")
            await update.message.reply_text("❌ Не удалось отправить сообщение.")

    else:
        # Обычный пользователь — пересылаем админу
        try:
            username = user.username or f"{user.first_name or ''} {user.last_name or ''}".strip()
            user_info = f"👤 От: @{username} (ID: {user_id})"
            message_text = f"{user_info}\n\n💬 Сообщение:\n{update.message.text}"

            sent_message = await context.bot.send_message(
                chat_id=ADMIN_USER_ID,
                text=message_text
            )

            # Сохраняем связь: пользователь → ID сообщения у админа
            user_states[user_id] = {
                "admin_message_id": sent_message.message_id,
                "username": username
            }

            await update.message.reply_text("✅ Ваше сообщение отправлено администратору! Ожидайте ответа.")
            
        except Exception as e:
            logger.error(f"Ошибка пересылки админу: {e}")
            await update.message.reply_text("❌ Произошла ошибка при отправке.")

async def handle_non_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик для не-текстовых сообщений"""
    if update.effective_user and update.effective_user.id != ADMIN_USER_ID:
        await update.message.reply_text("❌ Бот принимает только текстовые сообщения.")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Exception while handling an update: {context.error}")

def main():
    try:
        # Создаем приложение с явным указанием конфигурации
        application = Application.builder().token(BOT_TOKEN).build()

        # Обработчики
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_handler(MessageHandler(filters.ALL & ~filters.TEXT & ~filters.COMMAND, handle_non_text))
        application.add_error_handler(error_handler)

        # Определяем режим запуска
        if RENDER_EXTERNAL_HOSTNAME or WEBHOOK_URL:
            # Production: Render.com
            webhook_url = WEBHOOK_URL if WEBHOOK_URL else f"https://{RENDER_EXTERNAL_HOSTNAME}/{BOT_TOKEN}"
            
            logger.info(f"Starting webhook on port {PORT}: {webhook_url}")
            
            # Запускаем webhook с правильными параметрами
            application.run_webhook(
                listen="0.0.0.0",
                port=PORT,
                url_path=BOT_TOKEN,
                webhook_url=webhook_url,
                secret_token=None,
            )
        else:
            # Локальная разработка
            logger.info("Starting polling locally...")
            application.run_polling(allowed_updates=Update.ALL_TYPES)
            
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise

if __name__ == "__main__":
    main()
