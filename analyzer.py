from typing import Dict, Any
from config import GEMINI_API_KEY
import logging

logger = logging.getLogger(__name__)

# Fallback template berbasis aturan jika Gemini API Key belum diisi
DEFAULT_STRATEGIES = {
    "Dividen Jumbo (Spesial)": {
        "sentiment": "Sangat Bullish (Dividend Hunter Catalyst)",
        "entry": (
            "• Skenario Buy on Retest: Tunggu koreksi sehat ke support terdekat sebelum Cum Date.\n"
            "• Skenario Momentum: Masuk saat breakout resistance dengan volume di atas MA20.\n"
            "• Hindari mengejar harga jika sudah gap up >7% di open market."
        ),
        "risk": (
            "• Waspadai 'Dividend Trap' pasca Ex-Date (penurunan harga sebesar/melebihi nilai dividen).\n"
            "• Pastikan payout ratio masuk akal dan tidak menguras kas operasional perusahaan.\n"
            "• Pasang Stop Loss ketat di bawah support 1-2 minggu terakhir."
        )
    },
    "Share Buyback": {
        "sentiment": "Bullish (Manajemen Menilai Saham Undervalued)",
        "entry": (
            "• Skenario Swing/Accumulate: Cicil beli di area support harga rata-rata historis.\n"
            "• Buy on Breakout: Masuk saat harga menembus MA50/MA200 diiringi lonjakan volume transaksi."
        ),
        "risk": (
            "• Realisasi buyback membutuhkan waktu berbulan-bulan, bukan instan.\n"
            "• Jika kondisi makro/IHSG sedang downtrend kuat, aksi buyback bisa tertahan.\n"
            "• Batasi alokasi modal maksimal 10-15% per posisi."
        )
    },
    "Earning Surprise": {
        "sentiment": "Sangat Bullish (Fundamental Re-rating)",
        "entry": (
            "• Skenario Day Trade: Masuk saat pre-opening / awal sesi jika volume ledakan valid.\n"
            "• Skenario Swing: Tunggu retest support pertama pasca lonjakan laporan keuangan."
        ),
        "risk": (
            "• 'Sell on News': Risiko profit taking cepat dari institusi yang sudah akumulasi duluan.\n"
            "• Periksa apakah laba melonjak karena operasional inti atau hanya keuntungan non-operasional/kurs sekali jalan.\n"
            "• Set trailing stop dinamis untuk mengunci profit."
        )
    },
    "Kemenangan Tender / Kontrak Masif": {
        "sentiment": "Bullish (Peningkatan Arus Kas Masa Depan)",
        "entry": (
            "• Skenario Breakout: Buy on High Volume saat menembus level sideways.\n"
            "• Skenario Retest: Tunggu pembentukan higher low di timeframe 1 Jam."
        ),
        "risk": (
            "• Risiko keterlambatan eksekusi proyek atau pembengkakan biaya (cost overrun).\n"
            "• Margin laba kontrak proyek belum tentu setinggi ekspektasi pasar.\n"
            "• Disiplin Cut Loss jika harga breakdown di bawah level breakout candle."
        )
    },
    "Masuknya Investor Strategis": {
        "sentiment": "Sangat Bullish (Smart Money / Credibility Boost)",
        "entry": (
            "• Skenario Follow the Smart Money: Ikuti arah akumulasi di harga dekat harga transaksi investor strategis.\n"
            "• Buy on Consolidation: Masuk saat saham berkonsolidasi di rentang sempit."
        ),
        "risk": (
            "• Volatilitas tinggi karena spekulasi ritel jangka pendek.\n"
            "• Cek potensi lock-up period saham pengendali.\n"
            "• Jangan all-in pada saham dengan free-float terlalu tipis."
        )
    },
    "Regulasi Pemerintah Positif": {
        "sentiment": "Bullish Sektoral",
        "entry": (
            "• Skenario Sector Rotation: Masuk ke saham pemimpin sektor (leader) bukan saham laggard.\n"
            "• Beli saat harga mulai rebound dari moving average utama."
        ),
        "risk": (
            "• Implementasi aturan birokrasi sering memakan waktu lebih lama dari perkiraan.\n"
            "• Resiko perubahan kebijakan lanjutan dari kementerian terkait."
        )
    },
    "Kemitraan Strategis (Joint Venture)": {
        "sentiment": "Bullish (Sinergi Bisnis Global/Regional)",
        "entry": (
            "• Skenario Akumulasi: Masuk bertahap di area sideways bawah.\n"
            "• Beli saat konfirmasi golden cross indikator MACD / Stochastic."
        ),
        "risk": (
            "• Dampak profitabilitas baru terasa 1-3 tahun ke depan.\n"
            "• Euphoria berita cepat pudar jika tidak ada milestone berkala."
        )
    },
    "Stock Split": {
        "sentiment": "Bullish Jangka Pendek (Peningkatan Likuiditas Ritel)",
        "entry": (
            "• Beli 1-2 minggu menjelang tanggal efektif pemecahan saham.\n"
            "• Ambil posisi swing hingga hari pertama perdagangan nominal baru."
        ),
        "risk": (
            "• Stock split tidak mengubah nilai intrinsik/fundamental perusahaan sama sekali.\n"
            "• Rawan aksi taking profit tepat pada hari pertama perdagangan dengan harga baru."
        )
    },
    "Rights Issue Premium / Standby Buyer": {
        "sentiment": "Bullish Bersyarat (Tergantung Harga Pelaksanaan & Standby Buyer)",
        "entry": (
            "• Masuk jika harga pasar saat ini berada di bawah harga tebus / pelaksanaan (exercise price).\n"
            "• Manfaatkan momentum pergerakan harga menuju harga pelaksanaan."
        ),
        "risk": (
            "• Efek dilusi kepemilikan saham jika investor ritel tidak ikut menebus HMETD.\n"
            "• Hindari jika standby buyer tidak jelas atau harga tebus jauh di bawah harga pasar."
        )
    },
    "Akuisisi & Konsolidasi Bisnis": {
        "sentiment": "Sangat Bullish (Ekspansi Skala Pasar)",
        "entry": (
            "• Buy on Breakout: Masuk saat volume melonjak menembus level tertinggi mingguan.\n"
            "• Beli saat emiten target memiliki sinergi laba yang jelas."
        ),
        "risk": (
            "• Risiko integrasi bisnis baru dan penambahan beban utang financing akuisisi.\n"
            "• Batasi risiko dengan alokasi modal proporsional."
        )
    }
}

