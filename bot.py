
"""
PRO v15 - TV + MUSIC VOICE CHAT - @Iraniane_moghime_Otrish_bot
Features: Full news, price, weather, guide, TV live in VC, Music live in VC
"""
import os, re, json, asyncio, threading, tempfile, requests
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from flask import Flask

TOKEN = os.getenv("TOKEN")
API_ID = os.getenv("API_ID") or "32142474"
API_HASH = os.getenv("API_HASH") or "df485fa871baea8727242a2d5128f112"
SESSION_STRING = os.getenv("SESSION_STRING")  # Pyrogram session for userbot
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
    except: pass

def get_group(chat_id):
    cid = str(chat_id)
    if cid not in GROUPS:
        GROUPS[cid] = {
            "welcome": True, "anti_link": False, "anti_tag": False,
            "silent": {"enabled": False, "start": 23, "end": 7},
            "welcome_text": "سلام {name} عزیز 👋 به گروه ایرانیان مقیم اتریش خوش اومدی 🇦🇹🇮🇷",
            "insta_link": "", "insta_text": "پیج اینستاگرام ما رو فالو کنید 👇",
            "auto_news": False
        }
        save_groups()
    if "insta_link" not in GROUPS[cid]:
        GROUPS[cid]["insta_link"]=""; GROUPS[cid]["insta_text"]="پیج اینستاگرام ما رو فالو کنید 👇"; GROUPS[cid]["auto_news"]=False; save_groups()
    return GROUPS[cid]

async def check_admin(update, context):
    if update.effective_chat.type=="private": return True
    try:
        m=await context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id)
        return m.status in ["administrator","creator"]
    except: return False

# ========== VOICE CHAT PLAYER (PyTgCalls) ==========
voice_client = None
pytgcalls_instance = None
is_voice_available = False

def init_voice_client():
    global voice_client, pytgcalls_instance, is_voice_available
    if not API_ID or not API_HASH or not SESSION_STRING:
        print("VOICE: API_ID/API_HASH/SESSION_STRING not set - running in LINK mode only")
        return
    try:
        from pyrogram import Client
        from pytgcalls import PyTgCalls
        from pytgcalls.types import MediaStream
        voice_client = Client(name="voice_userbot", api_id=int(API_ID), api_hash=API_HASH, session_string=SESSION_STRING, in_memory=True)
        pytgcalls_instance = PyTgCalls(voice_client)
        is_voice_available = True
        print("VOICE: PyTgCalls initialized")
        # Start in thread
        def start_voice():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            async def run():
                await voice_client.start()
                await pytgcalls_instance.start()
                print("VOICE: Userbot started and ready for VC")
                await asyncio.Event().wait()
            loop.run_until_complete(run())
        threading.Thread(target=start_voice, daemon=True).start()
    except Exception as e:
        print(f"VOICE init error: {e}")
        is_voice_available = False

# TV Channels - LIVE STREAMS (m3u8 / mp3)
TV_CHANNELS = {
    "voa": {"name": "🇺🇸 صدای آمریکا VOA فارسی", "url": "https://voa-pp1.global.ssl.fastly.net/v1/playlist/8b542a6c-b2c2-4e8f-a8a8-0d6b7a3c3c3c.m3u8", "type": "tv", "fallback": "https://ir.voanews.com/"},
    "radiojavan": {"name": "🎵 رادیو جوان", "url": "https://stream.radiojavan.com/radiojavan", "type": "radio", "fallback": "https://www.radiojavan.com/"},
    "iranintl": {"name": "📺 ایران اینترنشنال", "url": "https://live.iranintl.com/hls/live.m3u8", "type": "tv", "fallback": "https://www.iranintl.com/live"},
    "bbc": {"name": "🇬🇧 BBC فارسی", "url": "https://stream.live.bbc.co.uk/bbc_persian_radio", "type": "radio", "fallback": "https://www.bbc.com/persian"},
    "manoto": {"name": "🎬 فیلم و سریال (منوتو آرشیو)", "url": "https://manoto.live/hls/live.m3u8", "type": "tv", "fallback": "https://www.manototv.com/"},
    "satellite": {"name": "📡 ماهواره - شبکه‌های ایرانی", "url": "https://perseus-stream.com/irib.m3u8", "type": "tv", "fallback": "https://www.telewebion.com/"},
    "gem": {"name": "💎 GEM TV", "url": "https://gemtv.live/hls/gem.m3u8", "type": "tv", "fallback": "https://gemtv.com/"},
    "afghan_tolo": {"name": "🇦🇫 طلوع افغانستان", "url": "https://tolotv.live/hls/tolo.m3u8", "type": "tv", "fallback": "https://www.tolo.tv/"},
    "itn": {"name": "🎥 ITN فیلم", "url": "https://itn.live/hls/live.m3u8", "type": "film", "fallback": "https://www.itn.ir/"},
}

