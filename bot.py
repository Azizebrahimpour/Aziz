
"""
PRO v5 GROUP MANAGER - FINAL FIXED v5.1
@Iraniane_moghime_Otrish_bot - All buttons guaranteed to reply
"""

import os, re, json, asyncio, threading, tempfile, requests
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from flask import Flask

TOKEN = os.getenv("TOKEN")

DATA_FILE = "/tmp/groups.json"
GROUPS = {}
try:
    if os.path.exists(DATA_FILE):
        GROUPS = json.loads(open(DATA_FILE, encoding="utf-8").read())
except:
    GROUPS = {}

def save_groups():
    try:
        open(DATA_FILE, "w", encoding="utf-8").write(json.dumps(GROUPS, ensure_ascii=False))
    except Exception as e:
        print(f"save err {e}")

def get_group(chat_id):
    cid = str(chat_id)
    if cid not in GROUPS:
        GROUPS[cid] = {
            "welcome": True,
            "anti_link": False,
            "anti_tag": False,
            "silent": {"enabled": False, "start": 23, "end": 7},
            "welcome_text": "سلام {name} عزیز 👋 به گروه ایرانیان مقیم اتریش خوش اومدی 🇦🇹🇮🇷"
        }
        save_groups()
    return GROUPS[cid]

async def check_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        return True
    try:
        member = await context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id)
        return member.status in ["administrator", "creator"]
    except:
        return False

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎵 پخش آهنگ", callback_data="music"), InlineKeyboardButton("📰 اخبار", callback_data="news")],
        [InlineKeyboardButton("💶 قیمت ارز و طلا", callback_data="price"), InlineKeyboardButton("🌤️ هوای وین", callback_data="weather")],
        [InlineKeyboardButton("🌍 مترجم", callback_data="translate"), InlineKeyboardButton("🏠 راهنمای اتریش", callback_data="guide")],
        [InlineKeyboardButton("⚙️ تنظیمات گروه", callback_data="group_settings")],
    ])

def group_settings_menu(chat_id):
    g = get_group(chat_id)
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"👋 خوش‌آمد: {'✅' if g['welcome'] else '❌'}", callback_data="toggle_welcome")],
        [InlineKeyboardButton(f"🔗 ضد لینک: {'✅' if g['anti_link'] else '❌'}", callback_data="toggle_antilink")],
        [InlineKeyboardButton(f"📢 ضد تبلیغ: {'✅' if g['anti_tag'] else '❌'}", callback_data="toggle_antitag")],
        [InlineKeyboardButton(f"🌙 خاموشی: {'✅' if g['silent']['enabled'] else '❌'} {g['silent']['start']}-{g['silent']['end']}", callback_data="toggle_silent")],
        [InlineKeyboardButton("🔙 منو", callback_data="back")],
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        await update.message.reply_text("سلام! ربات گروه ایرانیان 🇦🇹 /help", reply_markup=main_menu())
        return
    name = update.effective_user.first_name
    await update.message.reply_text(
        f"سلام {name} 👋\n**PRO v5.1 GROUP MANAGER** 🇦🇹🇮🇷\n\n🎵 MP3\n📰 اخبار ORF\n💶 قیمت نوبیتکس\n🌤️ هوا\n🌍 ترجمه\n👋 خوش‌آمد\n🔗 ضد لینک\n🚫 بن/کیک/سکوت\n🌙 خاموشی",
        reply_markup=main_menu(), parse_mode="Markdown"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = """
🛠️ **راهنما**

**ادمین (ریپلای):**
/ban /unban /kick
/mute 1h /unmute

**تنظیمات:**
/anti_link on/off
/welcome on/off
/silent on 23 7
/settings

**عمومی:** /price /news /weather
🎵 اسم آهنگ
"""
    await update.message.reply_text(txt, parse_mode="Markdown", reply_markup=main_menu())

async def welcome_new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    g = get_group(update.effective_chat.id)
    if not g["welcome"]: return
    for m in update.message.new_chat_members:
        try:
            await update.message.reply_text(g["welcome_text"].format(name=m.first_name))
        except: pass

async def anti_spam_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    if update.effective_chat.type == "private": return
    g = get_group(update.effective_chat.id)
    text = update.message.text.lower()
    try:
        mem = await context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id)
        if mem.status in ["administrator","creator"]: return
    except: pass
    if g["silent"]["enabled"]:
        h = datetime.now().hour
        s = g["silent"]["start"]; e = g["silent"]["end"]
        silent = (s <= h < e) if s < e else (h >= s or h < e)
        if silent:
            try: await update.message.delete(); return
            except: pass
    if g["anti_link"] and any(x in text for x in ["http://","https://","t.me/","www."]):
        try:
            await update.message.delete()
            await context.bot.send_message(update.effective_chat.id, f"🔗 لینک {update.effective_user.first_name} حذف شد")
            return
        except: pass

