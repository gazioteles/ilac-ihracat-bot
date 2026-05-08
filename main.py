import os
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "8605684770:AAHrhMgTeScvVctVGkvpPnaHm44LgDuotJc"
HUNTER_API_KEY = os.environ.get("HUNTER_API_KEY", "")

SECTORS = {
    "ecza": "pharmaceutical wholesaler",
    "hastane": "private hospital",
    "klinik": "clinic",
    "turizm": "medical tourism",
    "ithalatci": "pharmaceutical importer",
    "tedarik": "drug supplier",
}

def build_links(country, sector):
    queries = [
        f'"{sector}" "{country}" "info@" OR "procurement@"',
        f'"{sector}" "{country}" contact email',
        f'"{sector}" "{country}" site:linkedin.com',
        f'"{sector}" "{country}" "@gmail.com" OR "@yahoo.com"',
    ]
    google = [f"https://www.google.com/search?q={requests.utils.quote(q)}" for q in queries]
    directories = {
        "Kompass": f"https://www.kompass.com/search/?searchType=company&text={requests.utils.quote(sector + ' ' + country)}",
        "Google Maps": f"https://www.google.com/maps/search/{requests.utils.quote(sector + ' ' + country)}",
        "Europages": f"https://www.europages.co.uk/companies/{requests.utils.quote(country)}/{requests.utils.quote(sector)}.html",
        "Alibaba": f"https://www.alibaba.com/trade/search?SearchText={requests.utils.quote(sector + ' ' + country)}",
    }
    return google, directories

def hunter_domain_search(domain):
    if not HUNTER_API_KEY:
        return None
    try:
        url = f"https://api.hunter.io/v2/domain-search?domain={domain}&api_key={HUNTER_API_KEY}"
        response = requests.get(url, timeout=10)
        data = response.json()
        emails = data.get("data", {}).get("emails", [])
        return emails
    except:
        return None

def hunter_find_email(domain, first_name="", last_name=""):
    if not HUNTER_API_KEY:
        return None
    try:
        url = f"https://api.hunter.io/v2/email-finder?domain={domain}&first_name={first_name}&last_name={last_name}&api_key={HUNTER_API_KEY}"
        response = requests.get(url, timeout=10)
        data = response.json()
        return data.get("data", {}).get("email")
    except:
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Merhaba! İlaç İhracat Lead Botu\n\n"
        "Komutlar:\n"
        "/ara [ülke] [sektör] — Firma listesi getir\n"
        "/mail [domain] — Firmadan mail adresleri bul\n\n"
        "Sektörler: ecza, hastane, klinik, turizm, ithalatci, tedarik\n\n"
        "Örnekler:\n"
        "/ara Kenya ecza\n"
        "/mail pharmakeeper.com"
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
    await update.message.reply_text(f"Aranıyor: {country} — {sector}...")

    google, directories = build_links(country, sector)

    msg = f"📍 {country} | {sector}\n\n🔍 Google Aramaları:\n"
    for i, link in enumerate(google, 1):
        msg += f"{i}. {link}\n"

    msg += "\n📋 Dizinler:\n"
    for name, link in directories.items():
        msg += f"• {name}: {link}\n"

    msg += "\n💡 Mail bulmak için:\n/mail [firmadomain.com]"

    await update.message.reply_text(msg)

async def mail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Eksik bilgi!\nÖrnek: /mail pharmakeeper.com")
        return

    domain = args[0].lower().replace("www.", "")
    await update.message.reply_text(f"🔍 {domain} için mail adresleri aranıyor...")

    emails = hunter_domain_search(domain)

    if not emails:
        await update.message.reply_text(
            f"❌ {domain} için mail bulunamadı.\n"
            "Bu domain Hunter.io veritabanında olmayabilir.\n"
            "Hunter.io'da manuel ara: https://hunter.io"
        )
        return

    msg = f"✅ {domain} — Bulunan mailler:\n\n"
    for e in emails[:10]:
        email = e.get("value", "")
        position = e.get("position", "Bilinmiyor")
        confidence = e.get("confidence", 0)
        msg += f"📧 {email}\n"
        msg += f"   Pozisyon: {position}\n"
        msg += f"   Güven: %{confidence}\n\n"

    await update.message.reply_text(msg)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ara", ara))
    app.add_handler(CommandHandler("mail", mail))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
