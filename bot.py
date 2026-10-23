
# v17 FINAL - Force Live - 2025
import os, requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from flask import Flask
import threading

TOKEN = os.getenv("TOKEN") or "5146516008:AAG6jOVffT2Yt8moF2KMFcdDXK8EYbMVMxQ"
print(f"BOT v17 starting TOKEN {TOKEN[:8]}...")

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📺 TV لایو", callback_data="tv"), InlineKeyboardButton("💶 قیمت ارز", callback_data="price")],
        [InlineKeyboardButton("📰 اخبار", callback_data="news"), InlineKeyboardButton("🌤️ هوای وین", callback_data="weather")],
        [InlineKeyboardButton("🎵 آهنگ", callback_data="music"), InlineKeyboardButton("⚙️ تنظیمات", callback_data="settings")],
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "سلام عزیز 👋\n\n✅ ربات v17 روشن شد!\n\n📺 /tv - تلویزیون\n💶 /price - قیمت ارز\n📰 /news - اخبار\n\nهمه چیز کار میکنه!"
    await update.message.reply_text(text, reply_markup=main_menu())

async def tv_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message or (update.callback_query.message if update.callback_query else None)
    txt = """📺 **TV لایو**

🇺🇸 VOA: https://ir.voanews.com/
📺 ایران اینترنشنال: https://www.iranintl.com/live
💎 GEM: https://gemtv.com/
🎵 رادیو جوان: https://www.radiojavan.com/"""
    if update.callback_query:
        await update.callback_query.edit_message_text(txt, parse_mode="Markdown", reply_markup=main_menu())
    else:
        await update.message.reply_text(txt, parse_mode="Markdown", reply_markup=main_menu())

async def price_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = "💶 قیمت امروز:\nEUR/USD ~1.08\nمنبع: exchangerate-api"
    if update.callback_query:
        await update.callback_query.edit_message_text(txt, reply_markup=main_menu())
    else:
        await update.message.reply_text(txt, reply_markup=main_menu())

async def news_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = "📰 اخبار کامل: https://www.bbc.com/persian"
    if update.callback_query:
        await update.callback_query.edit_message_text(txt, reply_markup=main_menu())
    else:
        await update.message.reply_text(txt, reply_markup=main_menu())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "tv": await tv_cmd(update, context)
    elif q.data == "price": await price_cmd(update, context)
    elif q.data == "news": await news_cmd(update, context)
    elif q.data == "weather": await q.edit_message_text("🌤️ هوای وین: فردا آفتابی ☀️ 15°C", reply_markup=main_menu())
    elif q.data == "music": await q.edit_message_text("🎵 اسم آهنگ رو بفرست!", reply_markup=main_menu())
    elif q.data == "settings": await q.edit_message_text("⚙️ تنظیمات: بزودی...", reply_markup=main_menu())

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    txt = update.message.text.lower()
    if "/start" in txt: await start(update, context)
    elif "tv" in txt or "تلویزیون" in txt: await tv_cmd(update, context)
    elif "قیمت" in txt or "price" in txt: await price_cmd(update, context)
    else: await update.message.reply_text("منو:", reply_markup=main_menu())

flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "🤖 Bot v17 Live - Aziz - FORCE DEPLOY"
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
    app.add_handler(MessageHandler(filters.TEXT, handle_msg))
    print("✅ v17 Live - Ready!")
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