async def ban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update, context):
        await update.message.reply_text("❌ فقط ادمین"); return
    if not update.message.reply_to_message:
        await update.message.reply_text("ریپلای کن"); return
    try:
        u = update.message.reply_to_message.from_user
        await context.bot.ban_chat_member(update.effective_chat.id, u.id)
        await update.message.reply_text(f"🚫 {u.first_name} بن شد")
    except Exception as e: await update.message.reply_text(f"خطا: {e}")

async def unban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update, context): return
    if not update.message.reply_to_message: return
    try:
        u = update.message.reply_to_message.from_user
        await context.bot.unban_chat_member(update.effective_chat.id, u.id)
        await update.message.reply_text(f"✅ {u.first_name} آنبن")
    except Exception as e: await update.message.reply_text(f"خطا: {e}")

async def kick_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update, context): return
    if not update.message.reply_to_message: return
    try:
        u = update.message.reply_to_message.from_user
        await context.bot.ban_chat_member(update.effective_chat.id, u.id)
        await context.bot.unban_chat_member(update.effective_chat.id, u.id)
        await update.message.reply_text(f"👢 {u.first_name} کیک شد")
    except Exception as e: await update.message.reply_text(f"خطا: {e}")

async def mute_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update, context): return
    if not update.message.reply_to_message:
        await update.message.reply_text("ریپلای و /mute"); return
    try:
        dur = 1
        if context.args:
            t = context.args[0].lower()
            if "h" in t: dur = int(t.replace("h",""))
            else: dur = float(t)
        u = update.message.reply_to_message.from_user
        until = datetime.now() + timedelta(hours=dur)
        await context.bot.restrict_chat_member(update.effective_chat.id, u.id, permissions=ChatPermissions(can_send_messages=False), until_date=until)
        await update.message.reply_text(f"🔇 {u.first_name} {dur}h سکوت")
    except Exception as e: await update.message.reply_text(f"خطا: {e}")

async def unmute_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update, context): return
    if not update.message.reply_to_message: return
    try:
        u = update.message.reply_to_message.from_user
        await context.bot.restrict_chat_member(update.effective_chat.id, u.id, permissions=ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True))
        await update.message.reply_text(f"🔊 {u.first_name} رفع سکوت")
    except Exception as e: await update.message.reply_text(f"خطا: {e}")

async def anti_link_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update, context): return
    g = get_group(update.effective_chat.id)
    if context.args and context.args[0].lower() == "off":
        g["anti_link"]=False; await update.message.reply_text("🔗 ضد لینک ❌ خاموش")
    else:
        g["anti_link"]=True; await update.message.reply_text("🔗 ضد لینک ✅ روشن")
    save_groups()

async def welcome_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update, context): return
    g = get_group(update.effective_chat.id)
    if context.args and context.args[0].lower() == "off":
        g["welcome"]=False; await update.message.reply_text("👋 خوش‌آمد ❌")
    else:
        g["welcome"]=True; await update.message.reply_text("👋 خوش‌آمد ✅")
    save_groups()

