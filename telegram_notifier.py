import html
from typing import Dict, Any
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from db import get_news_detail
import logging
import sys

logger = logging.getLogger(__name__)

def format_summary_message(item: Dict[str, Any]) -> str:
    """Format pesan ringkas: hanya nama emiten, kategori, dan judul singkat."""
    ticker = html.escape(item.get("ticker", "IDX"))
    category = html.escape(item.get("category", "Keterbukaan Informasi"))
    title = html.escape(item.get("title", ""))

    msg = f"""🚨 <b>[NEWS BUYING]</b> <code>${ticker}</code>
🏷️ <b>Kategori:</b> {category}
📰 {title}"""
    return msg

def format_detail_message(item: Dict[str, Any]) -> str:
    """Format pesan lengkap yang ditampilkan ketika tombol 'Selengkapnya' diklik."""
    ticker = html.escape(item.get("ticker", "IDX"))
    category = html.escape(item.get("category", "Keterbukaan Informasi"))
    title = html.escape(item.get("title", ""))
    url = item.get("url", "https://www.idx.co.id")
    sentiment = html.escape(item.get("sentiment", "Bullish"))
    entry = html.escape(item.get("entry_strategy", item.get("entry", "")))
    risk = html.escape(item.get("risk_analysis", item.get("risk", "")))
    source = html.escape(item.get("source", "BEI Portal"))

    msg = f"""📋 <b>DETAIL ANALISIS SAHAM</b> <code>${ticker}</code>
━━━━━━━━━━━━━━━━━━━━
🏷️ <b>Kategori:</b> <i>{category}</i>
📰 <b>Judul:</b> {title}
📡 <b>Sumber:</b> {source}

🎯 <b>Sentimen Pasar:</b>
{sentiment}

💡 <b>Rekomendasi Masuk (Entry Strategy):</b>
{entry}

⚠️ <b>Risiko & Mitigasi:</b>
{risk}

🔗 <a href="{url}">Buka Dokumen / Berita Asli</a>
━━━━━━━━━━━━━━━━━━━━"""
    return msg

async def send_telegram_alert(item: Dict[str, Any], detail_id: int, bot_instance: Bot = None) -> bool:
    """Mengirim pesan ringkas dengan tombol Inline Keyboard 'Selengkapnya'."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("TELEGRAM_BOT_TOKEN atau TELEGRAM_CHAT_ID belum diisi di .env. Simulasi pesan:")
        print("="*50)
        sys.stdout.buffer.write(format_summary_message(item).encode("utf-8", errors="replace") + b"\n")
        print(f"[Tombol: [📖 Selengkapnya | callback: detail_{detail_id}]]")
        print("="*50)
        return False

    try:
        bot = bot_instance or Bot(token=TELEGRAM_BOT_TOKEN)
        text = format_summary_message(item)
        
        keyboard = [
            [
                InlineKeyboardButton("📖 Selengkapnya", callback_data=f"detail_{detail_id}"),
                InlineKeyboardButton("🔗 Berita Asli", url=item.get("url", "https://www.idx.co.id"))
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
        logger.info(f"Berhasil mengirim ringkasan emiten ${item.get('ticker')}")
        return True
    except Exception as e:
        logger.error(f"Gagal mengirim pesan ringkas Telegram: {e}")
        return False
