import os
import logging
import asyncio
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "8605684770:AAHrhMgTeScvVctVGkvpPnaHm44LgDuotJc"

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
        "Hunter.io": "https://hunter.io",
    }
    return google, directories

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Merhaba! İlaç İhracat Lead Botu\n\n"
        "Kullanım:\n"
        "/ara [ülke] [sektör]\n\n"
        "Sektörler: ecza, hastane, klinik, turizm, ithalatci, tedarik\n\n"
        "Örnek:\n"
        "/ara Kenya ecza\n"
        "/ara Nigeria hastane\n"
        "/ara UAE turizm"
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

    await update.message.reply_text(msg)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ara", ara))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