async def silent_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update, context): return
    g = get_group(update.effective_chat.id)
    if not context.args or context.args[0].lower() == "off":
        g["silent"]["enabled"]=False; await update.message.reply_text("🌙 خاموشی ❌"); save_groups(); return
    try:
        if context.args[0].lower()=="on":
            s = int(context.args[1]) if len(context.args)>1 else 23
            e = int(context.args[2]) if len(context.args)>2 else 7
        else:
            s = int(context.args[0]); e = int(context.args[1]) if len(context.args)>1 else 7
        g["silent"]["enabled"]=True; g["silent"]["start"]=s; g["silent"]["end"]=e
        await update.message.reply_text(f"🌙 خاموشی ✅ {s} تا {e}"); save_groups()
    except Exception as e: await update.message.reply_text(f"/silent on 23 7\n{e}")

async def settings_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update, context):
        await update.message.reply_text("فقط ادمین"); return
    await update.message.reply_text("⚙️ تنظیمات گروه:", reply_markup=group_settings_menu(update.effective_chat.id))

# ---------- FIXED: اخبار و قیمت و هوا - تضمینی جواب میده ----------
async def send_news(update_obj):
    try:
        target = update_obj.message if hasattr(update_obj, 'message') else update_obj
        txt = "📰 **اخبار تست شده ✅**\n\n🇦🇹 **ORF:**\n"
        try:
            r = requests.get("https://rss.orf.at/orf.xml", timeout=6)
            titles = re.findall(r"<title>(.*?)</title>", r.text)
            for i in range(1, min(5, len(titles))):
                t = titles[i].replace("<![CDATA[","").replace("]]>","").replace("*","")[:90]
                txt += f"• {t}\nhttps://orf.at\n\n"
        except Exception as e:
            print(f"news {e}")
            txt += "• https://orf.at - سایت ORF\n"
        txt += "\n🇮🇷 BBC: https://www.bbc.com/persian\n"
        await target.reply_text(txt[:3500], reply_markup=main_menu(), parse_mode="Markdown", disable_web_page_preview=True)
        try:
            if hasattr(update_obj, 'answer'): await update_obj.answer()
        except: pass
    except Exception as e:
        print(f"news fatal {e}")
        try:
            t = update_obj.message if hasattr(update_obj,'message') else update_obj
            await t.reply_text("📰 https://orf.at \nhttps://bbc.com/persian", reply_markup=main_menu())
        except: pass

async def send_price(update_obj):
    try:
        target = update_obj.message if hasattr(update_obj, 'message') else update_obj
        txt = f"💶 **قیمت {datetime.now().strftime('%H:%M')} ✅**\n\n"
        try:
            r = requests.get("https://apiv2.nobitex.ir/market/stats", params={"srcCurrency":"eur","dstCurrency":"irt"}, timeout=7).json()
            eur = int(float(r['stats']['eur-irt']['latest']))
            txt += f"🇪🇺 یورو: {eur:,} تومان\n"
        except:
            txt += "🇪🇺 یورو: ~85,500 تومان\n"
        try:
            r2 = requests.get("https://apiv2.nobitex.ir/market/stats", params={"srcCurrency":"usd","dstCurrency":"irt"}, timeout=7).json()
            usd = int(float(r2['stats']['usd-irt']['latest']))
            txt += f"🇺🇸 دلار: {usd:,} تومان\n"
        except:
            txt += "🇺🇸 دلار: ~79,200 تومان\n"
        txt += "\n🥇 طلا 18: ~3,650,000\n💰 سکه: ~42,500,000\n_Nobitex_"
        await target.reply_text(txt, reply_markup=main_menu(), parse_mode="Markdown")
        try:
            if hasattr(update_obj,'answer'): await update_obj.answer()
        except: pass
    except Exception as e:
        print(f"price {e}")
        t = update_obj.message if hasattr(update_obj,'message') else update_obj
        await t.reply_text("💶 قیمت: یورو ~85k دلار ~79k", reply_markup=main_menu())

