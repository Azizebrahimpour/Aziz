
import os, json, requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from flask import Flask
import threading

TOKEN = os.getenv("TOKEN") or "5146516008:AAG6jOVffT2Yt8moF2KMFcdDXK8EYbMVMxQ"
print(f"TOKEN loaded: {TOKEN[:10]}...")

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📺 TV لایو", callback_data="tv"), InlineKeyboardButton("💶 قیمت ارز", callback_data="price")],
        [InlineKeyboardButton("📰 اخبار", callback_data="news"), InlineKeyboardButton("🌤️ هوا", callback_data="weather")],
        [InlineKeyboardButton("🎵 آهنگ", callback_data="music")],
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام عزیز 👋\nربات روشن شد! ✅\n\nدستورات:\n/tv - تلویزیون\n/price - قیمت\n/news - اخبار", reply_markup=main_menu())

async def tv_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = """📺 **TV لایو - شبکه‌های ایرانی**

🇺🇸 VOA: https://ir.voanews.com/
📺 ایران اینترنشنال: https://www.iranintl.com/live
💎 GEM: https://gemtv.com/
🎵 رادیو جوان: https://www.radiojavan.com/

🔴 برای پخش تو Voice Chat گروه، لینک رو باز کن و Share کن تو گروه!"""
    await update.message.reply_text(txt, parse_mode="Markdown", reply_markup=main_menu())

async def price_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        r = requests.get("https://api.exchangerate-api.com/v4/latest/EUR", timeout=10).json()
        eur_usd = r["rates"].get("USD", 1.08)
        txt = f"💶 **قیمت ارز امروز**\n\nEUR/USD: {eur_usd}\nمنبع: exchangerate-api.com"
    except:
        txt = "💶 قیمت امروز: EUR ~1.08 USD (آفلاین)"
    await update.message.reply_text(txt, parse_mode="Markdown", reply_markup=main_menu())

async def news_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📰 اخبار: بزودی...\nبرای اخبار کامل به BBC Persian برو: https://www.bbc.com/persian", reply_markup=main_menu())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "tv": await tv_cmd(q, context)
    elif q.data == "price": 
        # fake message for price
        class M: 
            async def reply_text(self, *a, **k): await q.edit_message_text(*a, **k)
        await price_cmd(M(), context)
    elif q.data == "news": await news_cmd(q, context)
    elif q.data == "weather": await q.edit_message_text("🌤️ هوای وین: بزودی...", reply_markup=main_menu())
    elif q.data == "music": await q.edit_message_text("🎵 اسم آهنگ رو بفرست تا لینک بدم!", reply_markup=main_menu())

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        await update.message.reply_text("منو:", reply_markup=main_menu())

# Flask for Render health check
flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "🤖 Bot Live - @Iraniane_moghime_Otrish_bot"
@flask_app.route('/ping')
def ping(): return "pong"
def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port, use_reloader=False)

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("tv", tv_cmd))
    app.add_handler(CommandHandler("price", price_cmd))
    app.add_handler(CommandHandler("news", news_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    print("✅ PRO v15 روشن شد - بدون ارور!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
