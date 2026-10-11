import sqlite3
import logging
from config import DB_PATH

logger = logging.getLogger(__name__)

def init_db():
    """Inisialisasi tabel SQLite untuk mencatat berita yang sudah diproses dan menyimpan data detail."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processed_news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE,
                title TEXT,
                ticker TEXT,
                category TEXT,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS news_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT,
                category TEXT,
                title TEXT,
                url TEXT,
                source TEXT,
                sentiment TEXT,
                entry_strategy TEXT,
                risk_analysis TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    logger.info("Database SQLite terinisialisasi.")

def is_news_processed(url: str) -> bool:
    """Cek apakah URL berita sudah pernah diproses sebelumnya."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM processed_news WHERE url = ?", (url,))
        return cursor.fetchone() is not None

def mark_news_processed(url: str, title: str, ticker: str, category: str):
    """Tandai berita sebagai sudah diproses."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO processed_news (url, title, ticker, category)
                VALUES (?, ?, ?, ?)
            """, (url, title, ticker, category))
            conn.commit()
    except Exception as e:
        logger.error(f"Gagal menyimpan status berita ke DB: {e}")

def save_news_detail(item: dict) -> int:
    """Simpan detail lengkap berita dan kembalikan ID unik baris database."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO news_details (ticker, category, title, url, source, sentiment, entry_strategy, risk_analysis)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item.get("ticker", ""),
                item.get("category", ""),
                item.get("title", ""),
                item.get("url", ""),
                item.get("source", ""),
                item.get("sentiment", ""),
                item.get("entry", ""),
                item.get("risk", "")
            ))
            conn.commit()
            return cursor.lastrowid
    except Exception as e:
        logger.error(f"Gagal menyimpan detail berita ke DB: {e}")
        return 0

def get_news_detail(detail_id: int) -> dict:
    """Ambil data detail berita berdasarkan ID."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM news_details WHERE id = ?", (detail_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