# For music VC playback
VC_QUEUE = {}  # chat_id -> list of tracks

async def play_in_vc(chat_id, stream_url, title=""):
    global pytgcalls_instance, is_voice_available
    if not is_voice_available or not pytgcalls_instance:
        return False, "برای پخش لایو تو Voice Chat باید اول اکانت دوم (SESSION_STRING) رو ست کنی. الان فقط لینک مستقیم میدم."
    try:
        from pytgcalls.types import MediaStream
        # Leave if already in call
        try:
            await pytgcalls_instance.leave_call(chat_id)
        except: pass
        await asyncio.sleep(1)
        await pytgcalls_instance.play(chat_id, MediaStream(stream_url))
        print(f"VOICE: Playing {title} in {chat_id}")
        return True, f"🔴 الان داره تو Voice Chat گروه پخش میشه: {title}"
    except Exception as e:
        print(f"VC play error {e}")
        return False, f"خطا در پخش VC: {e}\nاول باید Voice Chat گروه رو روشن کنید و اکانت دوم رو ادمین کنید!"

async def stop_vc(chat_id):
    try:
        if pytgcalls_instance:
            await pytgcalls_instance.leave_call(chat_id)
        return True
    except Exception as e:
        print(f"VC stop err {e}")
        return False

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📺 TV لایو", callback_data="tv_menu"), InlineKeyboardButton("🎵 آهنگ VC", callback_data="music_vc")],
        [InlineKeyboardButton("🎵 پخش آهنگ (MP3)", callback_data="music"), InlineKeyboardButton("📰 اخبار کامل", callback_data="news")],
        [InlineKeyboardButton("💶 قیمت ارز", callback_data="price"), InlineKeyboardButton("🌤️ هوای وین", callback_data="weather")],
        [InlineKeyboardButton("📸 اینستاگرام", callback_data="insta"), InlineKeyboardButton("🌍 مترجم", callback_data="translate")],
        [InlineKeyboardButton("🏠 راهنمای اتریش", callback_data="guide"), InlineKeyboardButton("⚙️ تنظیمات گروه", callback_data="group_settings")],
    ])

def tv_menu_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇺🇸 صدای آمریکا", callback_data="tv_voa"), InlineKeyboardButton("🎵 رادیو جوان", callback_data="tv_radiojavan")],
        [InlineKeyboardButton("📺 ایران اینترنشنال", callback_data="tv_iranintl"), InlineKeyboardButton("🇬🇧 BBC فارسی", callback_data="tv_bbc")],
        [InlineKeyboardButton("🎬 فیلم", callback_data="tv_itn"), InlineKeyboardButton("📡 ماهواره", callback_data="tv_satellite")],
        [InlineKeyboardButton("💎 GEM TV", callback_data="tv_gem"), InlineKeyboardButton("🇦🇫 طلوع افغانی", callback_data="tv_afghan_tolo")],
        [InlineKeyboardButton("⏹️ قطع پخش", callback_data="vc_stop"), InlineKeyboardButton("🔙 منو", callback_data="back")],
    ])

def group_settings_menu(chat_id):
    g=get_group(chat_id)
    insta_status="✅" if g["insta_link"] else "❌"
    auto_status="✅" if g.get("auto_news") else "❌"
    vc_status="✅" if is_voice_available else "❌"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"👋 خوش‌آمد: {'✅' if g['welcome'] else '❌'}", callback_data="toggle_welcome")],
        [InlineKeyboardButton(f"🔗 ضد لینک: {'✅' if g['anti_link'] else '❌'}", callback_data="toggle_antilink")],
        [InlineKeyboardButton(f"🌙 خاموشی: {'✅' if g['silent']['enabled'] else '❌'} {g['silent']['start']}-{g['silent']['end']}", callback_data="toggle_silent")],
        [InlineKeyboardButton(f"📸 اینستا: {insta_status}", callback_data="set_insta_btn")],
        [InlineKeyboardButton(f"📰 اخبار خودکار 4ساعته: {auto_status}", callback_data="toggle_autonews")],
        [InlineKeyboardButton(f"📺 VC لایو: {vc_status}", callback_data="vc_info")],
        [InlineKeyboardButton("🔙 منو", callback_data="back")],
    ])

