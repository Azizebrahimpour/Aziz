
"""
PRO v7 ULTIMATE - GROUP MANAGER + INSTA + AUTO NEWS EVERY 2H
@Iraniane_moghime_Otrish_bot
Features: welcome, anti-link, ban/kick/mute, silent, insta link, auto news 2h, real price, real news
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
            "welcome_text": "سلام {name} عزیز 👋 به گروه ایرانیان مقیم اتریش خوش اومدی 🇦🇹🇮🇷",
            "insta_link": "",  # لینک اینستاگرام مدیر
            "insta_text": "پیج اینستاگرام ما رو فالو کنید 👇",
            "auto_news": False
        }
        save_groups()
    # backward compatibility
    if "insta_link" not in GROUPS[cid]:
        GROUPS[cid]["insta_link"] = ""
        GROUPS[cid]["insta_text"] = "پیج اینستاگرام ما رو فالو کنید 👇"
        GROUPS[cid]["auto_news"] = False
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
        [InlineKeyboardButton("🎵 پخش آهنگ", callback_data="music"), InlineKeyboardButton("📰 اخبار کامل", callback_data="news")],
        [InlineKeyboardButton("💶 قیمت بروز ارز و طلا", callback_data="price"), InlineKeyboardButton("🌤️ هوای وین", callback_data="weather")],
        [InlineKeyboardButton("📸 اینستاگرام", callback_data="insta"), InlineKeyboardButton("🌍 مترجم", callback_data="translate")],
        [InlineKeyboardButton("🏠 راهنمای اتریش", callback_data="guide"), InlineKeyboardButton("⚙️ تنظیمات گروه", callback_data="group_settings")],
    ])

def group_settings_menu(chat_id):
    g = get_group(chat_id)
    insta_status = "✅" if g["insta_link"] else "❌"
    auto_status = "✅" if g.get("auto_news") else "❌"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"👋 خوش‌آمد: {'✅' if g['welcome'] else '❌'}", callback_data="toggle_welcome")],
        [InlineKeyboardButton(f"🔗 ضد لینک: {'✅' if g['anti_link'] else '❌'}", callback_data="toggle_antilink")],
        [InlineKeyboardButton(f"🌙 خاموشی: {'✅' if g['silent']['enabled'] else '❌'} {g['silent']['start']}-{g['silent']['end']}", callback_data="toggle_silent")],
        [InlineKeyboardButton(f"📸 اینستا: {insta_status}", callback_data="set_insta_btn")],
        [InlineKeyboardButton(f"📰 اخبار خودکار 2ساعته: {auto_status}", callback_data="toggle_autonews")],
        [InlineKeyboardButton("🔙 منو", callback_data="back")],
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        await update.message.reply_text("سلام! ربات گروه ایرانیان 🇦🇹 /help", reply_markup=main_menu())
        return
    name = update.effective_user.first_name
    await update.message.reply_text(
        f"سلام {name} 👋\n**PRO v7 ULTIMATE** 🇦🇹🇮🇷\n\n🎵 MP3\n📰 اخبار کامل\n💶 قیمت بروز\n🌤️ هوا\n📸 اینستا لینک\n📰 اخبار خودکار هر 2 ساعت\n👋 خوش‌آمد\n🔗 ضد لینک\n🚫 بن/کیک/سکوت\n🌙 خاموشی",
        reply_markup=main_menu(), parse_mode="Markdown"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = """
🛠️ **راهنما v7**

**ادمین (ریپلای):**
/ban /unban /kick
/mute 1h /unmute

**تنظیمات گروه:**
/anti_link on/off
/welcome on/off
/silent on 23 7
/settings
/set_insta https://instagram.com/yourpage
/insta → نمایش اینستا
/auto_news on/off → اخبار هر 2 ساعت

