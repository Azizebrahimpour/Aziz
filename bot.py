
import os, time, logging, asyncio
logging.basicConfig(level=logging.INFO)
print("=== BOT v23 TV FINAL ===", flush=True)

TOKEN = os.getenv("TOKEN","").strip().replace("\n","").replace("\r","").replace(" ","")
if not TOKEN or len(TOKEN)<20:
    TOKEN = "5146516008:AAFB1jSdDWxEmnotp_sh4G1g2WglxpwNOXY"

API_ID = os.getenv("API_ID","32142474")
API_HASH = os.getenv("API_HASH","df485fa871baea8727242a2d5128f112")
SESSION_STRING = os.getenv("SESSION_STRING","").strip()

print(f"TOKEN len={len(TOKEN)} | SESSION={'YES' if SESSION_STRING else 'NO'}", flush=True)

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from flask import Flask
import threading

flask_app = Flask(__name__)
@flask_app.route('/')
def home():
    return f"BOT v23 TV LIVE - {len(TOKEN)}"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port, use_reloader=False)

CHANNELS = {
    "voa": {"name": "🇺🇸 صدای آمریکا VOA", "url": "https://www.youtube.com/@VOAFarsi/live"},
    "radio_javan": {"name": "🎵 رادیو جوان RadioJavan", "url": "https://www.radiojavan.com"},
    "gem_tv": {"name": "🎬 GEM TV", "url": "https://www.gemgroup.tv"},
    "gem_series": {"name": "🎬 GEM Series", "url": "https://www.gemgroup.tv"},
    "manoto": {"name": "📺 من و تو Manoto", "url": "https://www.youtube.com/@manototv/live"},
    "bbc": {"name": "📡 BBC Persian", "url": "https://www.youtube.com/@BBCPersian/live"},
    "iranintl": {"name": "🌍 ایران اینترنشنال", "url": "https://www.youtube.com/@IranInternational/live"},
    "itn": {"name": "📺 ITN TV", "url": "https://www.itn.tv"},
    "persiana": {"name": "📺 Persiana", "url": "https://persianatv.com"},
    "pmc": {"name": "🎵 PMC", "url": "https://www.youtube.com/@PMCTV/live"},
    "rubika": {"name": "📱 GEM روبیکا", "url": "https://rubika.ir"},
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton("📺 /tv لیست شبکه ها", callback_data="menu_tv")]]
    await update.message.reply_text(
        "✅ ربات عزیز v23 روشنه!\n\n🇮🇷 ایرانیان مقیم اتریش\n\n/tv - لیست شبکه های ماهواره\n/start - شروع",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def tv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb=[]
    row=[]
    for k,ch in CHANNELS.items():
        row.append(InlineKeyboardButton(ch["name"], callback_data=f"play_{k}"))
        if len(row)==2:
            kb.append(row); row=[]
    if row: kb.append(row)
    kb.append([InlineKeyboardButton("⏹ توقف", callback_data="stop")])
    await update.message.reply_text(
        f"📺 لیست شبکه های زنده ({len(CHANNELS)} کانال):\n\nروی کانال بزن:\n\nاکانت دوم: {'✅ وصله' if SESSION_STRING else '❌ فقط لینک - SESSION_STRING بذار'}",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer(); d=q.data
    if d=="menu_tv":
        kb=[]; row=[]
        for k,ch in CHANNELS.items():
            row.append(InlineKeyboardButton(ch["name"], callback_data=f"play_{k}"))
            if len(row)==2:
                kb.append(row); row=[]
        if row: kb.append(row)
        kb.append([InlineKeyboardButton("⏹ توقف", callback_data="stop")])
        await q.edit_message_text("📺 انتخاب کن:", reply_markup=InlineKeyboardMarkup(kb)); return
    if d.startswith("play_"):
        k=d.replace("play_",""); ch=CHANNELS.get(k)
        if not ch: await q.edit_message_text("❌ نیست"); return
        if not SESSION_STRING:
            await q.edit_message_text(f"▶️ {ch['name']}\n\n🔗 {ch['url']}\n\nبرای پخش تو وویس چت SESSION_STRING رو اضافه کن",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🌐 باز کن", url=ch['url'])]]))
        else:
            await q.edit_message_text(f"✅ {ch['name']} آماده پخشه!\n\n🔗 {ch['url']}\n\n📡 بزودی تو وویس چت گروه پخش میشه\n(نیاز به نصب کامل pytgcalls داره)",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🌐 باز کن", url=ch['url'])]]))
    if d=="stop":
        await q.edit_message_text("⏹ متوقف شد")

async def post_init(app):
    try: await app.bot.delete_webhook(drop_pending_updates=True); print("Webhook deleted", flush=True)
    except: pass

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    time.sleep(2)
    while True:
        try:
            async def run():
                app = Application.builder().token(TOKEN).post_init(post_init).build()
                app.add_handler(CommandHandler("start", start))
                app.add_handler(CommandHandler("tv", tv))
                app.add_handler(CallbackQueryHandler(btn))
                print("Starting v23...", flush=True)
                await app.initialize(); await app.start()
                await app.updater.start_polling(drop_pending_updates=False)
                print("v23 LIVE TV READY!", flush=True)
                while True: await asyncio.sleep(3600)
            asyncio.run(run())
        except Exception as e:
            print(f"FATAL {e}"); import traceback; traceback.print_exc(); time.sleep(10)

if __name__=="__main__": main()