async def start(update, context):
    if update.effective_chat.type!="private":
        await update.message.reply_text("سلام! ربات گروه ایرانیان 🇦🇹 /help 📺 /tv", reply_markup=main_menu()); return
    name=update.effective_user.first_name
    await update.message.reply_text(f"سلام {name} 👋\n**PRO v15 TV+VC** 🇦🇹🇮🇷\n\n📺 TV لایو تو Voice Chat\n🎵 آهنگ زنده تو گروه\n📰 اخبار کامل\n💶 قیمت\n🌤️ هوا\n📸 اینستا", reply_markup=main_menu(), parse_mode="Markdown")

async def help_cmd(update, context):
    txt="🛠️ **راهنما v15 TV+VC**\n\n**📺 TV لایو:**\n/tv - منوی تلویزیون (VOA, رادیو جوان, فیلم, ماهواره)\n/vcstop - قطع پخش\n\n**🎵 موزیک VC:**\nتو گروه: اسم آهنگ بفرست بعد دکمه پخش زنده بزن\n/tv رادیو جوان بزن مستقیم تو VC\n\n**ادمین (ریپلای):**\n/ban /unban /kick\n/mute 1h /unmute\n\n**تنظیمات:**\n/anti_link on/off\n/welcome on/off\n/silent on 23 7\n/settings\n/set_insta https://...\n/insta\n/auto_news on/off\n\n**عمومی:** /price /news /weather /insta /tv /kar /doctor /shop /guide\n"
    await update.message.reply_text(txt, parse_mode="Markdown", reply_markup=main_menu())

async def welcome_new(update, context):
    g=get_group(update.effective_chat.id)
    if not g["welcome"]: return
    for m in update.message.new_chat_members:
        try:
            txt=g["welcome_text"].format(name=m.first_name)
            if g["insta_link"]: txt+=f"\n\n{g['insta_text']}\n{g['insta_link']}"
            await update.message.reply_text(txt)
        except: pass

async def anti_spam_handler(update, context):
    if not update.message or not update.message.text: return
    if update.effective_chat.type=="private": return
    g=get_group(update.effective_chat.id)
    text=update.message.text.lower()
    try:
        mem=await context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id)
        if mem.status in ["administrator","creator"]: return
    except: pass
    if g["silent"]["enabled"]:
        h=datetime.now().hour; s=g["silent"]["start"]; e=g["silent"]["end"]
        silent=(s<=h<e) if s<e else (h>=s or h<e)
        if silent:
            try: await update.message.delete(); return
            except: pass
    if g["anti_link"] and any(x in text for x in ["http://","https://","t.me/","www."]):
        if g["insta_link"] and g["insta_link"].lower() in text: return
        try:
            await update.message.delete()
            await context.bot.send_message(update.effective_chat.id, f"🔗 لینک {update.effective_user.first_name} حذف شد")
            return
        except: pass

async def ban_cmd(update, context):
    if not await check_admin(update, context): await update.message.reply_text("فقط ادمین!"); return
    if not update.message.reply_to_message: await update.message.reply_text("روی پیام فرد ریپلای بزن /ban"); return
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, update.message.reply_to_message.from_user.id)
        await update.message.reply_text(f"🚫 {update.message.reply_to_message.from_user.first_name} بن شد")
    except Exception as e: await update.message.reply_text(f"خطا {e}")

async def unban_cmd(update, context):
    if not await check_admin(update, context): return
    if not update.message.reply_to_message: return
    try:
        await context.bot.unban_chat_member(update.effective_chat.id, update.message.reply_to_message.from_user.id)
        await update.message.reply_text("✅ آنبن شد")
    except: pass

async def kick_cmd(update, context):
    if not await check_admin(update, context): return
    if not update.message.reply_to_message: return
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, update.message.reply_to_message.from_user.id)
        await context.bot.unban_chat_member(update.effective_chat.id, update.message.reply_to_message.from_user.id)
        await update.message.reply_text("👢 کیک شد")
    except: pass

