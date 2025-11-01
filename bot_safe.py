import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.client.bot import DefaultBotProperties
from aiohttp import TCPConnector
from aiohttp_socks import ProxyConnector
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
PROXY = os.getenv("FALLBACK_PROXY")

# Use proxy if set, else IPv4
if PROXY:
    connector = ProxyConnector.from_url(PROXY)
else:
    connector = TCPConnector(family=2)

# Initialize bot
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML"),
    connector=connector
)
dp = Dispatcher()

# Example command handler
@dp.message()
async def echo(message: types.Message):
    await message.reply(f"You said: {message.text}")

async def main():
    print("Starting bot...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())

