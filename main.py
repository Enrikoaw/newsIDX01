import asyncio
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CallbackQueryHandler, ContextTypes
from config import TELEGRAM_BOT_TOKEN, FETCH_INTERVAL_SECONDS, RENDER_EXTERNAL_URL
from db import init_db, is_news_processed, mark_news_processed, save_news_detail, get_news_detail
from news_fetcher import get_all_recent_news, fetch_article_body
from classifier import classify_catalyst
from analyzer import analyze_catalyst
from telegram_notifier import send_telegram_alert, format_detail_message, format_summary_message

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("IDXNewsBot")

# Global telegram application instance
tg_app: Application = None

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menangani aksi klik tombol 'Selengkapnya' dan 'Tutup' dari pengguna di Telegram."""
    query = update.callback_query
    await query.answer()

    data = query.data
    if data.startswith("detail_"):
        detail_id = int(data.split("_")[1])
        detail = get_news_detail(detail_id)
        if not detail:
            await query.edit_message_text("Informasi detail tidak ditemukan atau telah kedaluwarsa.")
            return

        detail_text = format_detail_message(detail)
        keyboard = [
            [
                InlineKeyboardButton("🔼 Tutup Ringkas", callback_data=f"collapse_{detail_id}"),
                InlineKeyboardButton("🔗 Berita Asli", url=detail.get("url", "https://www.idx.co.id"))
            ]
        ]
        await query.edit_message_text(
            text=detail_text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard),
            disable_web_page_preview=True
        )

    elif data.startswith("collapse_"):
        detail_id = int(data.split("_")[1])
        detail = get_news_detail(detail_id)
        if not detail:
            return

        summary_text = format_summary_message(detail)
        keyboard = [
            [
                InlineKeyboardButton("📖 Selengkapnya", callback_data=f"detail_{detail_id}"),
                InlineKeyboardButton("🔗 Berita Asli", url=detail.get("url", "https://www.idx.co.id"))
            ]
        ]
        await query.edit_message_text(
            text=summary_text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard),
            disable_web_page_preview=True
        )

async def process_news_pipeline(bot_instance=None):
    """Menjalankan 1 siklus pengecekan, penyaringan, analisis, dan pengiriman notifikasi ringkas."""
    logger.info("Memulai siklus pengecekan keterbukaan informasi emiten BEI...")
    news_list = get_all_recent_news()
    logger.info(f"Total berita ditemukan: {len(news_list)}")

    found_catalysts = 0

    for item in news_list:
        url = item.get("url")
        title = item.get("title", "")

        # 1. Cek apakah berita sudah pernah diproses di DB
        if is_news_processed(url):
            continue

        # 2. Filter tahap pertama: Cek kecocokan 10 kategori katalis
        classification = classify_catalyst(title, item.get("content", ""))
        
        # Jika belum lolos tapi berpotensi, coba ambil body artikel
        if not classification:
            body = fetch_article_body(url, item.get("source", ""))
            classification = classify_catalyst(title, body)
            item["content"] = body
        else:
            if not item.get("content"):
                item["content"] = fetch_article_body(url, item.get("source", ""))

        if not classification:
            # Bukan berita yang memenuhi 10 kriteria news-buying
            mark_news_processed(url, title, "", "NON_CATALYST")
            continue

        category = classification["category"]
        ticker = classification["ticker"]
        found_catalysts += 1

        logger.info(f"🔥 [KATALIS TERDETEKSI] Emiten: ${ticker} | Kategori: {category} | Judul: {title}")

        # 3. Analisis rekomendasi masuk dan profil risiko
        analysis = analyze_catalyst(
            title=title,
            content=item.get("content", ""),
            category=category,
            ticker=ticker
        )

        # Siapkan payload
        payload = {
            "ticker": ticker,
            "category": category,
            "title": title,
            "url": url,
            "source": item.get("source", "BEI"),
            "sentiment": analysis["sentiment"],
            "entry": analysis["entry"],
            "risk": analysis["risk"]
        }

        # Simpan detail lengkap ke database SQLite agar bisa dipanggil saat tombol diklik
        detail_id = save_news_detail(payload)

        # 4. Kirim notifikasi ringkas dengan tombol interaktif ke Telegram
        await send_telegram_alert(payload, detail_id=detail_id, bot_instance=bot_instance)

        # 5. Tandai berita sebagai sudah diproses
        mark_news_processed(url, title, ticker, category)

        # Beri jeda 1 detik antar pengiriman pesan ke Telegram
        await asyncio.sleep(1)

    logger.info(f"Siklus selesai. {found_catalysts} katalis news-buying berhasil diproses dan dikirim.")

async def keep_alive_task():
    """
    Timer anti-tidur Render:
    Melakukan self-ping setiap 10 menit (600 detik) ke URL Render aplikasi
    agar instance Free Tier Render mendeteksi traffic web aktif dan tidak masuk mode sleep/tidur.
    """
    await asyncio.sleep(30) # Tunggu 30 detik pertama hingga server siap
    while True:
        url = RENDER_EXTERNAL_URL
        if url:
            if not url.startswith("http"):
                url = f"https://{url}"
            try:
                import requests
                r = requests.get(url, timeout=10)
                logger.info(f"⏰ [KEEP-ALIVE] Ping ke {url} berhasil (Status: {r.status_code}). Server tetap bangun!")
            except Exception as e:
                logger.warning(f"⏰ [KEEP-ALIVE] Gagal ping: {e}")
        else:
            logger.debug("⏰ [KEEP-ALIVE] RENDER_EXTERNAL_URL belum diset. Disarankan isi di env Render.")

        # Ping setiap 10 menit (Render gratis biasanya tidur setelah 15 menit idle)
        await asyncio.sleep(600)

async def scheduler_task(app: Application):
    """Loop background yang mengecek berita setiap 2 jam secara otomatis."""
    while True:
        try:
            await process_news_pipeline(bot_instance=app.bot)
        except Exception as e:
            logger.error(f"Error pada background scheduler: {e}", exc_info=True)

        logger.info(f"Menunggu {FETCH_INTERVAL_SECONDS} detik untuk siklus berikutnya...")
        await asyncio.sleep(FETCH_INTERVAL_SECONDS)

# --- FASTAPI WEB SERVER (HEALTH CHECK UNTUK RENDER WEB SERVICE) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    global tg_app
    init_db()

    # Jalankan timer anti-tidur Render
    asyncio.create_task(keep_alive_task())

    if TELEGRAM_BOT_TOKEN:
        # Inisialisasi bot Telegram
        tg_app = (
            Application.builder()
            .token(TELEGRAM_BOT_TOKEN)
            .build()
        )
        tg_app.add_handler(CallbackQueryHandler(handle_callback_query))
        
        await tg_app.initialize()
        await tg_app.start()
        # Polling dengan drop_pending_updates agar tidak konflik
        await tg_app.updater.start_polling(drop_pending_updates=True)
        logger.info("Telegram Bot Polling dimulai.")

        # Jalankan background scheduler
        scheduler_job = asyncio.create_task(scheduler_task(tg_app))
    else:
        logger.warning("TELEGRAM_BOT_TOKEN belum diset.")
        scheduler_job = None

    yield

    # Cleanup saat server shutdown
    if tg_app:
        logger.info("Menghentikan Telegram Bot...")
        if scheduler_job:
            scheduler_job.cancel()
        await tg_app.updater.stop()
        await tg_app.stop()
        await tg_app.shutdown()

api_app = FastAPI(title="IDX News Bot API", lifespan=lifespan)

@api_app.get("/")
def health_check():
    return {"status": "ok", "message": "IDX News Catalyst Bot is running 24/7!"}

def main():
    port = int(os.getenv("PORT", "10000"))
    uvicorn.run("main:api_app", host="0.0.0.0", port=port, log_level="info")

if __name__ == "__main__":
    main()