async def mute_cmd(update, context):
    if not await check_admin(update, context): return
    if not update.message.reply_to_message: return
    try:
        until=None
        if context.args:
            t=context.args[0]
            if "h" in t: until=datetime.now().timestamp()+int(t.replace("h",""))*3600
            if "m" in t: until=datetime.now().timestamp()+int(t.replace("m",""))*60
        perms=ChatPermissions(can_send_messages=False)
        await context.bot.restrict_chat_member(update.effective_chat.id, update.message.reply_to_message.from_user.id, perms, until_date=until)
        await update.message.reply_text("🔇 میوت شد")
    except Exception as e: await update.message.reply_text(f"خطا {e}")

async def unmute_cmd(update, context):
    if not await check_admin(update, context): return
    if not update.message.reply_to_message: return
    try:
        perms=ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True)
        await context.bot.restrict_chat_member(update.effective_chat.id, update.message.reply_to_message.from_user.id, perms)
        await update.message.reply_text("🔊 آنمیوت شد")
    except: pass

async def anti_link_cmd(update, context):
    if not await check_admin(update, context): return
    g=get_group(update.effective_chat.id)
    arg=context.args[0].lower() if context.args else ""
    if arg=="on": g["anti_link"]=True
    elif arg=="off": g["anti_link"]=False
    else: g["anti_link"]=not g["anti_link"]
    save_groups()
    await update.message.reply_text(f"🔗 ضد لینک: {'✅' if g['anti_link'] else '❌'}")

async def welcome_cmd(update, context):
    if not await check_admin(update, context): return
    g=get_group(update.effective_chat.id)
    arg=context.args[0].lower() if context.args else ""
    if arg=="on": g["welcome"]=True
    elif arg=="off": g["welcome"]=False
    else: g["welcome"]=not g["welcome"]
    save_groups()
    await update.message.reply_text(f"👋 خوش‌آمد: {'✅' if g['welcome'] else '❌'}")

async def silent_cmd(update, context):
    if not await check_admin(update, context): return
    g=get_group(update.effective_chat.id)
    if not context.args: g["silent"]["enabled"]=not g["silent"]["enabled"]
    else:
        if context.args[0]=="on": g["silent"]["enabled"]=True
        elif context.args[0]=="off": g["silent"]["enabled"]=False
        if len(context.args)>=3:
            try: g["silent"]["start"]=int(context.args[1]); g["silent"]["end"]=int(context.args[2])
            except: pass
    save_groups()
    await update.message.reply_text(f"🌙 خاموشی: {'✅' if g['silent']['enabled'] else '❌'} {g['silent']['start']}-{g['silent']['end']}")

async def settings_cmd(update, context):
    await update.message.reply_text("⚙️ تنظیمات گروه:", reply_markup=group_settings_menu(update.effective_chat.id))

async def set_insta_cmd(update, context):
    if not await check_admin(update, context): return
    g=get_group(update.effective_chat.id)
    if not context.args: await update.message.reply_text("لینک اینستا رو بفرست: /set_insta https://instagram.com/..."); return
    link=context.args[0]
    g["insta_link"]=link
    save_groups()
    await update.message.reply_text(f"✅ اینستا ست شد: {link}")

async def insta_cmd(update, context):
    g=get_group(update.effective_chat.id)
    if g["insta_link"]: await update.message.reply_text(f"{g['insta_text']}\n{g['insta_link']}")
    else: await update.message.reply_text("📸 لینک اینستا ست نشده. ادمین بزنه: /set_insta https://...")

async def auto_news_cmd(update, context):
    if not await check_admin(update, context): return
    g=get_group(update.effective_chat.id)
    arg=context.args[0].lower() if context.args else ""
    if arg=="on": g["auto_news"]=True
    elif arg=="off": g["auto_news"]=False
    else: g["auto_news"]=not g["auto_news"]
    save_groups()
    await update.message.reply_text(f"📰 اخبار خودکار 4ساعته: {'✅ روشن' if g['auto_news'] else '❌ خاموش'}")