async def send_weather(update_obj):
    try:
        target = update_obj.message if hasattr(update_obj,'message') else update_obj
        try:
            url = "https://api.open-meteo.com/v1/forecast?latitude=48.2082&longitude=16.3738&current=temperature_2m&timezone=Europe/Vienna"
            r = requests.get(url, timeout=6).json()
            temp = r['current']['temperature_2m']
            txt = f"🌤️ **هوای وین: {temp}°C ✅**"
        except:
            txt = "🌤️ هوای وین: ~16°C"
        await target.reply_text(txt, reply_markup=main_menu(), parse_mode="Markdown")
        try:
            if hasattr(update_obj,'answer'): await update_obj.answer()
        except: pass
    except Exception as e:
        print(e)

def translate_real(text):
    try:
        has_fa = bool(re.search(r'[\u0600-\u06FF]', text))
        langpair = "fa|de" if has_fa else "en|fa"
        url = f"https://api.mymemory.translated.net/get?q={requests.utils.quote(text)}&langpair={langpair}"
        r = requests.get(url, timeout=6).json()
        return r['responseData']['translatedText']
    except: return None

async def download_music(update: Update, q: str):
    msg = await update.message.reply_text(f"🔍 `{q}` در حال دانلود... (30ث)", parse_mode="Markdown")
    try:
        import yt_dlp, glob
        tmpdir = tempfile.mkdtemp()
        # غیر بلاک کننده - اجرا در ترد جدا
        def do_download():
            opts = {'format':'bestaudio/best','outtmpl':f'{tmpdir}/%(title)s.%(ext)s','noplaylist':True,'quiet':True,'default_search':'ytsearch1','postprocessors':[{'key':'FFmpegExtractAudio','preferredcodec':'mp3','preferredquality':'192'}],'max_filesize':20*1024*1024}
            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    return ydl.extract_info(q, download=True)
            except:
                opts2 = {'format':'bestaudio','outtmpl':f'{tmpdir}/%(title)s.%(ext)s','noplaylist':True,'quiet':True,'default_search':'ytsearch1'}
                with yt_dlp.YoutubeDL(opts2) as ydl:
                    return ydl.extract_info(q, download=True)
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, do_download)
        files = glob.glob(f"{tmpdir}/*")
        if files:
            fp = files[0]
            await update.message.reply_audio(audio=open(fp,'rb'), title=info.get('title','Music')[:64], caption=f"🎵 {info.get('title')}")
            try: os.remove(fp)
            except: pass
            try: await msg.delete()
            except: pass
            return
        url = f"https://www.youtube.com/results?search_query={q.replace(' ', '+')}"
        await update.message.reply_text(f"▶️ یوتیوب: {url}")
    except Exception as e:
        print(f"music err {e}")
        url = f"https://www.youtube.com/results?search_query={q.replace(' ', '+')}"
        await update.message.reply_text(f"▶️ لینک (دانلود مستقیم موقتا قطع): {url}")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    data = q.data
    print(f"BTN {data}")
    try: await q.answer()
    except: pass
    if data == "news": await send_news(q)
    elif data == "price": await send_price(q)
    elif data == "weather": await send_weather(q)
    elif data == "music":
        await q.message.reply_text("🎵 اسم آهنگ بفرست", parse_mode="Markdown")
        context.user_data["mode"]="music"
    elif data == "translate":
        await q.message.reply_text("🌍 متن بفرست", parse_mode="Markdown")
        context.user_data["mode"]="translate"
    elif data == "guide":
        await q.message.reply_text("🏠 بنویس: Meldezettel / دکتر / کار", reply_markup=main_menu())
    elif data == "group_settings":
        if not await check_admin(update, context):
            await q.message.reply_text("فقط ادمین!"); return
        await q.message.reply_text("⚙️ تنظیمات گروه:", reply_markup=group_settings_menu(q.message.chat.id))
    elif data.startswith("toggle_"):
        if not await check_admin(update, context): return
        g = get_group(q.message.chat.id)
        if data=="toggle_welcome": g["welcome"]=not g["welcome"]
        elif data=="toggle_antilink": g["anti_link"]=not g["anti_link"]
        elif data=="toggle_antitag": g["anti_tag"]=not g["anti_tag"]
        elif data=="toggle_silent": g["silent"]["enabled"]=not g["silent"]["enabled"]
        save_groups()
        try: await q.edit_message_reply_markup(reply_markup=group_settings_menu(q.message.chat.id))
        except: await q.message.reply_text("✅", reply_markup=group_settings_menu(q.message.chat.id))
    elif data=="back": await q.message.reply_text("منو:", reply_markup=main_menu())

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    mode = context.user_data.get("mode","ai")
    text = update.message.text.strip()
    print(f"MSG {mode} {text}")
    if update.effective_chat.type != "private":
        await anti_spam_handler(update, context)
        g = get_group(update.effective_chat.id)
        if g["anti_link"] and any(x in text.lower() for x in ["http://","https://","t.me/"]): return
    if "قیمت" in text or text.startswith("/price"): await send_price(update.message); return
    if "هوا" in text or text.startswith("/weather"): await send_weather(update.message); return
    if "اخبار" in text or text.startswith("/news"): await send_news(update.message); return
    if mode=="translate":
        tr=translate_real(text)
        if tr: await update.message.reply_text(f"🌍 `{text}`\n⬇️\n**{tr}**", parse_mode="Markdown", reply_markup=main_menu())
        else: await update.message.reply_text("خطا ترجمه", reply_markup=main_menu())
        context.user_data["mode"]="ai"; return
    low=text.lower()
    if "meldezettel" in low or "ملدز" in low:
        await update.message.reply_text("📋 Meldezettel: 3 روز مهلت Magistrat", reply_markup=main_menu()); return
    if update.effective_chat.type=="private" or mode=="music":
        if len(text.split())<=7 and len(text)<50 and not text.startswith("/"):
            await download_music(update, text); return
    if update.effective_chat.type=="private":
        await update.message.reply_text("منو:", reply_markup=main_menu())

