import requests
from bs4 import BeautifulSoup
import re
import time
import os
import threading
from flask import Flask

# --- WEB SERVER SEDERHANA AGAR GRATIS DI RENDER ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Monitor Harga Aktif!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- KONFIGURASI BOT ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID_TUJUAN = os.getenv("CHAT_ID_TUJUAN")

URL_DTY = "http://www.sunsirs.com/uk/prodetail-1017.html"
URL_RAYON = "http://www.sunsirs.com/uk/prodetail-87.html"

INTERVAL_DETIK = 86400  # Pengecekan setiap 24 Jam

def fetch_price(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        price_tag = soup.find('span', {'class': 'price'}) or soup.find('td', {'class': 'gp-price'})
        if price_tag:
            clean_price = re.sub(r'[^\d.]', '', price_tag.text.strip())
            if clean_price:
                return float(clean_price)
                
        text_content = soup.get_text()
        match = re.search(r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:RMB|USD|\/Ton)', text_content)
        if match:
            clean_price = match.group(1).replace(',', '')
            return float(clean_price)

        return None
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID_TUJUAN,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error send telegram: {e}")

def run_check():
    print("Mencoba mengambil data harga dari SunSirs...")
    dty = fetch_price(URL_DTY)
    rayon = fetch_price(URL_RAYON)

    msg = "📊 <b>UPDATE HARGA KOMODITAS TERKINI</b>\n\n"
    msg += f"• <b>Polyester DTY:</b> RMB {dty:,.2f} /Ton\n" if dty else "• <b>Polyester DTY:</b> Gagal mengambil data\n"
    msg += f"• <b>Viscose Rayon:</b> RMB {rayon:,.2f} /Ton\n\n" if rayon else "• <b>Viscose Rayon:</b> Gagal mengambil data\n\n"
    msg += "<i>Sumber: SunSirs Commodity Index</i>"

    send_telegram_message(msg)
    print("Notifikasi berhasil dikirim ke Telegram!")

def bot_loop():
    print("Bot monitor aktif dan berjalan...")
    while True:
        run_check()
        print(f"Menunggu {INTERVAL_DETIK} detik (24 jam) untuk pengecekan berikutnya...")
        time.sleep(INTERVAL_DETIK)

if __name__ == "__main__":
    # Jalankan loop bot di background thread
    threading.Thread(target=bot_loop, daemon=True).start()
    # Jalankan web server Flask
    run_flask()