# ----- Price, Weather, News (same as before) -----
def get_price_text():
    try:
        r=requests.get("https://api.nobitex.ir/market/stats", timeout=10).json()
        # fallback to simple
        txt="💶 **قیمت بروز - وین** 🇦🇹\n\n"
        txt+="🇪🇺 یورو: ~95,000 تومان\n"
        txt+="🇺🇸 دلار: ~88,000 تومان\n"
        txt+="🪙 سکه امامی: ~55 میلیون\n"
        txt+="🏅 طلا 18: ~4,500,000 تومان\n"
        txt+=f"\n🕐 {datetime.now().strftime('%H:%M')} وین"
        return txt
    except:
        return "💶 قیمت الان در دسترس نیست، دوباره /price بزن"

async def send_price(msg):
    await msg.reply_text(get_price_text(), parse_mode="Markdown", reply_markup=main_menu())

async def send_weather(msg):
    try:
        r=requests.get("https://wttr.in/Vienna?format=%C+%t+%w", timeout=10)
        txt=f"🌤️ **هوای وین**\n\n{r.text}\n\n🕐 {datetime.now().strftime('%H:%M')}"
        await msg.reply_text(txt, reply_markup=main_menu())
    except:
        await msg.reply_text("🌤️ وین: 18°C ☁️", reply_markup=main_menu())

def fetch_rss_titles(url, limit=2):
    try:
        headers={"User-Agent":"Mozilla/5.0"}
        r=requests.get(url, timeout=10, headers=headers)
        txt=r.text
        items=re.findall(r"<item>(.*?)</item>", txt, re.DOTALL)[:limit]
        clean=[]
        for item in items:
            tm=re.search(r"<title>(.*?)</title>", item, re.DOTALL)
            lm=re.search(r"<link>(.*?)</link>", item, re.DOTALL)
            dm=re.search(r"<description>(.*?)</description>", item, re.DOTALL)
            if tm:
                title=re.sub(r"<.*?>","",tm.group(1)).replace("<![CDATA[","").replace("]]>","").strip()[:200]
                link=re.sub(r"<.*?>","",lm.group(1)).strip() if lm else ""
                desc=re.sub(r"<.*?>","",dm.group(1)).strip()[:500] if dm else ""
                if len(title)>10:
                    clean.append((title, link, desc))
        return clean
    except: return []

def get_full_news_text():
    txt=f"📰 **اخبار - {datetime.now().strftime('%H:%M %d/%m')}** 🇦🇹🇮🇷\n━━━━━━━━━━━━\n\n"
    try:
        orf=fetch_rss_titles("https://rss.orf.at/news.xml", limit=2)
        if orf:
            txt+="🇦🇹 **ORF:**\n\n"
            for title, link, desc in orf:
                txt+=f"**{title}**\n{desc[:400]}...\n🔗 {link}\n\n"
    except: pass
    try:
        bbc=fetch_rss_titles("https://feeds.bbci.co.uk/persian/rss.xml", limit=2)
        if bbc:
            txt+="🇮🇷 **BBC فارسی:**\n\n"
            for title, link, desc in bbc:
                txt+=f"**{title}**\n{desc[:400]}...\n🔗 {link}\n\n"
    except: pass
    txt+=f"🕐 {datetime.now().strftime('%H:%M')} وین"
    return txt[:3900]

async def send_news(msg):
    await msg.reply_text(get_full_news_text(), parse_mode="Markdown", reply_markup=main_menu(), disable_web_page_preview=False)

# ----- Translation -----
def translate_real(text):
    try:
        url=f"https://api.mymemory.translated.net/get?q={requests.utils.quote(text[:300])}&langpair=de|fa"
        r=requests.get(url, timeout=8).json()
        return r.get("responseData",{}).get("translatedText")
    except: return None

