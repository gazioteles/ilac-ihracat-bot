import os
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
HUNTER_API_KEY = os.environ.get("HUNTER_API_KEY", "")

SECTORS = {
    "ecza": "pharmaceutical wholesaler",
    "hastane": "private hospital",
    "klinik": "clinic",
    "turizm": "medical tourism",
    "ithalatci": "pharmaceutical importer",
    "tedarik": "drug supplier",
}

def build_google_links(country, sector):
    queries = [
        f'"{sector}" "{country}" "info@" OR "procurement@" OR "import@"',
        f'"{sector}" "{country}" contact email',
        f'"{sector}" "{country}" site:linkedin.com',
        f'"{sector}" "{country}" "@gmail.com" OR "@yahoo.com"',
    ]
    links = []
    for q in queries:
        url = f"https://www.google.com/search?q={requests.utils.quote(q)}"
        links.append(url)
    return links

def build_directory_links(country, sector):
    encoded_country = requests.utils.quote(country)
    encoded_sector = requests.utils.quote(sector)
    return {
        "Kompass": f"https://www.kompass.com/search/?searchType=company&text={encoded_sector}+{encoded_country}",
        "Europages": f"https://www.europages.co.uk/companies/{encoded_country}/{encoded_sector}.html",
        "Google Maps": f"https://www.google.com/maps/search/{encoded_sector}+{encoded_country}",
        "Alibaba": f"https://www.alibaba.com/trade/search?SearchText={encoded_sector}+{encoded_country}",
    }

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "Merhaba! İlaç İhracat Lead Botu'na hoş geldin.\n\n"
        "Kullanım:\n"
        "/ara [ülke] [sektör]\n\n"
        "Sektör seçenekleri:\n"
        "ecza, hastane, klinik, turizm, ithalatci, tedarik\n\n"
        "Örnek:\n"
        "/ara Kenya ecza\n"
        "/ara Nigeria hastane\n"
        "/ara UAE turizm"
    )
    await update.message.reply_text(msg)

async def ara(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "Eksik bilgi! Örnek kullanım:\n/ara Kenya ecza"
        )
        return

    country = args[0].capitalize()
    sector_key = args[1].lower()

    if sector_key not in SECTORS:
        sektor_listesi = ", ".join(SECTORS.keys())
        await update.message.reply_text(
            f"Geçersiz sektör. Seçenekler:\n{sektor_listesi}"
        )
        return

    sector = SECTORS[sector_key]

    await update.message.reply_text(
        f"Aranıyor: {country} — {sector}\nLinkler hazırlanıyor..."
    )

    google_links = build_google_links(country, sector)
    directory_links = build_directory_links(country, sector)

    msg = f"📍 {country} | {sector}\n\n"
    msg += "🔍 Google Aramaları:\n"
    for i, link in enumerate(google_links, 1):
        msg += f"{i}. {link}\n"

    msg += "\n📋 Dizinler:\n"
    for name, link in directory_links.items():
        msg += f"• {name}: {link}\n"

    msg += "\n💡 Hunter.io ile mail bul:\nhttps://hunter.io"

    await update.message.reply_text(msg)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ara", ara))
    app.add_handler(CommandHandler("help", help_command))
    app.run_polling()

if __name__ == "__main__":
    main()
