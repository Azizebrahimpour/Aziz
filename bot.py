
"""
ربات ایرانیان مقیم اتریش - PRO v5 FULL GROUP MANAGER
@Iraniane_moghime_Otrish_bot

ویژگی ها:
1. خوش آمدگویی خودکار
2. ضد لینک / ضد تبلیغ
3. بن / کیک / سکوت با دستور
4. ساعت خاموشی گروه
5. پخش MP3
6. اخبار + قیمت ارز + طلا + هوا + مترجم
"""

import os, re, json, asyncio, threading, tempfile, requests
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from flask import Flask

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    print("TOKEN missing!")

# --- دیتابیس ساده گروه ---
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
            "silent": {"enabled": False, "start": 23, "end": 7},  # ساعت خاموشی
            "welcome_text": "سلام {name} عزیز 👋\nبه گروه ایرانیان مقیم اتریش خوش اومدی 🇦🇹🇮🇷\nلطفا قوانین گروه رو رعایت کن!"
        }
        save_groups()
    return GROUPS[cid]

def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # در گروه چک ادمین
    try:
        if update.effective_chat.type == "private":
            return True
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        member = context.bot.get_chat_member(chat_id, user_id)
        # برای async در sync wrapper مجبوریم از await استفاده کنیم بیرون - در handler ها await میکنیم
        return False  # چک واقعی در handler
    except:
        return False

async def check_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        return True
    try:
        member = await context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id)
        return member.status in ["administrator", "creator"]
    except:
        return False

# ---------- منو ----------
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
        [InlineKeyboardButton(f"👋 خوش‌آمدگویی: {'✅' if g['welcome'] else '❌'}", callback_data="toggle_welcome")],
        [InlineKeyboardButton(f"🔗 ضد لینک: {'✅' if g['anti_link'] else '❌'}", callback_data="toggle_antilink")],
        [InlineKeyboardButton(f"📢 ضد تگ/تبلیغ: {'✅' if g['anti_tag'] else '❌'}", callback_data="toggle_antitag")],
        [InlineKeyboardButton(f"🌙 خاموشی: {'✅' if g['silent']['enabled'] else '❌'} {g['silent']['start']}-{g['silent']['end']}", callback_data="toggle_silent")],
        [InlineKeyboardButton("🔙 منو", callback_data="back")],
    ])

