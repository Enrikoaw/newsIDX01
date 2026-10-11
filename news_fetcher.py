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
    [SUMBER UTAMA] Mengambil berita keterbukaan informasi dan aksi korporasi resmi 
    dari IDX Channel (Kanal Resmi Bursa Efek Indonesia / BEI).
    """
    items = []
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

def fetch_from_backup_rss() -> List[Dict[str, Any]]:
    """
    [SUMBER SEKUNDER / BACKUP] Mengambil berita aksi korporasi & pasar modal
    dari Kontan Investasi RSS Feed sebagai cadangan jika rilis di kanal utama terlambat.
    """
    items = []
    url = "https://investasi.kontan.co.id/rss"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            root = ET.fromstring(r.content)
            for item in root.findall(".//item")[:25]:
                title_elem = item.find("title")
                link_elem = item.find("link")
                desc_elem = item.find("description")
                
                title = title_elem.text.strip() if title_elem is not None and title_elem.text else ""
                link = link_elem.text.strip() if link_elem is not None and link_elem.text else ""
                desc = desc_elem.text.strip() if desc_elem is not None and desc_elem.text else ""
                
                if title and link:
                    items.append({
                        "title": title,
                        "url": link,
                        "content": desc,
                        "source": "Kontan Pasar Modal (Backup)"
                    })
    except Exception as e:
        logger.warning(f"Gagal mengambil RSS backup Kontan: {e}")
    return items

def fetch_article_body(url: str, source: str = "") -> str:
    """Mengambil paragraf detail isi berita dari URL sumber."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=8)
        if r.status_code != 200:
            return ""
        soup = BeautifulSoup(r.text, "html.parser")
        
        container = (
            soup.find("div", class_="article--content") or 
            soup.find("div", class_="detail--article") or 
            soup.find("div", class_="detail-content") or
            soup.find("div", class_="content-container") or
            soup.find("div", class_="tmpt-desk-kon")
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
    Mengumpulkan seluruh berita keterbukaan dan aksi korporasi:
    1. Sumber Utama: Kanal Resmi BEI (IDX Channel)
    2. Sumber Sekunder: Kontan Investasi RSS Feed
    """
    all_news = []
    
    # 1. Sumber Utama: BEI
    idx_items = fetch_from_idxchannel()
    logger.info(f"Diperoleh {len(idx_items)} berita dari Kanal Resmi BEI.")
    all_news.extend(idx_items)

    # 2. Sumber Sekunder / Backup: Kontan Investasi RSS
    backup_items = fetch_from_backup_rss()
    logger.info(f"Diperoleh {len(backup_items)} berita dari Sumber Backup Kontan.")
    all_news.extend(backup_items)

    return all_news
