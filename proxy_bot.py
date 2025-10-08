import os
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# Получаем настройки из переменных окружения
BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_USER_ID = int(os.environ["ADMIN_USER_ID"])
WEBHOOK_URL = os.environ["WEBHOOK_URL"]  # Например: https://your-bot.onrender.com
PORT = int(os.environ.get("PORT", 8443))

# Хранилище: запоминаем, кому отвечает админ (поддержка одного диалога)
user_message_map = {}

# Логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Напишите сообщение — оно будет отправлено администратору.")

# Обработка всех сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message

    if user.id == ADMIN_USER_ID:
        # Админ отвечает — отправляем последнему пользователю
        target_user_id = user_message_map.get(ADMIN_USER_ID)
        if not target_user_id:
            await message.reply_text("Нет активного диалога. Дождитесь сообщения от пользователя.")
            return

        try:
            # Отправляем текст
            if message.text:
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text=f"📬 Ответ от администратора:\n\n{message.text}"
                )
            # Отправляем фото
            if message.photo:
                await context.bot.send_photo(
                    chat_id=target_user_id,
                    photo=message.photo[-1].file_id,
                    caption="📬 Ответ от администратора (фото)"
                )
            # Отправляем документ
            if message.document:
                await context.bot.send_document(
                    chat_id=target_user_id,
                    document=message.document.file_id,
                    caption="📬 Ответ от администратора (документ)"
                )
            await message.reply_text(f"✅ Ответ отправлен пользователю {target_user_id}.")
        except Exception as e:
            logger.error(f"Ошибка при отправке ответа: {e}")
            await message.reply_text("❌ Не удалось доставить сообщение пользователю.")
    else:
        # Обычный пользователь — пересылаем админу
        user_message_map[ADMIN_USER_ID] = user.id
        try:
            username = user.username or "—"
            text = message.text or ""
            await context.bot.send_message(
                chat_id=ADMIN_USER_ID,
                text=f"📩 Новое сообщение от @{username} (ID: {user.id}):\n\n{text}"
            )
            if message.photo:
                await context.bot.send_photo(
                    chat_id=ADMIN_USER_ID,
                    photo=message.photo[-1].file_id,
                    caption=f"📩 Фото от @{username} (ID: {user.id})"
                )
            if message.document:
                await context.bot.send_document(
                    chat_id=ADMIN_USER_ID,
                    document=message.document.file_id,
                    caption=f"📩 Документ от @{username} (ID: {user.id})"
                )
            await message.reply_text("Ваше сообщение отправлено администратору!")
        except Exception as e:
            logger.error(f"Ошибка пересылки админу: {e}")
            await message.reply_text("Ошибка при отправке сообщения администратору.")

# Запуск бота с webhook
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))

    # Запускаем webhook-сервер
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL,
        url_path="",  # Webhook будет на корневом пути: https://.../
        cert=None,    # Render обеспечивает HTTPS, сертификат не нужен
    )

if __name__ == "__main__":
    main()