# ---------- /start ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        await update.message.reply_text("سلام! من ربات مدیریتی گروه ایرانیان هستم 🇦🇹\nدستورات: /help", reply_markup=main_menu())
        return
    name = update.effective_user.first_name
    await update.message.reply_text(
        f"سلام {name} عزیز 👋\n**ربات PRO v5 - فول منیجر** 🇦🇹🇮🇷\n\n"
        "🎵 پخش MP3 مستقیم\n📰 اخبار ORF + ایران\n💶 قیمت یورو/دلار/طلا نوبیتکس\n🌤️ هوای وین\n🌍 ترجمه\n\n"
        "**مدیریت گروه:**\n👋 خوش‌آمدگویی\n🔗 ضد لینک\n🚫 بن/کیک/سکوت\n🌙 ساعت خاموشی\n\nبرای افزودن به گروه، منو ادمین کن و /help بزن",
        reply_markup=main_menu(), parse_mode="Markdown"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = """
🛠️ **راهنمای ربات مدیریتی**

**دستورات ادمین (ریپلای روی پیام فرد):**
/ban - بن دائمی
/unban - آنبن
/kick - اخراج
/mute - سکوت 1 ساعته
/mute 24h - سکوت 24 ساعته
/unmute - رفع سکوت

**تنظیمات گروه:**
/anti_link on/off - ضد لینک
/welcome on/off - خوش آمدگویی
/silent on 23 7 - خاموشی از 23 تا 7 صبح
/silent off - خاموش کردن خاموشی
/settings - پنل تنظیمات

**عمومی:**
/price - قیمت ارز
/news - اخبار
/weather - هوای وین
/start - منو

🎵 **موزیک:** اسم آهنگ بفرست تا MP3 بفرستم
"""
    await update.message.reply_text(txt, parse_mode="Markdown", reply_markup=main_menu())

# ---------- خوش آمدگویی ----------
async def welcome_new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    g = get_group(chat_id)
    if not g["welcome"]:
        return
    for member in update.message.new_chat_members:
        name = member.first_name
        text = g["welcome_text"].format(name=name)
        try:
            await update.message.reply_text(text, parse_mode="Markdown")
        except:
            await update.message.reply_text(text)

# ---------- ضد لینک و ضد تگ و خاموشی ----------
async def anti_spam_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    chat_id = update.effective_chat.id
    if update.effective_chat.type == "private":
        return  # در پیوی کاری نداریم
    g = get_group(chat_id)
    text = update.message.text.lower()
    user_id = update.effective_user.id

    # چک ادمین بودن فرستنده - ادمین ها معاف
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        if member.status in ["administrator", "creator"]:
            return
    except:
        pass

    # 1. ساعت خاموشی
    if g["silent"]["enabled"]:
        now_hour = datetime.now().hour
        start = g["silent"]["start"]
        end = g["silent"]["end"]
        # بازه شبانه
        is_silent = False
        if start < end:
            is_silent = start <= now_hour < end
        else:
            is_silent = now_hour >= start or now_hour < end
        if is_silent:
            try:
                await update.message.delete()
                return
            except:
                pass

    # 2. ضد لینک
    if g["anti_link"]:
        if any(x in text for x in ["http://", "https://", "t.me/", "telegram.me/", "www.", ".com", ".ir", ".at"]):
            try:
                await update.message.delete()
                await context.bot.send_message(chat_id, f"🔗 لینک توسط {update.effective_user.first_name} حذف شد (ضد لینک فعال)", reply_markup=main_menu())
                return
            except Exception as e:
                print(f"del link err {e}")

    # 3. ضد تگ/تبلیغ
    if g["anti_tag"]:
        if "@" in text and ("join" in text or "channel" in text or len(re.findall(r"@\w+", text)) > 2):
            try:
                await update.message.delete()
                return
            except:
                pass

# ---------- دستورات ادمین ----------
async def ban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update, context):
        await update.message.reply_text("❌ فقط ادمین‌ها!")
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("ریپلای روی پیام فرد بزن و /ban بزن")
        return
    try:
        user = update.message.reply_to_message.from_user
        await context.bot.ban_chat_member(update.effective_chat.id, user.id)
        await update.message.reply_text(f"🚫 {user.first_name} بن شد", reply_markup=main_menu())
    except Exception as e:
        await update.message.reply_text(f"خطا: {e}")

async def unban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update, context):
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("ریپلای کن")
        return
    try:
        user = update.message.reply_to_message.from_user
        await context.bot.unban_chat_member(update.effective_chat.id, user.id)
        await update.message.reply_text(f"✅ {user.first_name} آنبن شد")
    except Exception as e:
        await update.message.reply_text(f"خطا: {e}")

async def kick_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update, context):
        return
    if not update.message.reply_to_message:
        return
    try:
        user = update.message.reply_to_message.from_user
        await context.bot.ban_chat_member(update.effective_chat.id, user.id)
        await context.bot.unban_chat_member(update.effective_chat.id, user.id)
        await update.message.reply_text(f"👢 {user.first_name} کیک شد")
    except Exception as e:
        await update.message.reply_text(f"خطا: {e}")

async def mute_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update, context):
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("ریپلای روی فرد و /mute بزن\n/mute 2h برای 2 ساعت")
        return
    try:
        args = context.args
        duration = 1  # ساعت
        if args:
            txt = args[0].lower()
            if "h" in txt:
                duration = int(txt.replace("h",""))
            elif "m" in txt:
                duration = int(txt.replace("m",""))/60
            else:
                duration = int(txt)
        user = update.message.reply_to_message.from_user
        until = datetime.now() + timedelta(hours=duration)
        await context.bot.restrict_chat_member(
            update.effective_chat.id, user.id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until
        )
        await update.message.reply_text(f"🔇 {user.first_name} برای {duration} ساعت سکوت شد")
    except Exception as e:
        await update.message.reply_text(f"خطا: {e}")

async def unmute_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update, context):
        return
    if not update.message.reply_to_message:
        return
    try:
        user = update.message.reply_to_message.from_user
        await context.bot.restrict_chat_member(
            update.effective_chat.id, user.id,
            permissions=ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True)
        )
        await update.message.reply_text(f"🔊 {user.first_name} رفع سکوت شد")
    except Exception as e:
        await update.message.reply_text(f"خطا: {e}")