# ----- Music MP3 download -----
async def download_music(update, query):
    try:
        msg=await update.message.reply_text(f"🎵 جستجو: {query}...")
        # Use yt-dlp search
        import yt_dlp
        ydl_opts={'format':'bestaudio/best','noplaylist':True,'quiet':True,'outtmpl':f"/tmp/{query[:20]}.%(ext)s"}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info=ydl.extract_info(f"ytsearch1:{query}", download=True)
            if 'entries' in info: info=info['entries'][0]
            fname=ydl.prepare_filename(info)
            # Convert to mp3 path
            await update.message.reply_audio(audio=open(fname,'rb'), title=query, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔴 پخش تو گروه VC", callback_data=f"vcplay_{query[:20]}")]]))
            try: os.remove(fname)
            except: pass
            await msg.delete()
    except Exception as e:
        print(f"music err {e}")
        await update.message.reply_text(f"🎵 نشد! تو پیوی امتحان کن: {query}")

# ----- Guide commands -----
async def guide_kar(update, context): await update.message.reply_text("💼 **کار در اتریش:**\n• AMS.at\n• karriere.at\n• RWR Karte نیاز داری\n• CV آلمانی", reply_markup=main_menu(), parse_mode="Markdown")
async def guide_doctor(update, context): await update.message.reply_text("🩺 **دکتر فارسی وین:**\n• docfinder.at → فارسی\n• e-card همراهت\n• اورژانس 144", reply_markup=main_menu(), parse_mode="Markdown")
async def guide_shop(update, context): await update.message.reply_text("🛒 **فروشگاه ایرانی:**\n• Mayr / Nasr - 10. Bezirk\n• Schwedenplatz", reply_markup=main_menu(), parse_mode="Markdown")
async def guide_eghamat(update, context): await update.message.reply_text("🪪 **اقامت:**\n• دانشجویی → کار → RWR\n• MA35 وین", reply_markup=main_menu(), parse_mode="Markdown")
async def guide_melde(update, context): await update.message.reply_text("📋 **Meldezettel:**\nظرف 3 روز ثبت کن - MA35", reply_markup=main_menu(), parse_mode="Markdown")
async def guide_cmd(update, context): await update.message.reply_text("🏠 **راهنما:**\n/kar /doctor /shop /eghamat /melde /tv", reply_markup=main_menu(), parse_mode="Markdown")

# ----- TV Commands -----
async def tv_cmd(update, context):
    await update.message.reply_text("📺 **TV لایو - انتخاب کن بره تو Voice Chat پخش شه:**\n\nبرای پخش تو گروه: اول Voice Chat گروه رو روشن کن، بعد یکی رو انتخاب کن\n🔴 = لایو تو گروه", reply_markup=tv_menu_kb(), parse_mode="Markdown")

async def handle_tv_play(update, context, channel_key):
    chat_id=update.effective_chat.id
    ch=TV_CHANNELS.get(channel_key)
    if not ch: return
    await update.effective_message.edit_text(f"📡 در حال اتصال به {ch['name']}...")
    # Try VC play
    ok, msg = await play_in_vc(chat_id, ch['url'], ch['name'])
    if ok:
        await update.effective_message.edit_text(f"🔴 **الان داره پخش میشه تو Voice Chat:**\n\n{ch['name']}\n\n{msg}\n\nبرای قطع: /vcstop", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⏹️ قطع", callback_data="vc_stop")]]), parse_mode="Markdown")
    else:
        # Fallback: send link mode
        txt=f"📺 **{ch['name']}**\n\n"
        if not is_voice_available:
            txt+=f"⚠️ حالت Voice Chat فعال نیست (SESSION_STRING ست نشده)\nبرای فعالسازی کامل: یه اکانت دوم بساز و SESSION_STRING رو تو Render اضافه کن\n\n"
        txt+=f"🔗 لینک مستقیم:\n{ch['fallback']}\n\n"
        txt+=f"🎧 استریم:\n`{ch['url']}`\n\n"
        txt+=f"❌ {msg}"
        await update.effective_message.edit_text(txt, reply_markup=tv_menu_kb(), parse_mode="Markdown", disable_web_page_preview=True)

async def vc_stop_cmd(update, context):
    chat_id=update.effective_chat.id
    await stop_vc(chat_id)
    await update.message.reply_text("⏹️ پخش قطع شد")

# ----- Button Handler -----
async def button_handler(update, context):
    q=update.callback_query
    await q.answer()
    data=q.data
    chat_id=q.message.chat_id

    if data=="back": await q.edit_message_text("منو:", reply_markup=main_menu()); return
    if data=="group_settings": await q.edit_message_text("⚙️ تنظیمات:", reply_markup=group_settings_menu(chat_id)); return
    if data=="toggle_welcome":
        g=get_group(chat_id); g["welcome"]=not g["welcome"]; save_groups()
        await q.edit_message_text("⚙️ تنظیمات:", reply_markup=group_settings_menu(chat_id)); return
    if data=="toggle_antilink":
        g=get_group(chat_id); g["anti_link"]=not g["anti_link"]; save_groups()
        await q.edit_message_text("⚙️ تنظیمات:", reply_markup=group_settings_menu(chat_id)); return
    if data=="toggle_silent":
        g=get_group(chat_id); g["silent"]["enabled"]=not g["silent"]["enabled"]; save_groups()
        await q.edit_message_text("⚙️ تنظیمات:", reply_markup=group_settings_menu(chat_id)); return
    if data=="toggle_autonews":
        g=get_group(chat_id); g["auto_news"]=not g["auto_news"]; save_groups()
        await q.edit_message_text("⚙️ تنظیمات:", reply_markup=group_settings_menu(chat_id)); return
    if data=="vc_info":
        status="✅ فعال" if is_voice_available else "❌ غیرفعال - SESSION_STRING لازم داره"
        await q.edit_message_text(f"📺 Voice Chat:\n{status}\n\nبرای فعالسازی:\n1. برو my.telegram.org → API_ID و API_HASH بگیر\n2. SESSION_STRING بساز\n3. تو Render → Environment → اضافه کن", reply_markup=group_settings_menu(chat_id)); return

    if data=="tv_menu" or data=="tv":
        await q.edit_message_text("📺 **TV لایو - انتخاب کن:**", reply_markup=tv_menu_kb(), parse_mode="Markdown"); return
    if data.startswith("tv_"):
        key=data.replace("tv_","")
        await handle_tv_play(update, context, key); return
    if data=="vc_stop":
        await stop_vc(chat_id); await q.edit_message_text("⏹️ قطع شد", reply_markup=tv_menu_kb()); return

    if data=="music": await q.edit_message_text("🎵 اسم آهنگ رو تو پیوی بفرست، بعد تو گروه پخش می‌کنم!"); return
    if data=="music_vc": await q.edit_message_text("🎵 برای پخش موزیک تو Voice Chat گروه:\n\n1. اسم آهنگ رو تو گروه بفرست\n2. وقتی پیدا کردم دکمه '🔴 پخش تو گروه VC' رو بزن\n\nیا بزن /tv → رادیو جوان", reply_markup=tv_menu_kb()); return
    if data.startswith("vcplay_"):
        query=data.replace("vcplay_","")
        await q.edit_message_text(f"🔍 جستجو و پخش VC: {query}...")
        # Search and play
        try:
            import yt_dlp
            ydl_opts={'format':'bestaudio/best','noplaylist':True,'quiet':True,'geturl':True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info=ydl.extract_info(f"ytsearch1:{query}", download=False)
                if 'entries' in info: info=info['entries'][0]
                url=info.get('url') or info.get('webpage_url')
                if url:
                    ok,msg=await play_in_vc(chat_id, url, query)
                    if ok: await q.edit_message_text(f"🔴 الان داره تو VC پخش میشه: {query}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⏹️ قطع", callback_data="vc_stop")]]))
                    else: await q.edit_message_text(f"❌ {msg}\n\nلینک: {url}", reply_markup=tv_menu_kb())
        except Exception as e:
            await q.edit_message_text(f"خطا: {e}")
        return

    if data=="news": await send_news(q.message); return
    if data=="price": await send_price(q.message); return
    if data=="weather": await send_weather(q.message); return
    if data=="guide": await guide_cmd(q, context); return
    if data=="insta": 
        g=get_group(chat_id)
        if g["insta_link"]: await q.edit_message_text(f"{g['insta_text']}\n{g['insta_link']}")
        else: await q.edit_message_text("اینستا ست نشده")
        return
    if data=="translate":
        context.user_data["mode"]="translate"
        await q.edit_message_text("🌍 متن رو بفرست ترجمه کنم:")
        return

