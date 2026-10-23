
import os, sys, time
print("=== BOT v20 ULTRA SIMPLE ===", flush=True)

TOKEN = os.getenv("TOKEN", "")
print(f"RAW len={len(TOKEN)}", flush=True)
# Clean aggressively
TOKEN = TOKEN.strip().replace("\n","").replace("\r","").replace(" ","").replace("\t","").replace("\n","").replace("\r","")
# Remove possible zero width
TOKEN = TOKEN.replace(chr(8203),"").replace(chr(160),"")
print(f"CLEAN len={len(TOKEN)} start={TOKEN[:15]}...", flush=True)

if not TOKEN or len(TOKEN)<20:
    TOKEN = "5146516008:AAFB1jSdDWxEmnotp_sh4G1g2WgIxpwNOXY"
    print(f"Using fallback TOKEN len={len(TOKEN)}", flush=True)

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from flask import Flask
import threading

flask_app = Flask(__name__)
@flask_app.route('/')
def home():
    return f"BOT v20 LIVE - TOKEN len={len(TOKEN)} OK"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    print(f"Flask starting on {port}", flush=True)
    flask_app.run(host="0.0.0.0", port=port, use_reloader=False)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f">>> /start from {update.effective_user.id}", flush=True)
    await update.message.reply_text("✅✅✅ عزیز کار کرد! v20 روشنه!\n\n/tv بزن")

def main():
    # Start flask in thread
    threading.Thread(target=run_flask, daemon=True).start()
    time.sleep(1)
    print("Building Application...", flush=True)
    try:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        print("Starting polling NO DROP...", flush=True)
        # No drop, no close_loop
        app.run_polling(drop_pending_updates=False, allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        print(f"!!! FATAL POLLING ERROR: {e}", flush=True)
        import traceback
        traceback.print_exc()
        print("Keeping Flask alive despite error", flush=True)
        while True:
            time.sleep(60)

if __name__ == "__main__":
    main()
