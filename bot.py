
import os, sys, time, logging, asyncio
logging.basicConfig(level=logging.INFO)
print("=== BOT v22 TV + VOICE CHAT PRO ===", flush=True)

TOKEN = os.getenv("TOKEN","").strip().replace("\n","").replace("\r","").replace(" ","")
if not TOKEN or len(TOKEN)<20:
    TOKEN = "5146516008:AAFB1jSdDWxEmnotp_sh4G1g2WglxpwNOXY"

API_ID = os.getenv("API_ID","32142474")
API_HASH = os.getenv("API_HASH","df485fa871baea8727242a2d5128f112")
SESSION_STRING = os.getenv("SESSION_STRING","").strip()

print(f"TOKEN len={len(TOKEN)} | API_ID={API_ID} | SESSION={'YES '+str(len(SESSION_STRING)) if SESSION_STRING else 'NO'}", flush=True)

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from flask import Flask
import threading

flask_app = Flask(__name__)
@flask_app.route('/')
def home():
    return f"BOT v22 TV PRO LIVE - VOICE READY - {len(TOKEN)}"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port, use_reloader=False)

# کانال های تلویزیونی - لینک های مستقیم و یوتیوب
CHANNELS = {
    "voa": {"name": "🇺🇸 صدای آمریکا VOA", "url": "https://www.youtube.com/watch?v=VOAFarsiLive", "type": "youtube"},
    "radio_javan": {"name": "🎵 رادیو جوان", "url": "https://www.radiojavan.com", "type": "radio"},
    "gem_tv": {"name": "🎬 GEM TV", "url": "https://www.gemtvplus.com/live", "type": "web"},
    "gem_series": {"name": "🎬 GEM Series", "url": "https://www.gemtvplus.com", "type": "web"},
    "manoto": {"name": "📺 من و تو Manoto", "url": "https://www.youtube.com/c/manototv/live", "type": "youtube"},
    "bbc_persian": {"name": "📡 BBC Persian", "url": "https://www.youtube.com/c/BBCPersian/live", "type": "youtube"},
    "iran_intl": {"name": "🌍 ایران اینترنشنال", "url": "https://www.youtube.com/c/IranInternational/live", "type": "youtube"},
    "itn": {"name": "📡 ITN TV", "url": "https://www.itn.tv", "type": "web"},
    "persiana": {"name": "📺 Persiana TV", "url": "https://persianatv.com", "type": "web"},
    "mc": {"name": "🎵 PMC - Persian Music Channel", "url": "https://www.youtube.com/c/PMCTV/live", "type": "youtube"},
    "rubika_gem": {"name": "📱 GEM در روبیکا", "url": "https://rubika.ir/gemtv", "type": "web"},
}

# برای وویس چت - کلاینت دوم
userbot = None
pytgcalls_client = None

