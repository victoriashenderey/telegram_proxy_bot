import asyncio
from aiogram import Bot, Dispatcher, types
import json
import os

BOT_TOKEN = "8075176282:AAFMxqX48B5xHQAgwPQ1BQIXFgiDVOOQyb8"
ADMIN_ID = 69241598
FORWARD_MAP_FILE = "forward_map.json"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Загружаем словарь пересылок из файла, если есть
if os.path.exists(FORWARD_MAP_FILE):
    with open(FORWARD_MAP_FILE, "r") as f:
        forward_map = json.load(f)
else:
    forward_map = {}

def save_map():
    with open(FORWARD_MAP_FILE, "w") as f:
        json.dump(forward_map, f)

@dp.message()
async def proxy_message(message: types.Message):
    if message.chat.id != ADMIN_ID:
        # Пересылаем клиенту админу
        forwarded = await bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
        # Сохраняем сопоставление пересланного сообщения -> клиент
        forward_map[str(forwarded.message_id)] = message.chat.id
        save_map()
    else:
        # Ответ админа
        if message.reply_to_message and str(message.reply_to_message.message_id) in forward_map:
            client_id = forward_map[str(message.reply_to_message.message_id)]
            try:
                await bot.send_message(client_id, message.text)
            except Exception as e:
                print(f"Ошибка отправки клиенту: {e}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