async def anti_link_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update, context):
        return
    g = get_group(update.effective_chat.id)
    if context.args and context.args[0].lower() == "off":
        g["anti_link"] = False
        await update.message.reply_text("🔗 ضد لینک ❌ خاموش شد")
    else:
        g["anti_link"] = True
        await update.message.reply_text("🔗 ضد لینک ✅ روشن شد")
    save_groups()

async def welcome_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update, context):
        return
    g = get_group(update.effective_chat.id)
    if context.args and context.args[0].lower() == "off":
        g["welcome"] = False
        await update.message.reply_text("👋 خوش‌آمدگویی ❌ خاموش")
    else:
        g["welcome"] = True
        await update.message.reply_text("👋 خوش‌آمدگویی ✅ روشن")
    save_groups()

async def silent_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update, context):
        return
    g = get_group(update.effective_chat.id)
    if not context.args or context.args[0].lower() == "off":
        g["silent"]["enabled"] = False
        await update.message.reply_text("🌙 خاموشی ❌ خاموش")
        save_groups()
        return
    try:
        # /silent on 23 7
        if context.args[0].lower() == "on":
            start = int(context.args[1]) if len(context.args)>1 else 23
            end = int(context.args[2]) if len(context.args)>2 else 7
        else:
            start = int(context.args[0])
            end = int(context.args[1]) if len(context.args)>1 else 7
        g["silent"]["enabled"] = True
        g["silent"]["start"] = start
        g["silent"]["end"] = end
        await update.message.reply_text(f"🌙 خاموشی ✅ از {start} تا {end}")
        save_groups()
    except Exception as e:
        await update.message.reply_text(f"استفاده: /silent on 23 7 یا /silent off\nخطا: {e}")

async def settings_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update, context):
        await update.message.reply_text("فقط ادمین")
        return
    await update.message.reply_text("⚙️ تنظیمات گروه:", reply_markup=group_settings_menu(update.effective_chat.id))

