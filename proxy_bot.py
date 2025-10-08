import asyncio
from aiogram import Bot, Dispatcher, types

BOT_TOKEN = "8075176282:AAFMxqX48B5xHQAgwPQ1BQIXFgiDVOOQyb8"
ADMIN_ID = 69241598

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Словарь для сопоставления сообщений
# ключ: id пересланного сообщения админу
# значение: id клиента
forward_map = {}

@dp.message()
async def proxy_message(message: types.Message):
    if message.chat.id != ADMIN_ID:
        # Пересылаем клиенту админу
        forwarded = await bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
        # Запоминаем, какой клиент за каким сообщением
        forward_map[forwarded.message_id] = message.chat.id
    else:
        # Если админ отвечает на пересланное сообщение
        if message.reply_to_message and message.reply_to_message.message_id in forward_map:
            client_id = forward_map[message.reply_to_message.message_id]
            await bot.send_message(client_id, message.text)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
