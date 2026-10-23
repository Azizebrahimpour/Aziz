
# v18 FIXED - No drop, always answer
import os, sys
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from flask import Flask
import threading

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    TOKEN = "5146516008:AAG6jOVffT2Yt8moF2KMFcdDXK8EYbMVMxQ"
    print("WARNING: TOKEN env not set, using fallback")

print(f"=== BOT v18 START ===")
print(f"TOKEN: {TOKEN[:15]}... len={len(TOKEN)}")

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📺 TV لایو", callback_data="tv"), InlineKeyboardButton("💶 قیمت", callback_data="price")],
        [InlineKeyboardButton("📰 اخبار", callback_data="news"), InlineKeyboardButton("🌤️ هوا", callback_data="weather")],
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"START received from {update.effective_user.id}")
    await update.message.reply_text("سلام عزیز 👋\n✅ ربات v18 روشن شد! کار میکنه!\n\n/tv /price /news", reply_markup=main_menu())

async def tv_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = "📺 TV:\nVOA: https://ir.voanews.com/\nIranIntl: https://www.iranintl.com/live"
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(txt, reply_markup=main_menu())
    else:
        await update.message.reply_text(txt, reply_markup=main_menu())

async def price_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = "💶 قیمت امروز: EUR/USD 1.08"
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(txt, reply_markup=main_menu())
    else:
        await update.message.reply_text(txt, reply_markup=main_menu())

async def news_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = "📰 https://www.bbc.com/persian"
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(txt, reply_markup=main_menu())
    else:
        await update.message.reply_text(txt, reply_markup=main_menu())

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    print(f"Button {q.data}")
    await q.answer()
    if q.data == "tv": await tv_cmd(update, context)
    elif q.data == "price": await price_cmd(update, context)
    elif q.data == "news": await news_cmd(update, context)
    elif q.data == "weather": await q.edit_message_text("🌤️ وین فردا 15°C آفتابی", reply_markup=main_menu())

async def any_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    print(f"MSG: {update.message.text} from {update.effective_user.id} chat={update.effective_chat.type}")
    # Always answer
    await update.message.reply_text(f"پیامت رو گرفتم: {update.message.text}\n\nمنو:", reply_markup=main_menu())

flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "BOT v18 Live - Working - Aziz"
@flask_app.route('/ping')
def ping(): return "pong"
def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port, use_reloader=False)

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    try:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("tv", tv_cmd))
        app.add_handler(CommandHandler("price", price_cmd))
        app.add_handler(CommandHandler("news", news_cmd))
        app.add_handler(CallbackQueryHandler(buttons))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, any_msg))
        # IMPORTANT: drop_pending_updates=False so old /start not lost
        print("Starting polling with drop_pending=False")
        app.run_polling(drop_pending_updates=False, allowed_updates=Update.ALL_TYPES, close_loop=False)
    except Exception as e:
        print(f"FATAL ERROR: {e}", file=sys.stderr)
        import traceback; traceback.print_exc()
        # Keep flask alive
        while True:
            import time; time.sleep(60)

if __name__ == "__main__":
    main()
