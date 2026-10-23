
import os, sys, time, logging, asyncio
logging.basicConfig(level=logging.INFO)

print("=== BOT v21 FIX POLLING ===", flush=True)
TOKEN = os.getenv("TOKEN","").strip().replace("\n","").replace("\r","").replace(" ","")
if not TOKEN or len(TOKEN)<20:
    TOKEN = "5146516008:AAFB1jSdDWxEmnotp_sh4G1g2WglxpwNOXY"
print(f"TOKEN len={len(TOKEN)} ok", flush=True)

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from flask import Flask
import threading

flask_app = Flask(__name__)
@flask_app.route('/')
def home():
    return f"BOT v21 LIVE - len={len(TOKEN)} - Polling Active"

@flask_app.route('/ping')
def ping():
    return "pong"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port, use_reloader=False, threaded=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f">>> START {update.effective_user.id} {update.effective_chat.type}", flush=True)
    try:
        await update.message.reply_text("✅✅✅ عزیز کار کرد! v21 روشنه! بالاخره!\n\n/tv بزن")
        print(">>> Replied to /start", flush=True)
    except Exception as e:
        print(f"Reply error {e}", flush=True)

async def post_init(app):
    # Delete webhook on startup
    try:
        await app.bot.delete_webhook(drop_pending_updates=True)
        print("Webhook deleted in post_init", flush=True)
    except Exception as e:
        print(f"delete_webhook error {e}", flush=True)

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    time.sleep(2)
    print("Building app v21...", flush=True)
    while True:
        try:
            async def run():
                app = Application.builder().token(TOKEN).post_init(post_init).build()
                app.add_handler(CommandHandler("start", start))
                print("Starting polling v21...", flush=True)
                await app.initialize()
                await app.start()
                await app.updater.start_polling(drop_pending_updates=False, allowed_updates=Update.ALL_TYPES)
                print("Polling started! Waiting forever...", flush=True)
                # Keep alive
                while True:
                    await asyncio.sleep(3600)
            asyncio.run(run())
        except Exception as e:
            print(f"!!! FATAL LOOP {e}", flush=True)
            import traceback; traceback.print_exc()
            print("Retrying in 10 sec...", flush=True)
            time.sleep(10)

if __name__ == "__main__":
    main()
