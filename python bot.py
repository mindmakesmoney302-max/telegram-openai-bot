
# bot.py — robust Aiogram 3.x bot with defensive session/proxy handling
import os
import logging
import asyncio
from urllib.parse import urlparse

from dotenv import load_dotenv

import aiohttp
from aiohttp_socks import ProxyConnector  # installed earlier

from aiogram import Bot, Dispatcher, types
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.filters import Command

from services import get_openai_response
from history import add_message, get_history, clear_history

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
PROXY_URL = os.getenv("PROXY_URL", "").strip()  # set blank to disable proxy

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

# Build aiohttp_socks connector from PROXY_URL or return None
def build_proxy_connector(proxy_url: str):
    if not proxy_url:
        return None
    try:
        return ProxyConnector.from_url(proxy_url, rdns=True)
    except Exception as e:
        raise ValueError(f"Invalid PROXY_URL '{proxy_url}': {e}")

async def create_aiogram_session(connector):
    """
    Create AiohttpSession in a way that works across aiogram versions:
      - If AiohttpSession accepts connector=..., use that
      - Else create raw aiohttp.ClientSession(connector=...) and pass as session=...
      - Else try positional fallback
    Returns (aiogram_session, underlying_client_if_created_or_None)
    """
    # Try to pass connector directly (some aiogram versions accept connector kw)
    try:
        logger.debug("Trying AiohttpSession(connector=connector)")
        s = AiohttpSession(connector=connector)
        logger.info("Using AiohttpSession(connector=...)")
        return s, None
    except TypeError as e:
        logger.debug("AiohttpSession(connector=...) not supported: %s", e)
    except Exception as e:
        logger.debug("AiohttpSession(connector=...) failed: %s", e)

    # Try to build a raw aiohttp.ClientSession with connector and pass as session=...
    client = None
    try:
        if connector:
            client = aiohttp.ClientSession(connector=connector)
        else:
            client = aiohttp.ClientSession()
        try:
            logger.debug("Trying AiohttpSession(session=client)")
            s = AiohttpSession(session=client)
            logger.info("Using AiohttpSession(session=client)")
            return s, client
        except TypeError as e:
            logger.debug("AiohttpSession(session=...) not supported: %s", e)
        except Exception as e:
            logger.debug("AiohttpSession(session=...) failed: %s", e)
    except Exception as e:
        logger.debug("Failed to create raw aiohttp.ClientSession: %s", e)

    # Try positional fallback: pass client/session positionally
    try:
        if client:
            logger.debug("Trying AiohttpSession(client) positional fallback")
            s = AiohttpSession(client)
            logger.info("Using AiohttpSession(client) positional fallback")
            return s, client
    except Exception as e:
        logger.debug("Positional fallback failed: %s", e)

    # Last resort: let AiohttpSession create internal session (no proxy)
    try:
        logger.debug("Trying AiohttpSession() default (no connector)")
        s = AiohttpSession()
        logger.info("Using AiohttpSession() default")
        # if we created a client earlier but cannot use it, close it
        if client:
            await client.close()
        return s, None
    except Exception as e:
        logger.exception("All attempts to create AiohttpSession failed: %s", e)
        if client:
            await client.close()
        raise RuntimeError("Unable to create aiogram AiohttpSession") from e

async def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN is not set in .env. Please add your Telegram bot token.")
        return

    connector = None
    if PROXY_URL:
        try:
            connector = build_proxy_connector(PROXY_URL)
            logger.info("Proxy connector created from PROXY_URL")
        except Exception as e:
            logger.error("Bad PROXY_URL: %s", e)
            connector = None
            # You can choose to return here if proxy is required:
            # return

    aiogram_session = None
    underlying_client = None
    try:
        aiogram_session, underlying_client = await create_aiogram_session(connector)
    except Exception as e:
        logger.exception("Failed to create aiogram session: %s", e)
        return

    # Create bot with the wrapper session (callable)
    bot = Bot(token=BOT_TOKEN, session=aiogram_session)

    try:
        logger.info("Starting polling...")
        await dp.start_polling(bot)
    finally:
        logger.info("Shutting down sessions...")
        try:
            await aiogram_session.close()
        except Exception:
            pass
        # ensure underlying client closed if we created it explicitly
        try:
            if underlying_client:
                await underlying_client.close()
        except Exception:
            pass

if __name__ == "__main__":
    asyncio.run(main())