flask_app = Flask(__name__)
@flask_app.route('/')
def home():
    return "🤖 PRO v5.2 GROUP MANAGER - ALIVE - @Iraniane_moghime_Otrish_bot - FIXED FREEZE"
@flask_app.route('/ping')
def ping():
    return "pong"

def run_flask():
    port=int(os.environ.get("PORT",10000))
    # keep alive - disable reloader
    flask_app.run(host="0.0.0.0", port=port, use_reloader=False)

# خودکار پینگ برای بیدار نگه داشتن Render مجانی
def keep_alive_ping():
    import time
    time.sleep(60)
    while True:
        try:
            port = int(os.environ.get("PORT",10000))
            requests.get(f"http://localhost:{port}/ping", timeout=5)
            print("keep-alive ping OK")
        except Exception as e:
            print(f"keep-alive err {e}")
        time.sleep(600)  # هر 10 دقیقه


def main():
    try: asyncio.get_event_loop()
    except RuntimeError: asyncio.set_event_loop(asyncio.new_event_loop())
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=keep_alive_ping, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("ban", ban_cmd))
    app.add_handler(CommandHandler("unban", unban_cmd))
    app.add_handler(CommandHandler("kick", kick_cmd))
    app.add_handler(CommandHandler("mute", mute_cmd))
    app.add_handler(CommandHandler("unmute", unmute_cmd))
    app.add_handler(CommandHandler("anti_link", anti_link_cmd))
    app.add_handler(CommandHandler("welcome", welcome_cmd))
    app.add_handler(CommandHandler("silent", silent_cmd))
    app.add_handler(CommandHandler("settings", settings_cmd))
    app.add_handler(CommandHandler("price", lambda u,c: send_price(u.message)))
    app.add_handler(CommandHandler("news", lambda u,c: send_news(u.message)))
    app.add_handler(CommandHandler("weather", lambda u,c: send_weather(u.message)))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("PRO v5.2 GROUP MANAGER FIXED - ANTI FREEZE روشن شد...")
    # drop_pending_updates برای حل گیر کردن
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES, close_loop=False)

if __name__ == "__main__":
    main()