**عمومی:** /price /news /weather /insta
🎵 اسم آهنگ
"""
    await update.message.reply_text(txt, parse_mode="Markdown", reply_markup=main_menu())

# --- خوش آمدگویی ---
async def welcome_new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    g = get_group(update.effective_chat.id)
    if not g["welcome"]: return
    for m in update.message.new_chat_members:
        try:
            txt = g["welcome_text"].format(name=m.first_name)
            if g["insta_link"]:
                txt += f"\n\n{g['insta_text']}\n{g['insta_link']}"
            await update.message.reply_text(txt)
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
        # اجازه اینستا خود مدیر رو بده
        if g["insta_link"] and g["insta_link"].lower() in text:
            return
        try:
            await update.message.delete()
            await context.bot.send_message(update.effective_chat.id, f"🔗 لینک {update.effective_user.first_name} حذف شد")
            return
        except: pass

# --- دستورات ادمین ---
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
        await update.message.reply_text("ریپلای کن و /mute"); return
    try:
        dur = 1
        if context.args:
            t = context.args[0].lower()
            if "h" in t: dur = int(t.replace("h",""))
            elif "m" in t: dur = float(t.replace("m",""))/60
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
        g["anti_link"] = False
        await update.message.reply_text("🔗 ضد لینک ❌ خاموش")
    else:
        g["anti_link"] = True
        await update.message.reply_text("🔗 ضد لینک ✅ روشن")
    save_groups()

async def welcome_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update, context): return
    g = get_group(update.effective_chat.id)
    if context.args and context.args[0].lower() == "off":
        g["welcome"] = False
        await update.message.reply_text("👋 خوش‌آمد ❌ خاموش")
    else:
        g["welcome"] = True
        await update.message.reply_text("👋 خوش‌آمد ✅ روشن")
    save_groups()

async def silent_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update, context): return
    g = get_group(update.effective_chat.id)
    if not context.args or context.args[0].lower() == "off":
        g["silent"]["enabled"] = False
        await update.message.reply_text("🌙 خاموشی ❌ خاموش")
        save_groups()
        return
    try:
        if context.args[0].lower() == "on":
            s = int(context.args[1]) if len(context.args)>1 else 23
            e = int(context.args[2]) if len(context.args)>2 else 7
        else:
            s = int(context.args[0])
            e = int(context.args[1]) if len(context.args)>1 else 7
        g["silent"]["enabled"] = True
        g["silent"]["start"] = s
        g["silent"]["end"] = e
        await update.message.reply_text(f"🌙 خاموشی ✅ {s} تا {e}")
        save_groups()
    except Exception as e:
        await update.message.reply_text(f"مثال: /silent on 23 7\nخطا: {e}")

# --- اینستا ---


async def set_insta_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update, context):
        await update.message.reply_text("فقط ادمین"); return
    if not context.args:
        await update.message.reply_text("بزن: /set_insta https://instagram.com/aziz.12230\nیا /set_insta off برای حذف\n\nنکته: فقط لینک بفرست")
        return
    g = get_group(update.effective_chat.id)
    raw = " ".join(context.args).strip()
    if raw.lower() in ["off","delete","حذف","remove"]:
        g["insta_link"] = ""
        await update.message.reply_text("📸 لینک اینستا حذف شد ❌")
        save_groups()
        return
    # استخراج لینک - حتی اگر اشتباه دو بار نوشت
    match = re.search(r"(https?://[\w./?=_-]+)", raw)
    if match:
        link = match.group(1)
    else:
        username = raw.split()[0].replace("@","").replace("instagram.com/","").replace("https://","").replace("http://","").strip("/").strip()
        if not username:
            username = "aziz.12230"
        link = f"https://instagram.com/{username}"
    link = link.split()[0].replace("set_insta","").strip()
    if "instagram.com" not in link and "instagr.am" not in link:
        await update.message.reply_text(f"❌ لینک نامعتبر\nدرست: https://instagram.com/aziz.12230")
        return
    g["insta_link"] = link
    await update.message.reply_text(f"✅ لینک اینستا ذخیره شد:\n{link}\n\nحالا /insta بزن", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📸 باز کردن اینستاگرام", url=link)]]))
    save_groups()

async def insta_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # تشخیص chat_id برای هم Update و هم CallbackQuery
        if isinstance(update, Update):
            chat_id = update.effective_chat.id
            msg = update.message
        else:  # CallbackQuery
            chat_id = update.message.chat.id
            msg = update.message
            try:
                await update.answer()
            except:
                pass
        g = get_group(chat_id)
        if not g.get("insta_link"):
            await msg.reply_text("📸 هنوز لینک اینستا تنظیم نشده\nادمین بزنه: /set_insta https://instagram.com/aziz.12230", reply_markup=main_menu())
            return
        link = g["insta_link"].strip().split()[0]
        txt = f"{g['insta_text']}\n\n📸 **اینستاگرام ما:**\n{link}"
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("📸 باز کردن اینستاگرام", url=link)]])
        await msg.reply_text(txt, reply_markup=kb, parse_mode="Markdown")
    except Exception as e:
        print(f"insta err {e}")
        try:
            await update.message.reply_text(f"📸 اینستا: {get_group(update.effective_chat.id).get('insta_link','')}")
        except:
            pass


async def auto_news_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update, context): return
    g = get_group(update.effective_chat.id)
    if not context.args or context.args[0].lower() == "off":
        g["auto_news"] = False
        await update.message.reply_text("📰 اخبار خودکار هر 2 ساعت ❌ خاموش شد")
    else:
        g["auto_news"] = True
        await update.message.reply_text("📰 اخبار خودکار هر 2 ساعت ✅ روشن شد\nربات هر 2 ساعت اخبار مهم رو خودکار میفرسته")
    save_groups()

async def settings_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update, context):
        await update.message.reply_text("فقط ادمین"); return
    await update.message.reply_text("⚙️ تنظیمات گروه v7:", reply_markup=group_settings_menu(update.effective_chat.id))

# --- اخبار کامل ---
def fetch_rss_titles(url, limit=4):
    try:
        r = requests.get(url, timeout=8, headers={"User-Agent":"Mozilla/5.0"})
        titles = re.findall(r"<title>(.*?)</title>", r.text, re.DOTALL)
        links = re.findall(r"<link>(.*?)</link>", r.text, re.DOTALL)
        clean = []
        for i in range(1, min(limit+1, len(titles))):
            t = titles[i]
            t = re.sub(r"<.*?>","",t)
            t = t.replace("<![CDATA[","").replace("]]>","").replace("&quot;","\"").replace("&amp;","&").replace("*","").strip()
            if len(t) < 10: continue
            link = ""
            if i < len(links):
                link = re.sub(r"<.*?>","",links[i]).strip().replace("<![CDATA[","").replace("]]>","").strip()
            clean.append((t[:120], link))
        return clean
    except Exception as e:
        print(f"rss err {url} {e}")
        return []

def get_full_news_text():
    txt = f"📰 **اخبار خودکار - {datetime.now().strftime('%H:%M %d/%m')}** 🇦🇹🇮🇷\n\n"
    orf_news = fetch_rss_titles("https://rss.orf.at/orf.xml", limit=4)
    if orf_news:
        txt += "🇦🇹 **اتریش - ORF:**\n"
        for t, link in orf_news:
            txt += f"• {t}\n"
            if link and "http" in link:
                txt += f"  {link}\n"
            txt += "\n"
    else:
        txt += "🇦🇹 ORF: https://orf.at\n\n"
    bbc_news = fetch_rss_titles("https://feeds.bbci.co.uk/persian/rss.xml", limit=4)
    if bbc_news:
        txt += "🇮🇷 **ایران/جهان - BBC:**\n"
        for t, link in bbc_news:
            txt += f"• {t}\n"
            if link:
                txt += f"  {link}\n"
            txt += "\n"
    if len(txt) > 3900:
        txt = txt[:3900] + "\n..."
    return txt

async def send_news(update_obj):
    try:
        target = update_obj.message if hasattr(update_obj, 'message') else update_obj
        await target.reply_text("📰 در حال دریافت اخبار بروز... ⏳")
        txt = get_full_news_text()
        await target.reply_text(txt, reply_markup=main_menu(), parse_mode="Markdown", disable_web_page_preview=True)
        try:
            if hasattr(update_obj,'answer'): await update_obj.answer()
        except: pass
    except Exception as e:
        print(f"news fatal {e}")
        try:
            t = update_obj.message if hasattr(update_obj,'message') else update_obj
            await t.reply_text("📰 ORF: https://orf.at\nBBC: https://bbc.com/persian", reply_markup=main_menu())
        except: pass

async def send_price(update_obj):
    try:
        target = update_obj.message if hasattr(update_obj, 'message') else update_obj
        txt = f"💶 **قیمت بروز - {datetime.now().strftime('%H:%M %d/%m')} ✅**\n\n"
        got_live = False
        try:
            r = requests.get("https://nerkh.jahankhahan.shop/data/live.json", timeout=8).json()
            rates = r.get("rates", {})
            date = r.get("date",""); time_ = r.get("time","")
            euro = rates.get("euro", 0); dollar = rates.get("dollar", 0); gold18 = rates.get("gold", 0)
            emami = rates.get("emami", rates.get("sekkeh", 0)); ounce = r.get("ounce", 0)
            if euro:
                txt += f"🇪🇺 **یورو آزاد:** {euro:,} تومان\n"; got_live = True
            if dollar:
                txt += f"🇺🇸 **دلار آزاد:** {dollar:,} تومان\n"; got_live = True
            if gold18:
                txt += f"\n🥇 **طلا 18:** {gold18:,} تومان/گرم\n"
            if emami:
                txt += f"🪙 **سکه امامی:** {emami:,} تومان\n"
            if ounce:
                txt += f"🌍 **انس:** ${ounce:,.0f}\n"
            if got_live:
                txt += f"\n🕐 {date} {time_}\n_منبع: Nerkhsanj_"
            else:
                raise Exception("no rates")
        except Exception as e:
            print(f"nerkh err {e}")
            txt += "خطا دریافت قیمت - /price دوباره بزن\n"
        await target.reply_text(txt, reply_markup=main_menu(), parse_mode="Markdown")
        try:
            if hasattr(update_obj,'answer'): await update_obj.answer()
        except: pass
    except Exception as e:
        print(f"price fatal {e}")

async def send_weather(update_obj):
    try:
        target = update_obj.message if hasattr(update_obj,'message') else update_obj
        try:
            url = "https://api.open-meteo.com/v1/forecast?latitude=48.2082&longitude=16.3738&current=temperature_2m,wind_speed_10m&timezone=Europe/Vienna"
            r = requests.get(url, timeout=6).json()
            temp = r['current']['temperature_2m']; wind = r['current']['wind_speed_10m']
            txt = f"🌤️ **هوای وین: {temp}°C**\n💨 باد: {wind} km/h"
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
    msg = await update.message.reply_text(f"🔍 `{q}` دانلود... (30ث)", parse_mode="Markdown")
    try:
        import yt_dlp, glob
        tmpdir = tempfile.mkdtemp()
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
        await update.message.reply_text(f"▶️ لینک: {url}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    data = q.data
    print(f"BTN {data}")
    try: await q.answer()
    except: pass
    if data == "news": await send_news(q)
    elif data == "price": await send_price(q)
    elif data == "weather": await send_weather(q)
    elif data == "insta": await insta_cmd(q, context)
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
        await q.message.reply_text("⚙️ تنظیمات گروه v7:", reply_markup=group_settings_menu(q.message.chat.id))
    elif data == "set_insta_btn":
        if not await check_admin(update, context): return
        await q.message.reply_text("📸 لینک اینستات رو بفرست:\n/set_insta https://instagram.com/aziz.12230\nیا /set_insta off برای حذف")
    elif data.startswith("toggle_"):
        if not await check_admin(update, context): return
        g = get_group(q.message.chat.id)
        if data=="toggle_welcome": g["welcome"]=not g["welcome"]
        elif data=="toggle_antilink": g["anti_link"]=not g["anti_link"]
        elif data=="toggle_silent": g["silent"]["enabled"]=not g["silent"]["enabled"]
        elif data=="toggle_autonews": g["auto_news"]=not g.get("auto_news", False)
        save_groups()
        try: await q.edit_message_reply_markup(reply_markup=group_settings_menu(q.message.chat.id))
        except: await q.message.reply_text("✅", reply_markup=group_settings_menu(q.message.chat.id))
    elif data=="back": await q.message.reply_text("منو:", reply_markup=main_menu())


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    mode = context.user_data.get("mode","ai")
    text = update.message.text.strip()
    print(f"MSG {mode} {text} chat={update.effective_chat.type}")
    # ضد لینک چک برای گروه
    if update.effective_chat.type != "private":
        await anti_spam_handler(update, context)
        g = get_group(update.effective_chat.id)
        if g["anti_link"] and any(x in text.lower() for x in ["http://","https://","t.me/"]):
            if g.get("insta_link") and g["insta_link"].lower() in text.lower():
                pass
            else:
                return

    # --- دستورات عمومی برای همه (گروه و پیوی) ---
    if "قیمت" in text or text.startswith("/price") or "price" in text.lower():
        await send_price(update.message); return
    if "هوا" in text or text.startswith("/weather") or "weather" in text.lower():
        await send_weather(update.message); return
    if "اخبار" in text or text.startswith("/news"):
        await send_news(update.message); return
    if text.startswith("/insta") or "اینستا" in text:
        await insta_cmd(update, context); return

    # ترجمه
    if mode=="translate":
        tr=translate_real(text)
        if tr: await update.message.reply_text(f"🌍 `{text}`\n⬇️\n**{tr}**", parse_mode="Markdown", reply_markup=main_menu())
        else: await update.message.reply_text("خطا ترجمه", reply_markup=main_menu())
        context.user_data["mode"]="ai"; return

    low=text.lower()

    # --- راهنمای اتریش برای همه ---
    if "meldezettel" in low or "ملدز" in low:
        await update.message.reply_text("📋 **Meldezettel:**\nظرف 3 روز بعد از ورود باید تو Magistrat ثبت کنی. مدرک: قرارداد خونه + پاسپورت\n🏠 محل: MA 35", reply_markup=main_menu(), parse_mode="Markdown"); return
    if "کار" in text or "job" in low or "arbeit" in low:
        await update.message.reply_text("💼 **کار در اتریش:**\n• AMS.at - سایت کاریابی دولتی\n• karriere.at / StepStone.at\n• برای ایرانیا: نیاز به Rot-Weiß-Rot Karte یا اجازه کار\n• CV به آلمانی بنویس", reply_markup=main_menu()); return
    if "دکتر" in text or "پزشک" in text or "arzt" in low or "doctor" in low:
        await update.message.reply_text("🩺 **دکتر فارسی در وین:**\n• Dr. Fard - 01/123...\n• جستجو: docfinder.at → فارسی\n• برای بیمه: e-card همراهت باشه\n• اورژانس: 144", reply_markup=main_menu()); return
    if "فروشگاه ایرانی" in text or "سوپر ایرانی" in text or "فروشگاه" in text:
        await update.message.reply_text("🛒 **فروشگاه ایرانی وین:**\n• Mayr / Nasr / Iran Shop - 10. Bezirk\n• Schwedenplatz - چندتا مغازه ایرانی\n• برنج، زعفرون، سبزی قورمه همه دارن", reply_markup=main_menu()); return
    if "اقامت" in text or "aufenthalt" in low or "ویزا" in text:
        await update.message.reply_text("🪪 **اقامت اتریش:**\n• دانشجویی → کار → RWR Karte\n• تمدید 3 ماه قبل از اتمام\n• MA 35 برای وین\n• وکیل مهاجرتی بگیر", reply_markup=main_menu()); return
    if "راهنمای اتریش" in text or text.lower()=="راهنما" or "guide" in low or "🏠" in text:
        await update.message.reply_text(
            "🏠 **راهنمای اتریش - همه چی اینجاست:**\n\n"
            "📋 Meldezettel\n💼 کار\n🩺 دکتر فارسی\n🛒 فروشگاه ایرانی\n🪪 اقامت\n\n"
            "فقط کلمه‌ش رو بفرست، مثلا بنویس: `کار` یا `دکتر` یا `Meldezettel`",
            reply_markup=main_menu(), parse_mode="Markdown"
        ); return

    # موزیک برای همه - هم گروه هم پیوی
    if len(text.split())<=7 and len(text)<50 and not text.startswith("/"):
        # اگر متن راهنما نیست، موزیکه
        if not any(x in low for x in ["meldezettel","اقامت","فروشگاه","دکتر","کار","guide","راهنما"]):
            await download_music(update, text); return

    if update.effective_chat.type=="private":
        await update.message.reply_text("منو:", reply_markup=main_menu())


# --- اخبار خودکار هر 2 ساعت ---
async def auto_news_job(context: ContextTypes.DEFAULT_TYPE):
    print("AUTO NEWS JOB running...")
    try:
        # همه گروه هایی که auto_news روشن دارن
        for cid, g in list(GROUPS.items()):
            if g.get("auto_news"):
                try:
                    txt = get_full_news_text()
                    # اضافه اینستا
                    if g.get("insta_link"):
                        txt += f"\n\n📸 {g['insta_text']}\n{g['insta_link']}"
                    await context.bot.send_message(chat_id=int(cid), text=txt, parse_mode="Markdown", disable_web_page_preview=True, reply_markup=main_menu())
                    print(f"auto news sent to {cid}")
                    await asyncio.sleep(1)
                except Exception as e:
                    print(f"auto news err {cid} {e}")
    except Exception as e:
        print(f"auto job fatal {e}")

flask_app = Flask(__name__)
@flask_app.route('/')
def home():
    return "🤖 PRO v7 ULTIMATE - INSTA + AUTO NEWS 2H - @Iraniane_moghime_Otrish_bot"
@flask_app.route('/ping')
def ping():
    return "pong"

def run_flask():
    port=int(os.environ.get("PORT",10000))
    flask_app.run(host="0.0.0.0", port=port, use_reloader=False)

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
        time.sleep(600)

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
    app.add_handler(CommandHandler("set_insta", set_insta_cmd))
    app.add_handler(CommandHandler("insta", insta_cmd))
    app.add_handler(CommandHandler("auto_news", auto_news_cmd))
    app.add_handler(CommandHandler("price", lambda u,c: send_price(u.message)))
    app.add_handler(CommandHandler("news", lambda u,c: send_news(u.message)))
    app.add_handler(CommandHandler("weather", lambda u,c: send_weather(u.message)))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    # JobQueue - اخبار هر 2 ساعت
    if app.job_queue:
        app.job_queue.run_repeating(auto_news_job, interval=7200, first=7200)
        print("Auto news job scheduled every 2h")
    else:
        print("JobQueue not available")
    print("PRO v7 ULTIMATE - INSTA + AUTO NEWS روشن شد...")
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES, close_loop=False)

if __name__ == "__main__":
    main()
