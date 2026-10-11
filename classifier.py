import re
from typing import Dict, Any, Optional

# Definisi 10 Kategori Katalis Berita Positif / News Buying
CATALYST_PATTERNS = {
    "Dividen Jumbo (Spesial)": [
        r"dividen\s+(?:interim|spesial|jumbo|tunai)",
        r"tebar\s+dividen",
        r"bagi(?:kan)?\s+dividen",
        r"dividend\s+payout",
        r"cum\s+date\s+dividen"
    ],
    "Share Buyback": [
        r"buyback\s+saham",
        r"pembelian\s+kembali\s+saham",
        r"beli\s+kembali\s+saham",
        r"alokasi(?:kan)?\s+(?:dana\s+)?buyback",
        r"dana\s+buyback"
    ],
    "Earning Surprise": [
        r"laba(?:\s+bersih)?\s+(?:melonjak|melesat|meroket|tumbuh|naik\s+signifikan|terbang)",
        r"kinerja\s+(?:keuangan\s+)?moncer",
        r"kinerja\s+(?:keuangan\s+)?melesat",
        r"pendapatan\s+(?:melonjak|meroket|tumbuh\s+pesat)",
        r"rekor\s+laba",
        r"balikkan\s+rugi\s+jadi\s+laba"
    ],
    "Kemenangan Tender / Kontrak Masif": [
        r"(?:kantongi|raih|amankan|menangkan|peroleh)\s+kontrak",
        r"kontrak\s+baru\s+rp",
        r"kontrak\s+(?:jumbo|masif|strategis|bernilai)",
        r"menang(?:kan)?\s+tender",
        r"proyek\s+baru\s+senilai"
    ],
    "Masuknya Investor Strategis": [
        r"investor\s+strategis",
        r"masuknya\s+investor",
        r"borong\s+saham",
        r"tambah\s+kepemilikan",
        r"koleksi\s+saham",
        r"akuisisi\s+\d+%\s+saham",
        r"pengendali\s+baru",
        r"taipan|konglomerat"
    ],
    "Regulasi Pemerintah Positif": [
        r"insentif\s+pemerintah",
        r"subsidi\s+(?:pemerintah|kendaraan|energi)",
        r"kebijakan\s+pemerintah\s+untungkan",
        r"regulasi\s+(?:baru\s+dorong|untungkan)",
        r"bebas\s+bea\s+masuk",
        r"relaksasi\s+pajak"
    ],
    "Kemitraan Strategis (Joint Venture)": [
        r"kemitraan\s+strategis",
        r"gandeng\s+(?:raksasa|perusahaan|global)",
        r"kerjasama\s+strategis",
        r"joint\s+venture",
        r"sepakat\s+bentuk\s+usaha\s+patungan",
        r"kolaborasi\s+dengan"
    ],
    "Stock Split": [
        r"stock\s+split",
        r"pemecahan\s+nilai\s+nominal",
        r"pemecahan\s+saham",
        r"rasio\s+stock\s+split"
    ],
    "Rights Issue Premium / Standby Buyer": [
        r"rights\s+issue",
        r"hmetd",
        r"pembeli\s+siaga",
        r"standby\s+buyer",
        r"private\s+placement"
    ],
    "Akuisisi & Konsolidasi Bisnis": [
        r"akuisisi",
        r"ambil\s+alih\s+saham",
        r"pengambilalihan",
        r"caplok\s+(?:perusahaan|saham)",
        r"konsolidasi\s+bisnis",
        r"merger\s+dan\s+akuisisi"
    ]
}

# Daftar kata yang menandakan sentimen negatif (hindari false positive)
NEGATIVE_EXCLUSIONS = [
    r"gagal\s+bayar",
    r"default",
    r"suspensi",
    r"anjlok",
    r"pailit",
    r"rugi\s+membengkak",
    r"delisting",
    r"turun\s+drastis",
    r"pkpu"
]

import os
import json

# Muat kamus pemetaan nama perusahaan ke kode saham 4 huruf jika file tersedia
COMPANY_MAP = {}
map_file = os.path.join(os.path.dirname(__file__), "idx_companies.json")
if os.path.exists(map_file):
    try:
        with open(map_file, "r", encoding="utf-8") as f:
            COMPANY_MAP = json.load(f)
    except Exception as e:
        pass

def extract_ticker(text: str) -> Optional[str]:
    """Ekstraksi kode saham 4 huruf kapital (misal BBRI, TLKM, MAHA) atau melalui pemetaan nama perusahaan."""
    # Jangan deteksi indeks pasar atau istilah umum sebagai ticker saham
    EXCLUDED_CODES = {"IHSG", "LQ45", "IDX30", "KOMPAS100", "BEI", "OJK", "BUMN", "APBN", "PDB", "FED"}
    
    # 1. Cek Pola Kode Langsung: (KODE) atau [KODE]
    matches = re.findall(r'[\(\[]([A-Z]{4})[\)\]]', text)
    for m in matches:
        if m not in EXCLUDED_CODES:
            return m
    
    # 2. Cek Pola kata kapital berjarak: misal "saham PTBA", "emiten BREN"
    match = re.search(r'(?:saham|emiten|kode)\s+([A-Z]{4})\b', text)
    if match and match.group(1) not in EXCLUDED_CODES:
        return match.group(1)
        
    # 3. Cek Pola di awal judul: misal "MAHA Amankan Kontrak..."
    match = re.search(r'^([A-Z]{4})\b', text)
    if match and match.group(1) not in EXCLUDED_CODES:
        return match.group(1)

    # 4. Cek Pemetaan Nama Perusahaan / Alias dari kamus idx_companies.json
    text_lower = text.lower()
    # Urutkan kunci berdasarkan panjang terpanjang ke terpendek agar 'bank bri' dicocokkan sebelum 'bri'
    for name_key, ticker_code in sorted(COMPANY_MAP.items(), key=lambda x: len(x[0]), reverse=True):
        if len(name_key) >= 4:
            pattern = r'\b' + re.escape(name_key) + r'\b'
            if re.search(pattern, text_lower):
                return ticker_code
        
    return None

def classify_catalyst(title: str, content: str = "") -> Optional[Dict[str, Any]]:
    """
    Menganalisis teks judul dan konten untuk memeriksa apakah termasuk dalam salah satu dari 10 kategori.
    Mengembalikan dictionary detail katalis jika cocok, atau None jika bukan katalis.
    """
    full_text = f"{title} {content}".lower()
    
    # Cek apakah ada sentimen negatif fatal
    for neg_pattern in NEGATIVE_EXCLUSIONS:
        if re.search(neg_pattern, full_text):
            # Jika ada kata negatif tapi konteksnya "balikkan rugi", biarkan lolos
            if "balikkan rugi" not in full_text and "dari rugi" not in full_text:
                return None
                
    # Cek 10 kategori
    matched_categories = []
    matched_reasons = []
    
    for category, patterns in CATALYST_PATTERNS.items():
        for pat in patterns:
            found = re.search(pat, full_text)
            if found:
                matched_categories.append(category)
                matched_reasons.append(found.group(0))
                break
                
    if not matched_categories:
        return None
        
    ticker = extract_ticker(title) or extract_ticker(content)
    # HANYA loloskan jika emiten/kode saham 4 huruf terdeteksi jelas
    if not ticker or ticker == "Emiten Terkait":
        return None
    
    return {
        "is_catalyst": True,
        "category": matched_categories[0], # Kategori primer
        "all_categories": matched_categories,
        "ticker": ticker,
        "matched_term": matched_reasons[0]
    }
