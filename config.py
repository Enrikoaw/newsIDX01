import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Settings
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Gemini AI Settings (Optional for enhanced deep reasoning)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Scheduler Interval (dalam detik, default: 2 jam = 7200 detik)
FETCH_INTERVAL_SECONDS = int(os.getenv("FETCH_INTERVAL_SECONDS", "7200"))

# Database path
DB_PATH = os.getenv("DB_PATH", "idx_news.db")

# User Agent for HTTP requests
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

# Render External URL (otomatis disediakan Render jika diset, atau diset manual untuk self-ping)
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL", "")

