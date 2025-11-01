import os
import asyncio
import ssl
from aiogram import Bot, Dispatcher, types
from aiogram.client.session.aiohttp import AiohttpSession
from openai import AsyncOpenAI

# ====== CONFIG via ENV VARS ======
BOT_TOKEN = os.getenv("BOT_TOKEN")              # set in Render
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")    # set in Render
PROXY_URL = os.getenv("PROXY_URL", None)        # optional; leave None for Render
# ==================================

openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
bot = Bot(token=BOT_TOKEN, session=AiohttpSession(proxy=PROXY_URL))
dp = Dispatcher()

import asyncio
import ssl
from aiogram import Bot, Dispatcher, types
from aiogram.client.session.aiohttp import AiohttpSession
from openai import AsyncOpenAI

BOT_TOKEN = "8274126714:AAHilTOIRtPlGSPQKKsF8eSRKIyrDJBxc_s"
import os
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

PROXY_URL = "socks5://195.2.78.126:443"


import os
import ssl
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.client.session.aiohttp import AiohttpSession
from openai import AsyncOpenAI
from dotenv import load_dotenv
from threading import Thread
from http.server import SimpleHTTPRequestHandler, HTTPServer

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PROXY_URL = os.getenv("PROXY_URL")  # Optional proxy for local testing in Pakistan

openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)


async def main():
    # Create SSL context to avoid certificate issues
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    # Initialize Aiogram session (use proxy if provided)
    if PROXY_URL:
        session = AiohttpSession(proxy=PROXY_URL)
    else:
        session = AiohttpSession()

    bot = Bot(token=BOT_TOKEN, session=session)
    dp = Dispatcher()

    @dp.message()
    async def chat_handler(message: types.Message):
        user_text = message.text.strip()

        if not user_text or user_text.startswith("/"):
            await message.answer("👋 Send me a message and I’ll reply using AI!")
            return

        await message.answer("💭 Thinking...")

        try:
            response = await openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful AI Telegram bot for users in Pakistan."},
                    {"role": "user", "content": user_text},
                ],
            )
            reply = response.choices[0].message.content.strip()
            await message.answer(reply)

        except Exception as e:
            print(f"❌ Error: {e}")
            await message.answer("⚠️ Sorry, something went wrong. Please try again later.")

    print("🤖 Bot is running... Press Ctrl+C to stop.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    # Optional: Keep-alive server for Render or Replit
    def keep_alive():
        server = HTTPServer(('0.0.0.0', 8080), SimpleHTTPRequestHandler)
        server.serve_forever()

    Thread(target=keep_alive, daemon=True).start()

    asyncio.run(main())
import os
import ssl
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.client.session.aiohttp import AiohttpSession
from openai import AsyncOpenAI
from dotenv import load_dotenv
from threading import Thread
from http.server import SimpleHTTPRequestHandler, HTTPServer

# Load .env for local testing
load_dotenv()

# Config (from Render env vars)
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PROXY_URL = os.getenv("PROXY_URL", None)  # not needed on Render; optional for local testing
ASSISTANT_SYSTEM = os.getenv(
    "ASSISTANT_SYSTEM",
    "You are a helpful AI assistant. Answer concisely. If the user writes in Urdu, reply in Urdu; if in English, reply in English."
)

# Basic safety checks
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing. Set BOT_TOKEN in environment variables.")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is missing. Set OPENAI_API_KEY in environment variables.")

openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

def looks_like_urdu(text: str) -> bool:
    """Very small heuristic: detect Arabic script characters commonly used in Urdu."""
    if not text:
        return False
    for ch in text:
        # Arabic block includes Urdu characters; if any character falls into that Unicode range, treat as Urdu
        if '\u0600' <= ch <= '\u06FF' or '\u0750' <= ch <= '\u077F' or '\u08A0' <= ch <= '\u08FF':
            return True
    return False

async def create_openai_reply(user_text: str) -> str:
    """Call OpenAI async chat completion and return reply text."""
    # If Urdu detected, instruct model to respond in Urdu; otherwise English.
    system_msg = ASSISTANT_SYSTEM
    # Extra guidance: keep reply short and user-friendly
    try:
        response = await openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_text},
            ],
            max_tokens=700,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        # bubble up errors so caller can log and inform user
        raise

async def start_bot():
    # SSL context (helps some environments); Aiogram manages connections
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    # Aiogram session: no proxy needed on Render; if PROXY_URL provided, Aiogram will use it
    session = AiohttpSession(proxy=PROXY_URL) if PROXY_URL else AiohttpSession()
    bot = Bot(token=BOT_TOKEN, session=session)
    dp = Dispatcher()

    @dp.message()
    async def handle_message(message: types.Message):
        text = (message.text or "").strip()
        user = message.from_user

        print(f"[IN] {user.id} ({user.username}): {text}")

        if not text:
            await message.answer("⚠️ I didn't receive any text. Please send a message.")
            return

        if text.startswith("/start") or text.startswith("/help"):
            await message.answer("👋 Hello! Send me a message in English or Urdu and I'll reply using AI.")
            return

        await message.answer("💭 Thinking...")

        try:
            # Optional language detection log
            if looks_like_urdu(text):
                print("Detected: Urdu")
            else:
                print("Detected: likely English/other")

            reply = await create_openai_reply(text)
            await message.answer(reply)
            print(f"[OUT] Replied to {user.id}")

        except Exception as e:
            print("OpenAI/send error:", e)
            await message.answer("⚠️ Sorry — an error occurred. Please try again in a moment.")

    print("🤖 Bot is running... Press Ctrl+C to stop.")
    await dp.start_polling(bot)

# Optional simple HTTP server so Render Web Service type remains active.
def keep_alive():
    server = HTTPServer(("0.0.0.0", 8080), SimpleHTTPRequestHandler)
    server.serve_forever()

if __name__ == "__main__":
    # Start small webserver to keep platform happy (ok for Render web service)
    Thread(target=keep_alive, daemon=True).start()
    asyncio.run(start_bot())




