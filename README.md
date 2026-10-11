# 📈 IDX News-Buying Catalyst Telegram Bot

Sistem otomatisasi pemantau keterbukaan informasi dan aksi korporasi Bursa Efek Indonesia (BEI / IDX) yang menyaring 10 katalis positif (*news buying*), menganalisis strategi *entry* & risiko, lalu mengirim notifikasi ke Telegram setiap 2 jam.

---

## 🌟 10 Kategori Katalis yang Dipantau

1. **Dividen Jumbo (Spesial)**: Pembagian dividen interim/final yield tinggi.
2. **Share Buyback**: Rencana atau alokasi dana pembelian kembali saham.
3. **Earning Surprise**: Laporan keuangan kuartalan dengan lonjakan laba bersih signifikan.
4. **Kemenangan Tender / Kontrak Masif**: Perolehan kontrak baru bernilai material.
5. **Masuknya Investor Strategis**: Pembelian saham oleh konglomerat, taipan, atau institusi bonafide.
6. **Regulasi Pemerintah Positif**: Kebijakan sektoral yang menguntungkan emiten (insentif, subsidi, dsb).
7. **Kemitraan Strategis (Joint Venture)**: Kerjasama bisnis dengan entitas global/raksasa industri.
8. **Stock Split**: Pemecahan nilai nominal saham untuk memicu likuiditas ritel.
9. **Rights Issue Premium / Standby Buyer**: HMETD atau private placement dengan pembeli siaga kuat.
10. **Akuisisi & Konsolidasi Bisnis**: Pengambilalihan aset atau merger strategis.

---

## 📲 Format Interaktif Telegram

Pesan yang masuk ke Telegram dibuat **sangat ringkas** agar grup/chat tidak banjir pesan (*spam*). Pengguna dapat mengklik tombol **[📖 Selengkapnya]** untuk membuka rincian rekomendasi, atau **[🔼 Tutup Ringkas]** untuk melipatnya kembali.

### 1. Pesan Ringkas Awal (Default Alert)
```text
🚨 [NEWS BUYING] $BUAH
🏷️ Kategori: Dividen Jumbo (Spesial)
📰 Segar Kumala (BUAH) Setor Dividen Interim Rp10 per Saham

[📖 Selengkapnya]   [🔗 Berita Asli]
```

### 2. Setelah Tombol [📖 Selengkapnya] Diklik
Pesan di Telegram akan otomatis diperluas (*in-place edit*) menampilkan:
```text
📋 DETAIL ANALISIS SAHAM $BUAH
━━━━━━━━━━━━━━━━━━━━
🏷️ Kategori: Dividen Jumbo (Spesial)
📰 Judul: Segar Kumala (BUAH) Setor Dividen Interim Rp10 per Saham
📡 Sumber: IDX Channel

🎯 Sentimen Pasar:
Sangat Bullish (Dividend Hunter Catalyst)

💡 Rekomendasi Masuk (Entry Strategy):
• Skenario Buy on Retest: Tunggu koreksi ke support sebelum Cum Date.
• Skenario Momentum: Masuk saat breakout resistance volume tinggi.

⚠️ Risiko & Mitigasi:
• Waspadai Dividend Trap pasca Ex-Date.
• Pasang Stop Loss ketat di level support terdekat.

🔗 Buka Dokumen / Berita Asli
━━━━━━━━━━━━━━━━━━━━
[🔼 Tutup Ringkas]   [🔗 Berita Asli]
```

```
idx-news-bot/
├── config.py             # Konfigurasi aplikasi & environment variables
├── db.py                 # SQLite deduplikasi berita (mencegah duplikat alert)
├── classifier.py         # Engine filter 10 kategori katalis & deteksi kode saham ($TICKER)
├── analyzer.py           # Engine rekomendasi masuk (entry) & analisis risiko (Hybrid: Rule-based + Gemini AI)
├── telegram_notifier.py  # Pengirim pesan terformat HTML ke Telegram Bot
├── news_fetcher.py       # Penarik berita real-time (IDX Channel, EmitenNews, RSS)
├── main.py               # Main scheduler loop (berjalan setiap 2 jam)
├── requirements.txt      # Dependensi pustaka Python
├── Dockerfile            # Container image untuk deploy di cloud
├── render.yaml           # Blueprint deployment Render
├── .env.example          # Contoh variabel konfigurasi
└── README.md             # Panduan instalasi dan penggunaan
```

---

## 🚀 Panduan Setup Lokal

### 1. Salin Environment Variables
Salin file `.env.example` menjadi `.env`:
```bash
cp .env.example .env
```

Isi variabel di dalam file `.env`:
- `TELEGRAM_BOT_TOKEN`: Dapatkan dari [@BotFather](https://t.me/BotFather) di Telegram.
- `TELEGRAM_CHAT_ID`: ID grup, channel, atau chat pribadi Anda (bisa didapatkan via [@userinfobot](https://t.me/userinfobot) atau channel ID berawalan `-100...`).
- `GEMINI_API_KEY`: *(Opsional)* Dapatkan dari [Google AI Studio](https://aistudio.google.com). Jika dikosongkan, bot otomatis menggunakan sistem analisis berbasis aturan (*Rule-Based Strategy*).
- `FETCH_INTERVAL_SECONDS`: Interval pengecekan (default: `7200` detik = 2 jam).

### 2. Jalankan Bot
```bash
python main.py
```

---

## ☁️ Panduan Deploy ke Render

1. **Push ke GitHub / GitLab**:
   - Inisialisasi git dan upload folder ini ke repositori privat/publik Anda:
     ```bash
     git init
     git add .
     git commit -m "Initial commit IDX News Bot"
     git branch -M main
     git remote add origin <URL_REPO_ANDA>
     git push -u origin main
     ```

2. **Buat Service di Render**:
   - Buka dashboard [Render.com](https://dashboard.render.com).
   - Klik **New +** -> Pilih **Background Worker** (atau **Web Service**).
   - Hubungkan ke repositori GitHub Anda.
   - Pilih **Environment**: `Docker` (akan otomatis membaca `Dockerfile` yang sudah disediakan).

3. **Atur Environment Variables di Render Dashboard**:
   - `TELEGRAM_BOT_TOKEN` : Token bot Telegram Anda
   - `TELEGRAM_CHAT_ID` : ID Chat / Channel Telegram tujuan
   - `GEMINI_API_KEY` : *(Opsional)* API Key Gemini
   - `FETCH_INTERVAL_SECONDS` : `7200`

4. Klik **Deploy Worker**. Sistem akan otomatis berjalan di cloud 24/7 dan mengecek pengumuman setiap 2 jam!
