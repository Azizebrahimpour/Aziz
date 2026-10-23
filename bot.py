
import os, sys
# Force strip token
TOKEN = os.getenv("TOKEN", "").strip()
# Remove all whitespace/newlines that break token
TOKEN = TOKEN.replace("\n","").replace("\r","").replace(" ","").replace("\t","")
if not TOKEN:
    TOKEN = "5146516008:AAG6jOVffT2Yt8moF2KMFcdDXK8EYbMVMxQ"
    print("WARNING: using fallback token - set TOKEN env!")

print("=== BOT v19 START ===")
print(f"TOKEN length={len(TOKEN)} starts={TOKEN[:10]}...")
if len(TOKEN) < 30 or ":" not in TOKEN:
    print("ERROR: TOKEN invalid format! Must be like 123456:ABC...")

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from flask import Flask
import threading, requests

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📺 TV", callback_data="tv"), InlineKeyboardButton("💶 قیمت", callback_data="price")],
        [InlineKeyboardButton("📰 اخبار", callback_data="news")],
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"START from {update.effective_user.id}")
    await update.message.reply_text("✅ سلام عزیز! ربات v19 روشنه! کار میکنه!\n\n/tv /price", reply_markup=main_menu())

async def any_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    print(f"MSG {update.message.text}")
    await update.message.reply_text(f"گرفتم: {update.message.text}", reply_markup=main_menu())

async def btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text(f"دکمه {q.data} زده شد", reply_markup=main_menu())

flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "BOT v19 LIVE - OK"
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
        app.add_handler(CallbackQueryHandler(btn))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, any_msg))
        print("Polling started drop_pending=False")
        app.run_polling(drop_pending_updates=False)
    except Exception as e:
        print(f"FATAL {e}")
        import traceback; traceback.print_exc()
        while True:
            import time; time.sleep(30)

if __name__ == "__main__":
    main()
