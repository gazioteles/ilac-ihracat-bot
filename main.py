import os
import re
import time
import logging
import requests
import openpyxl
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "8605684770:AAHrhMgTeScvVctVGkvpPnaHm44LgDuotJc"
HUNTER_API_KEY = os.environ.get("HUNTER_API_KEY", "")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")

SECTORS = {
    "ecza": "pharmacy wholesaler",
    "hastane": "private hospital",
    "klinik": "clinic",
    "turizm": "medical tourism",
    "ithalatci": "pharmaceutical importer",
    "tedarik": "drug supplier",
    "tercuman": "medical interpreter",
}

def google_maps_search(query, country):
    try:
        search_url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": f"{query} {country}",
            "format": "json",
            "limit": 10,
            "addressdetails": 1,
        }
        headers = {"User-Agent": "ilac-ihracat-bot/1.0"}
        response = requests.get(search_url, params=params, headers=headers, timeout=10)
        data = response.json()
        results = []
        for place in data:
            results.append({
                "name": place.get("display_name", "").split(",")[0],
                "address": place.get("display_name", ""),
                "phone": "",
                "website": "",
                "rating": "",
            })
            time.sleep(0.5)
        return results
    except Exception as e:
        logging.error(f"OpenStreetMap error: {e}")
        return []
    try:
        search_query = f"{query} {country}"
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {"query": search_query, "key": GOOGLE_API_KEY}
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        results = []
        for place in data.get("results", [])[:10]:
            place_id = place.get("place_id")
            detail_url = "https://maps.googleapis.com/maps/api/place/details/json"
            detail_params = {
                "place_id": place_id,
                "fields": "name,formatted_address,formatted_phone_number,website,rating",
                "key": GOOGLE_API_KEY
            }
            detail_resp = requests.get(detail_url, params=detail_params, timeout=10)
            detail = detail_resp.json().get("result", {})
            results.append({
                "name": detail.get("name", ""),
                "address": detail.get("formatted_address", ""),
                "phone": detail.get("formatted_phone_number", ""),
                "website": detail.get("website", ""),
                "rating": detail.get("rating", ""),
            })
            time.sleep(0.5)
        return results
    except Exception as e:
        logging.error(f"Google Maps error: {e}")
        return []

def extract_email_from_website(website):
    if not website:
        return ""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(website, headers=headers, timeout=8)
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', resp.text)
        filtered = [e for e in emails if not any(x in e.lower() for x in ['example', 'domain', 'email', 'test'])]
        return filtered[0] if filtered else ""
    except:
        return ""

def hunter_search(domain):
    if not HUNTER_API_KEY or not domain:
        return ""
    try:
        domain = domain.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]
        url = f"https://api.hunter.io/v2/domain-search?domain={domain}&api_key={HUNTER_API_KEY}&limit=1"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        emails = data.get("data", {}).get("emails", [])
        return emails[0].get("value", "") if emails else ""
    except:
        return ""

def create_excel(firms, country, sector):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Leads"
    headers = ["Firma Adı", "Adres", "Telefon", "Website", "Email", "Puan", "Ülke", "Sektör"]
    ws.append(headers)
    for f in firms:
        ws.append([
            f.get("name", ""),
            f.get("address", ""),
            f.get("phone", ""),
            f.get("website", ""),
            f.get("email", ""),
            f.get("rating", ""),
            country,
            sector,
        ])
    filename = f"/tmp/leads_{country}_{sector}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    wb.save(filename)
    return filename

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Merhaba! İlaç İhracat Lead Botu\n\n"
        "Komutlar:\n"
        "/ara [ülke] [sektör] — Firma bul + Excel oluştur\n"
        "/mail [domain] — Domain'den mail bul\n\n"
        "Sektörler:\necza, hastane, klinik, turizm, ithalatci, tedarik, tercuman\n\n"
        "Örnek:\n"
        "/ara Kenya ecza\n"
        "/ara UAE hastane\n"
        "/mail firma.com"
    )
    await update.message.reply_text(text)

async def ara(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Eksik bilgi!\nÖrnek: /ara Kenya ecza")
        return

    country = args[0].capitalize()
    sector_key = args[1].lower()

    if sector_key not in SECTORS:
        await update.message.reply_text(f"Geçersiz sektör.\nSeçenekler: {', '.join(SECTORS.keys())}")
        return

    sector = SECTORS[sector_key]
    await update.message.reply_text(f"🔍 {country} — {sector} aranıyor...\nBu işlem 1-2 dakika sürebilir.")

    firms = google_maps_search(sector, country)

    if not firms:
    await update.message.reply_text("❌ Sonuç bulunamadı. Farklı ülke veya sektör dene.")
    return

    await update.message.reply_text(f"✅ {len(firms)} firma bulundu. Mailler aranıyor...")

    for firm in firms:
        website = firm.get("website", "")
        email = extract_email_from_website(website)
        if not email and website:
            domain = website.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]
            email = hunter_search(domain)
        firm["email"] = email
        time.sleep(0.3)

    excel_file = create_excel(firms, country, sector_key)

    msg = f"📊 {country} — {sector}\n\n"
    for i, f in enumerate(firms, 1):
        msg += f"{i}. {f['name']}\n"
        if f.get('phone'):
            msg += f"   📞 {f['phone']}\n"
        if f.get('email'):
            msg += f"   📧 {f['email']}\n"
        if f.get('website'):
            msg += f"   🌐 {f['website']}\n"
        msg += "\n"

    await update.message.reply_text(msg[:4000])
    await update.message.reply_document(
        document=open(excel_file, 'rb'),
        filename=f"leads_{country}_{sector_key}.xlsx",
        caption="Excel dosyan hazır! 📊"
    )

async def mail_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Örnek: /mail firma.com")
        return
    domain = args[0].lower().replace("www.", "")
    await update.message.reply_text(f"🔍 {domain} aranıyor...")
    email = hunter_search(domain)
    if email:
        await update.message.reply_text(f"✅ Bulunan mail:\n📧 {email}")
    else:
        await update.message.reply_text(f"❌ {domain} için mail bulunamadı.")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ara", ara))
    app.add_handler(CommandHandler("mail", mail_komutu))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