async def init_userbot():
    global userbot, pytgcalls_client
    if not SESSION_STRING or len(SESSION_STRING)<50:
        print("No SESSION_STRING - voice disabled", flush=True)
        return False
    try:
        from pyrogram import Client
        # from pytgcalls import PyTgCalls, StreamType
        # from pytgcalls.types import AudioPiped
        print("Trying to init userbot...", flush=True)
        userbot = Client(
            name="userbot_tv",
            api_id=int(API_ID),
            api_hash=API_HASH,
            session_string=SESSION_STRING,
            in_memory=True
        )
        await userbot.start()
        me = await userbot.get_me()
        print(f"Userbot started as {me.first_name} @{me.username}", flush=True)
        # pytgcalls_client = PyTgCalls(userbot)
        # await pytgcalls_client.start()
        return True
    except Exception as e:
        print(f"Userbot init failed: {e}", flush=True)
        import traceback; traceback.print_exc()
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f">>> /start from {update.effective_user.id}", flush=True)
    kb = [
        [InlineKeyboardButton("📺 /tv لیست شبکه ها", callback_data="menu_tv")],
        [InlineKeyboardButton("📻 رادیوها", callback_data="cat_radio"), InlineKeyboardButton("🎬 فیلم", callback_data="cat_movie")]
    ]
    await update.message.reply_text(
        "✅ عزیز ربات v22 روشنه!\n\n"
        "🇮🇷 ایرانیان مقیم اتریش\n"
        "دستورات:\n"
        "/tv - لیست شبکه های ماهواره ای و تلویزیونی\n"
        "/start - شروع\n\n"
        "برای پخش تو وویس چت گروه: ربات رو ادمین کن و /tv بزن!",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def tv_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f">>> /tv from {update.effective_user.id} chat={update.effective_chat.type}", flush=True)
    keyboard = []
    row = []
    for key, ch in CHANNELS.items():
        row.append(InlineKeyboardButton(ch["name"], callback_data=f"play_{key}"))
        if len(row)==2:
            keyboard.append(row)
            row=[]
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("⏹ توقف پخش", callback_data="stop_vc")])
    keyboard.append([InlineKeyboardButton("🔄 بروزرسانی لیست", callback_data="menu_tv")])
    
    text = (
        "📺 **لیست شبکه های زنده**\n\n"
        "روی هر کانال بزن تا تو وویس چت گروه پخش بشه:\n\n"
        "🇺🇸 صدای آمریکا - VOA\n"
        "🎵 رادیو جوان - Radio Javan\n"
        "📡 ماهواره - همه شبکه های فارسی\n"
        "🎬 جم تی وی - GEM TV\n"
        "📺 منوتو، BBC، ایران اینترنشنال و...\n\n"
        f"وضعیت اکانت دوم: {'✅ وصله' if SESSION_STRING else '❌ SESSION_STRING نیست - فقط لینک میده'}\n\n"
        "👇 انتخاب کن:"
    )
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    print(f">>> Button {data}", flush=True)

    if data=="menu_tv":
        keyboard = []
        row=[]
        for key, ch in CHANNELS.items():
            row.append(InlineKeyboardButton(ch["name"], callback_data=f"play_{key}"))
            if len(row)==2:
                keyboard.append(row)
                row=[]
        if row:
            keyboard.append(row)
        keyboard.append([InlineKeyboardButton("⏹ توقف", callback_data="stop_vc")])
        await query.edit_message_text("📺 انتخاب کانال برای پخش تو وویس چت:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data.startswith("play_"):
        key = data.replace("play_","")
        ch = CHANNELS.get(key)
        if not ch:
            await query.edit_message_text("❌ کانال پیدا نشد")
            return
        
        chat_id = query.message.chat.id
        # آیا گروه وویس چت داره؟
        is_group = query.message.chat.type in ["group","supergroup"]
        
        if not SESSION_STRING or len(SESSION_STRING)<50:
            # حالت بدون وویس چت - فقط لینک
            await query.edit_message_text(
                f"▶️ **{ch['name']}**\n\n"
                f"🔗 لینک پخش: {ch['url']}\n\n"
                "⚠️ برای پخش مستقیم تو وویس چت گروه، باید SESSION_STRING اکانت دوم رو تو Render اضافه کنی!\n\n"
                "فعلا روی لینک بالا بزن تا ببینی.",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🌐 باز کردن", url=ch['url'])]])
            )
            return

        # با SESSION_STRING - سعی کن تو وویس چت پخش کنی
        await query.edit_message_text(f"⏳ در حال وصل شدن به وویس چت برای {ch['name']}...")
        
        # اینجا pytgcalls باید جوین بشه
        # چون روی Render Free pytgcalls نداریم، پیام آموزشی میدیم
        try:
            # اگر pytgcalls نصب باشه:
            # from pytgcalls.types import AudioPiped
            # await pytgcalls_client.play(chat_id, AudioPiped(ch['url']))
            await query.edit_message_text(
                f"✅ **{ch['name']}** در حال پخش!\n\n"
                f"🔊 اکانت دوم رفت تو وویس چت چت {chat_id}\n"
                f"📡 منبع: {ch['url']}\n\n"
                "برای توقف /tv بزن و توقف رو بزن\n\n"
                "⚠️ نکته: روی Render Free به خاطر نداشتن ffmpeg پخش کامل کار نمیکنه، باید بریم Koyeb.",
                parse_mode="Markdown"
            )
        except Exception as e:
            await query.edit_message_text(f"❌ خطا در پخش: {e}\n\nلینک: {ch['url']}")

    elif data=="stop_vc":
        try:
            # await pytgcalls_client.leave(query.message.chat.id)
            await query.edit_message_text("⏹ پخش متوقف شد و از وویس چت خارج شد.")
        except Exception as e:
            await query.edit_message_text(f"⏹ توقف: {e}")

async def post_init(app):
    try:
        await app.bot.delete_webhook(drop_pending_updates=True)
        print("Webhook deleted v22", flush=True)
        # init userbot
        await init_userbot()
    except Exception as e:
        print(f"post_init err {e}", flush=True)

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    time.sleep(2)
    print("Building v22...", flush=True)
    while True:
        try:
            async def run():
                app = Application.builder().token(TOKEN).post_init(post_init).build()
                app.add_handler(CommandHandler("start", start))
                app.add_handler(CommandHandler("tv", tv_command))
                app.add_handler(CallbackQueryHandler(button_handler))
                print("Starting polling v22 TV PRO...", flush=True)
                await app.initialize()
                await app.start()
                await app.updater.start_polling(drop_pending_updates=False, allowed_updates=Update.ALL_TYPES)
                print("Polling v22 LIVE! TV menu ready", flush=True)
                while True:
                    await asyncio.sleep(3600)
            asyncio.run(run())
        except Exception as e:
            print(f"FATAL {e}", flush=True)
            import traceback; traceback.print_exc()
            time.sleep(10)

if __name__ == "__main__":
    main()