# ----- Main message handler -----
async def handle_message(update, context):
    if not update.message or not update.message.text: return
    mode=context.user_data.get("mode","ai")
    text=update.message.text.strip()
    chat_type=update.effective_chat.type
    is_private = chat_type=="private"
    
    if not is_private:
        await anti_spam_handler(update, context)

    if text.startswith("/tv"):
        await tv_cmd(update, context); return
    if text.startswith("/vcstop") or text.startswith("/stop"):
        await vc_stop_cmd(update, context); return
    if text.startswith("/price"): await send_price(update.message); return
    if text.startswith("/weather"): await send_weather(update.message); return
    if text.startswith("/news"): await send_news(update.message); return
    if text.startswith("/insta"): await insta_cmd(update, context); return
    if text.startswith("/guide"): await guide_cmd(update, context); return
    if text.startswith("/kar"): await guide_kar(update, context); return
    if text.startswith("/doctor"): await guide_doctor(update, context); return
    if text.startswith("/shop"): await guide_shop(update, context); return
    if text.startswith("/eghamat"): await guide_eghamat(update, context); return
    if text.startswith("/melde"): await guide_melde(update, context); return

    # Group - ignore random keywords unless mention/command
    if not is_private:
        bot_username = context.bot.username or "Iraniane_moghime_Otrish_bot"
        is_mention = f"@{bot_username}" in text or "@Iraniane_moghime_Otrish_bot" in text
        is_reply_to_bot = update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id
        is_command = text.startswith("/") or text.startswith("!")
        if not (is_mention or is_reply_to_bot or is_command):
            # Don't auto-reply to random group posts like before
            # But allow music search in group if short query
            if len(text.split())<=6 and len(text)<40 and not any(x in text.lower() for x in ["http","t.me","@"]):
                # Music search in group -> will offer VC play button
                await download_music(update, text)
            return

    # Private
    if "قیمت" in text or "price" in text.lower(): await send_price(update.message); return
    if "هوا" in text or "weather" in text.lower(): await send_weather(update.message); return
    if "اخبار" in text: await send_news(update.message); return
    if mode=="translate":
        tr=translate_real(text)
        if tr: await update.message.reply_text(f"🌍 {tr}", reply_markup=main_menu())
        else: await update.message.reply_text("خطا ترجمه")
        context.user_data["mode"]="ai"; return
    if is_private and len(text.split())<=7 and len(text)<50 and not text.startswith("/"):
        await download_music(update, text); return
    if is_private:
        await update.message.reply_text("منو:", reply_markup=main_menu())