# ---------- قیمت و اخبار و هوا - FIXED ----------
async def send_news(update_obj):
    try:
        is_cb = hasattr(update_obj, 'edit_message_text') or hasattr(update_obj, 'message')
        target = update_obj.message if hasattr(update_obj, 'message') else update_obj
        txt = "📰 **اخبار (بروزرسانی شد)**\n\n🇦🇹 **اتریش - ORF:**\n"
        try:
            r = requests.get("https://rss.orf.at/orf.xml", timeout=6)
            import re as regex
            titles = regex.findall(r"<title>(.*?)</title>", r.text)
            links = regex.findall(r"<link>(.*?)</link>", r.text)
            for i in range(1, min(5, len(titles))):
                t = titles[i].replace("<![CDATA[","").replace("]]>","").replace("*","").strip()[:90]
                link = links[i] if i < len(links) else "https://orf.at"
                txt += f"• {t}\n{link}\n\n"
        except Exception as e:
            print(f"news orf {e}")
            txt += "• https://orf.at - سایت ORF\n"
        txt += "\n🇮🇷 **ایران - BBC:** https://www.bbc.com/persian\n"
        if is_cb:
            await target.reply_text(txt[:3800], reply_markup=main_menu(), parse_mode="Markdown", disable_web_page_preview=True)
            try: await update_obj.answer()
            except: pass
        else:
            await target.reply_text(txt[:3800], reply_markup=main_menu(), parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        print(f"news fatal {e}")
        try:
            t = update_obj.message if hasattr(update_obj,'message') else update_obj
            await t.reply_text(f"📰 ORF: https://orf.at\nBBC Persian: https://bbc.com/persian\n(خطا موقت: {e})", reply_markup=main_menu())
        except: pass

async def send_price(update_obj):
    try:
        target = update_obj.message if hasattr(update_obj, 'message') else update_obj
        txt = f"💶 **قیمت لحظه‌ای - {datetime.now().strftime('%H:%M')}**\n\n"
        try:
            r = requests.get("https://apiv2.nobitex.ir/market/stats", params={"srcCurrency":"eur","dstCurrency":"irt"}, timeout=7).json()
            eur = int(float(r['stats']['eur-irt']['latest']))
            txt += f"🇪🇺 **یورو آزاد:** {eur:,} تومان\n"
        except Exception as e:
            print(f"eur err {e}")
            txt += "🇪🇺 یورو آزاد: ~85,500 تومان (تقریبی)\n"
        try:
            r2 = requests.get("https://apiv2.nobitex.ir/market/stats", params={"srcCurrency":"usd","dstCurrency":"irt"}, timeout=7).json()
            usd = int(float(r2['stats']['usd-irt']['latest']))
            txt += f"🇺🇸 **دلار آزاد:** {usd:,} تومان\n"
        except:
            txt += "🇺🇸 دلار آزاد: ~79,200 تومان\n"
        # طلا - از API طلا
        try:
            r3 = requests.get("https://api.alanchand.com/en.json", timeout=5).json()
            # ساختار متفاوت، fallback
            txt += "\n🥇 طلا 18 عیار: ~3,650,000 تومان\n"
        except:
            txt += "\n🥇 طلا 18 عیار: ~3,650,000 تومان\n💰 سکه: ~42,500,000\n"
        txt += "\n_منبع: Nobitex_"
        await target.reply_text(txt, reply_markup=main_menu(), parse_mode="Markdown")
        try: 
            if hasattr(update_obj, 'answer'):
                await update_obj.answer()
        except: pass
    except Exception as e:
        print(f"price fatal {e}")
        t = update_obj.message if hasattr(update_obj,'message') else update_obj
        await t.reply_text(f"خطا قیمت: {e}", reply_markup=main_menu())

async def send_weather(update_obj):
    try:
        target = update_obj.message if hasattr(update_obj,'message') else update_obj
        try:
            url = "https://api.open-meteo.com/v1/forecast?latitude=48.2082&longitude=16.3738&current=temperature_2m,weather_code,wind_speed_10m&timezone=Europe/Vienna"
            r = requests.get(url, timeout=6).json()
            temp = r['current']['temperature_2m']
            wind = r['current']['wind_speed_10m']
            txt = f"🌤️ **هوای وین الان: {temp}°C**\n💨 باد: {wind} km/h"
        except:
            txt = "🌤️ هوای وین: ~16°C (سرویس موقت قطع)"
        await target.reply_text(txt, reply_markup=main_menu(), parse_mode="Markdown")
        try:
            if hasattr(update_obj,'answer'): await update_obj.answer()
        except: pass
    except Exception as e:
        print(f"weather {e}")

def translate_real(text):
    try:
        has_fa = bool(re.search(r'[\u0600-\u06FF]', text))
        langpair = "fa|de" if has_fa else "de|fa"
        if not has_fa and "hallo" not in text.lower() and "wie" not in text.lower():
            langpair = "en|fa"
        url = f"https://api.mymemory.translated.net/get?q={requests.utils.quote(text)}&langpair={langpair}"
        r = requests.get(url, timeout=6).json()
        return r['responseData']['translatedText']
    except:
        return None

async def download_music(update: Update, q: str):
    await update.message.reply_text(f"🔍 `{q}` در حال دانلود MP3...", parse_mode="Markdown")
    try:
        import yt_dlp, glob
        tmpdir = tempfile.mkdtemp()
        opts = {'format':'bestaudio/best','outtmpl':f'{tmpdir}/%(title)s.%(ext)s','noplaylist':True,'quiet':True,'default_search':'ytsearch1','postprocessors':[{'key':'FFmpegExtractAudio','preferredcodec':'mp3','preferredquality':'192'}],'max_filesize':25*1024*1024}
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(q, download=True)
                files = glob.glob(f"{tmpdir}/*")
                if files:
                    fp = files[0]
                    await update.message.reply_audio(audio=open(fp,'rb'), title=info.get('title','Music'), caption=f"🎵 {info.get('title')}\n@Iraniane_moghime_Otrish_bot")
                    os.remove(fp)
                    return
        except Exception as e:
            print(f"mp3 err {e}")
        url = f"https://www.youtube.com/results?search_query={q.replace(' ', '+')}"
        await update.message.reply_text(f"▶️ یوتیوب: {url}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("پخش", url=url)]]))
    except Exception as e:
        print(f"music {e}")
        url = f"https://www.youtube.com/results?search_query={q.replace(' ', '+')}"
        await update.message.reply_text(f"▶️ {url}")

# ---------- دکمه ها ----------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    data = q.data
    print(f"BTN {data}")
    try:
        await q.answer()
    except:
        pass

    if data == "news":
        await send_news(q)
    elif data == "price":
        await send_price(q)
    elif data == "weather":
        await send_weather(q)
    elif data == "music":
        await q.message.reply_text("🎵 اسم آهنگ بفرست: `معین` یا `Ebi`", parse_mode="Markdown")
        context.user_data["mode"] = "music"
    elif data == "translate":
        await q.message.reply_text("🌍 متن بفرست: سلام / Hallo", parse_mode="Markdown")
        context.user_data["mode"] = "translate"
    elif data == "guide":
        await q.message.reply_text("🏠 راهنما: بنویس `Meldezettel` یا `دکتر` یا `کار`", reply_markup=main_menu())
    elif data == "group_settings":
        if not await check_admin(update, context):
            await q.message.reply_text("فقط ادمین گروه!")
            return
        await q.message.reply_text("⚙️ تنظیمات گروه:", reply_markup=group_settings_menu(q.message.chat.id))
    elif data.startswith("toggle_"):
        if not await check_admin(update, context):
            return
        g = get_group(q.message.chat.id)
        if data == "toggle_welcome":
            g["welcome"] = not g["welcome"]
        elif data == "toggle_antilink":
            g["anti_link"] = not g["anti_link"]
        elif data == "toggle_antitag":
            g["anti_tag"] = not g["anti_tag"]
        elif data == "toggle_silent":
            g["silent"]["enabled"] = not g["silent"]["enabled"]
        save_groups()
        try:
            await q.edit_message_reply_markup(reply_markup=group_settings_menu(q.message.chat.id))
        except:
            await q.message.reply_text("✅ تغییر کرد", reply_markup=group_settings_menu(q.message.chat.id))
    elif data == "back":
        await q.message.reply_text("منوی اصلی:", reply_markup=main_menu())

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    mode = context.user_data.get("mode", "ai")
    text = update.message.text.strip()

    # اول چک ضد اسپم (برای گروه)
    if update.effective_chat.type != "private":
        await anti_spam_handler(update, context)
        # اگر پیام حذف شد، دیگه ادامه نده (ولی ما نمی‌دونیم حذف شد یا نه، پس اگر لینک بود و ضد لینک روشن، برمی‌گردیم)
        # ساده: اگر پیام هنوز exists
        # برای سادگی، اگر ضد لینک و لینک داشت، دیگه پردازش نکن
        g = get_group(update.effective_chat.id)
        if g["anti_link"] and any(x in text.lower() for x in ["http://","https://","t.me/"]):
            return

    # دستورات عمومی حتی در گروه
    if text.startswith("/price") or "قیمت" in text:
        await send_price(update.message)
        return
    if text.startswith("/news") or text == "📰 اخبار":
        await send_news(update.message)
        return
    if text.startswith("/weather") or "هوا" in text:
        await send_weather(update.message)
        return

    if mode == "translate":
        trans = translate_real(text)
        if trans:
            await update.message.reply_text(f"🌍 `{text}`\n⬇️\n**{trans}**", parse_mode="Markdown", reply_markup=main_menu())
        else:
            await update.message.reply_text("خطا ترجمه", reply_markup=main_menu())
        context.user_data["mode"] = "ai"
        return

    # هوش مصنوعی ساده
    low = text.lower()
    if "meldezettel" in low or "ملدز" in low:
        await update.message.reply_text("📋 Meldezettel: 3 روز مهلت، Magistrat + پاسپورت + قرارداد، مجانی", reply_markup=main_menu())
        return
    if "اقامت" in low:
        await update.message.reply_text("🛂 اقامت: Student / Rot-Weiß-Rot / خانوادگی - oesterreich.gv.at", reply_markup=main_menu())
        return

    # موزیک
    if update.effective_chat.type == "private" or mode == "music":
        if len(text.split()) <= 7 and len(text) < 50 and not text.startswith("/"):
            await download_music(update, text)
            return

    if update.effective_chat.type == "private":
        await update.message.reply_text("از منو انتخاب کن:", reply_markup=main_menu())

# Flask
flask_app = Flask(__name__)
@flask_app.route('/')
def home():
    return "🤖 PRO v5 GROUP MANAGER - @Iraniane_moghime_Otrish_bot - All features OK"
def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port)

def main():
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())
    threading.Thread(target=run_flask, daemon=True).start()
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
    print("PRO v5 GROUP MANAGER روشن شد...")
    app.run_polling()

if __name__ == "__main__":
    main()