def analyze_catalyst(title: str, content: str, category: str, ticker: str) -> Dict[str, str]:
    """
    Menghasilkan analisis News Buying, Rekomendasi Masuk, dan Analisis Risiko.
    Jika GEMINI_API_KEY tersedia, gunakan AI untuk analisis mendalam konteks spesifik.
    Jika tidak, gunakan strategi berbasis aturan yang teruji dan cepat.
    """
    # 1. Coba gunakan Gemini API jika key tersedia
    if GEMINI_API_KEY:
        try:
            from google import genai
            client = genai.Client(api_key=GEMINI_API_KEY)
            
            prompt = f"""
Anda adalah analis ekuitas profesional Bursa Efek Indonesia (BEI / IDX) spesialis strategi News-Buying & Catalyst Trading.
Analisis pengumuman berikut:

Judul: {title}
Kategori: {category}
Emiten: {ticker}
Ringkasan Berita: {content[:1000]}

Berikan output dalam format JSON persis seperti berikut:
{{
  "sentiment": "Bullish / Sangat Bullish dengan alasan 1 kalimat",
  "entry_recommendation": "Poin-poin skenario masuk (Buy on Breakout / Retest / Support) yang konkret dan terukur untuk trader",
  "risk_analysis": "Poin-poin risiko utama yang harus diwaspadai (misal: dividend trap, sell on news, gap down, dll) beserta level mitigasi stop loss"
}}
Hanya kirimkan JSON valid tanpa markdown formatting.
"""
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt
            )
            import json
            text_resp = response.text.strip()
            if text_resp.startswith("```"):
                text_resp = text_resp.strip("`").replace("json\n", "").strip()
            data = json.loads(text_resp)
            return {
                "sentiment": data.get("sentiment", "Bullish"),
                "entry": data.get("entry_recommendation", ""),
                "risk": data.get("risk_analysis", "")
            }
        except Exception as e:
            logger.warning(f"Gagal memanggil Gemini API ({e}), beralih ke analisis berbasis aturan.")

    # 2. Fallback: Gunakan Rule-based Engine yang sudah dirancang khusus
    strategy = DEFAULT_STRATEGIES.get(category, {
        "sentiment": "Positif / News Buying Catalyst",
        "entry": "• Beli saat breakout konfirmasi volume di atas rata-rata.\n• Tunggu pembentukan support baru sebelum entry besar.",
        "risk": "• Selalu tentukan batas Stop Loss maksimal 3-5% dari harga beli.\n• Waspadai volatilitas pasar saham menyeluruh."
    })
    
    return {
        "sentiment": strategy["sentiment"],
        "entry": strategy["entry"],
        "risk": strategy["risk"]
    }