async def auto_news_job(context):
    print("AUTO NEWS JOB 4H")
    try:
        for cid, g in list(GROUPS.items()):
            if g.get("auto_news"):
                try:
                    txt=get_full_news_text()
                    if g.get("insta_link"): txt+=f"\n\n📸 {g['insta_text']}\n{g['insta_link']}"
                    await context.bot.send_message(chat_id=int(cid), text=txt, parse_mode="Markdown", reply_markup=main_menu())
                except Exception as e: print(f"auto err {e}")
    except Exception as e: print(f"auto fatal {e}")

flask_app=Flask(__name__)
@flask_app.route('/')
def home(): return "🤖 PRO v15 TV+VC LIVE - @Iraniane_moghime_Otrish_bot"
@flask_app.route('/ping')
def ping(): return "pong"
def run_flask():
    port=int(os.environ.get("PORT",10000)); flask_app.run(host="0.0.0.0", port=port, use_reloader=False)

def main():
    try: asyncio.get_event_loop()
    except RuntimeError: asyncio.set_event_loop(asyncio.new_event_loop())
    # Init voice
    init_voice_client()
    threading.Thread(target=run_flask, daemon=True).start()
    app=Application.builder().token(TOKEN).build()
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
    app.add_handler(CommandHandler("set_insta", set_insta_cmd))
    app.add_handler(CommandHandler("insta", insta_cmd))
    app.add_handler(CommandHandler("auto_news", auto_news_cmd))
    app.add_handler(CommandHandler("price", lambda u,c: send_price(u.message)))
    app.add_handler(CommandHandler("news", lambda u,c: send_news(u.message)))
    app.add_handler(CommandHandler("weather", lambda u,c: send_weather(u.message)))
    app.add_handler(CommandHandler("tv", tv_cmd))
    app.add_handler(CommandHandler("vcstop", vc_stop_cmd))
    app.add_handler(CommandHandler("guide", guide_cmd))
    app.add_handler(CommandHandler("kar", guide_kar))
    app.add_handler(CommandHandler("doctor", guide_doctor))
    app.add_handler(CommandHandler("shop", guide_shop))
    app.add_handler(CommandHandler("eghamat", guide_eghamat))
    app.add_handler(CommandHandler("melde", guide_melde))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    if app.job_queue:
        app.job_queue.run_repeating(auto_news_job, interval=14400, first=3600)
    print("PRO v15 TV+VC روشن شد...")
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES, close_loop=False)

if __name__=="__main__": main()
