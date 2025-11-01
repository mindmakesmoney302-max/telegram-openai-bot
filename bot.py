import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.client.session.aiohttp import AiohttpSession
from aiohttp import TCPConnector

# --- CONFIGURATION SECTION ---

BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"  # Replace with your actual BotFather token

# Option 1: Use a SOCKS5 or HTTPS proxy (recommended in Pakistan)
# You can get free ones temporarily from https://free-proxy-list.net/
# Example: proxy="http://185.104.252.10:3128"
PROXY_URL = "http://your-proxy:port"  # Replace or leave as None if not using

# --- END CONFIGURATION ---

async def main():
    # Create session with proxy and SSL disabled (fixes semaphore timeout)
    connector = TCPConnector(ssl=False)

    if PROXY_URL:
        session = AiohttpSession(connector=connector, proxy=PROXY_URL)
    else:
        session = AiohttpSession(connector=connector)

    bot = Bot(token=BOT_TOKEN, session=session)
    dp = Dispatcher()

    @dp.message()
    async def echo_handler(message: types.Message):
        await message.answer(f"Hello {message.from_user.first_name}! 👋")

    print("🤖 Bot is starting...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

# bot.py -- Aiogram 3.x compatible, robust session handling for different aiogram versions
import os
import logging
import asyncio
from urllib.parse import urlparse

from dotenv import load_dotenv

import aiohttp
from aiohttp_socks import ProxyConnector

from aiogram import Bot, Dispatcher, types
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.filters import Command

from services import get_openai_response
from history import add_message, get_history, clear_history

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
PROXY_URL = os.getenv("PROXY_URL", "").strip()  # e.g. socks5://user:pass@1.2.3.4:1080 or blank

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dp = Dispatcher()

def clear_history_keyboard():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🗑 Clear Chat History", callback_data="clear_history"))
    return kb

@dp.message(Command(commands=["start"]))
async def start_handler(message: types.Message):
    await message.answer(
        "🤖 Hello! I’m your AI chatbot. Send a message and I’ll reply.\n\n"
        "Use the button below to clear chat history.",
        reply_markup=clear_history_keyboard()
    )

@dp.callback_query(lambda c: c.data == "clear_history")
async def clear_history_callback(callback_query: types.CallbackQuery):
    clear_history(callback_query.from_user.id)
    await callback_query.message.edit_text("🗑 Chat history cleared!", reply_markup=clear_history_keyboard())

@dp.message()
async def chat_handler(message: types.Message):
    user_id = message.from_user.id
    user_text = message.text or ""
    add_message(user_id, "user", user_text)
    history = get_history(user_id)

    await message.chat.do("typing")
    response = await get_openai_response(history)
    add_message(user_id, "assistant", response)

    await message.reply(response, reply_markup=clear_history_keyboard())

def build_socks_connector(proxy_url: str):
    # returns aiohttp_socks.ProxyConnector or raises ValueError
    if not proxy_url:
        return None
    # proxy_url assumed valid like socks5://user:pass@host:1080 or socks5://127.0.0.1:1080
    try:
        return ProxyConnector.from_url(proxy_url, rdns=True)
    except Exception as e:
        raise ValueError(f"Invalid PROXY_URL: {e}")

async def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not set in .env")
        return

    connector = None
    if PROXY_URL:
        try:
            connector = build_socks_connector(PROXY_URL)
            logger.info("Using proxy connector for PROXY_URL=%s", PROXY_URL)
        except Exception as e:
            logger.error("%s", e)
            connector = None
            # optionally exit here if proxy is required:
            # return

    # Create aiogram's AiohttpSession correctly depending on connector presence
    aiogram_session = None
    try:
        if connector:
            # create an aiohttp.ClientSession with the connector, then wrap it
            client = aiohttp.ClientSession(connector=connector)
            # pass the client session into AiohttpSession using keyword 'session' (works on common aiogram versions)
            aiogram_session = AiohttpSession(session=client)
            logger.info("Created AiohttpSession using provided aiohttp.ClientSession")
        else:
            # let AiohttpSession create/manage its own aiohttp.ClientSession (no proxy)
            aiogram_session = AiohttpSession()
            logger.info("Created AiohttpSession without explicit connector")
    except TypeError:
        # fallback: try positional arg (some aiogram versions accept the client directly)
        try:
            client = aiohttp.ClientSession(connector=connector) if connector else None
            aiogram_session = AiohttpSession(client) if client else AiohttpSession()
            logger.info("Created AiohttpSession via positional fallback")
        except Exception as e:
            logger.exception("Failed to create AiohttpSession (fallback): %s", e)
            return
    except Exception as e:
        logger.exception("Failed to create AiohttpSession: %s", e)
        return

    # Create bot with aiogram-session (callable)
    bot = Bot(token=BOT_TOKEN, session=aiogram_session)

    try:
        logger.info("Starting polling...")
        await dp.start_polling(bot)
    finally:
        logger.info("Closing session...")
        # close wrapper (which should close underlying client)
        try:
            await aiogram_session.close()
        except Exception:
            pass

if __name__ == "__main__":
    asyncio.run(main())



