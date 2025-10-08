import asyncio
from aiogram import Bot, Dispatcher, types

BOT_TOKEN = "8075176282:AAFMxqX48B5xHQAgwPQ1BQIXFgiDVOOQyb8"  # твой токен
ADMIN_ID = 69241598  # твой Telegram ID

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message()
async def proxy_message(message: types.Message):
    if message.chat.id != ADMIN_ID:
        await bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
    else:
        if message.reply_to_message and message.reply_to_message.forward_from:
            user_id = message.reply_to_message.forward_from.id
            await bot.send_message(user_id, message.text)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
