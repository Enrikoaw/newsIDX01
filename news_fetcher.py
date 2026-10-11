import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import logging
from typing import List, Dict, Any
from config import DEFAULT_USER_AGENT

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": DEFAULT_USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.idxchannel.com/"
}

def fetch_from_idxchannel() -> List[Dict[str, Any]]:
    """
    Mengambil berita keterbukaan informasi dan aksi korporasi resmi 
    eksklusif HANYA dari IDX Channel (Kanal Resmi Bursa Efek Indonesia / BEI).
    """
    items = []
    # Mengambil dari halaman Market News utama dan pagination untuk menangkap seluruh rilis terbaru
    urls = [
        "https://www.idxchannel.com/market-news",
        "https://www.idxchannel.com/market-news/2"
    ]
    seen_links = set()
    
    for url in urls:
        try:
            r = requests.get(url, headers=HEADERS, timeout=12)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    if "/market-news/" in href and href not in seen_links:
                        title = a.get_text(strip=True)
                        if len(title) > 25 and not title.startswith("http"):
                            seen_links.add(href)
                            full_link = href if href.startswith("http") else f"https://www.idxchannel.com{href}"
                            items.append({
                                "title": title,
                                "url": full_link,
                                "content": "",
                                "source": "IDX (Bursa Efek Indonesia)"
                            })
        except Exception as e:
            logger.error(f"Error fetching from IDX Channel ({url}): {e}")
            
    return items

def fetch_article_body(url: str, source: str = "") -> str:
    """Mengambil paragraf detail isi berita dari IDX Channel."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=8)
        if r.status_code != 200:
            return ""
        soup = BeautifulSoup(r.text, "html.parser")
        
        container = (
            soup.find("div", class_="article--content") or 
            soup.find("div", class_="detail--article") or 
            soup.find("div", class_="detail-content")
        )
        if container:
            return container.get_text(" ", strip=True)[:1500]
                
        paragraphs = [p.get_text(strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 30]
        return " ".join(paragraphs[:5])[:1500]
    except Exception as e:
        logger.debug(f"Gagal mengambil isi detail {url}: {e}")
        return ""

def get_all_recent_news() -> List[Dict[str, Any]]:
    """
    Mengambil berita eksklusif HANYA dari Bursa Efek Indonesia (BEI / IDX).
    Sumber eksternal selain BEI tidak digunakan.
    """
    idx_items = fetch_from_idxchannel()
    logger.info(f"Diperoleh {len(idx_items)} berita eksklusif dari IDX (Bursa Efek Indonesia).")
    return idx_items
