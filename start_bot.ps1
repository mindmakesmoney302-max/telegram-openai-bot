# ===============================
# Telegram + Aiogram + OpenAI Bot
# One-click launch (Windows PowerShell)
# ===============================

# ---- CONFIG ----
# Replace with your real credentials
$BOT_TOKEN = "123456789:AAExxxxxxxxxxxxxxxxxxxxx"
$FALLBACK_PROXY = "socks5://user:pass@host:1080"   # leave "" if no proxy
$OPENAI_API_KEY = "sk-xxxxxxxxxxxxxxxxxxxx"       # optional

# ---- SET ENV VARIABLES ----
$env:BOT_TOKEN = $BOT_TOKEN
$env:FALLBACK_PROXY = $FALLBACK_PROXY
$env:OPENAI_API_KEY = $OPENAI_API_KEY

# ---- START BOT ----
Write-Host "Starting Telegram bot..." -ForegroundColor Cyan
python bot_safe.py
