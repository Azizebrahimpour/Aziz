
import os, re, asyncio, threading, tempfile, requests, feedparser
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from flask import Flask

TOKEN = os.getenv("TOKEN") or "توکن"

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎵 پخش آهنگ", callback_data="music"), InlineKeyboardButton("📰 اخبار", callback_data="news")],
        [InlineKeyboardButton("💶 قیمت ارز", callback_data="price"), InlineKeyboardButton("🌤️ هوای وین", callback_data="weather")],
        [InlineKeyboardButton("🌍 مترجم", callback_data="translate"), InlineKeyboardButton("🏠 راهنمای اتریش", callback_data="guide")],
        [InlineKeyboardButton("🤖 هوش مصنوعی", callback_data="ai")],
    ])

def music_menu(url):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("▶️ یوتیوب", url=url)],
        [InlineKeyboardButton("🔙 منو", callback_data="back")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name
    await update.message.reply_text(
        f"سلام {name} عزیز 👋\nربات **ایرانیان مقیم اتریش PRO v3** 🇦🇹🇮🇷\n\n"
        "🎵 آهنگ بفرست → MP3\n📰 اخبار ORF\n💶 قیمت نوبیتکس\n🌤️ هوای وین\n🌍 ترجمه\n🏠 راهنما\n🤖 بپرس\n\nمنو:",
        reply_markup=main_menu(), parse_mode="Markdown"
    )

async def send_news(update_obj):
    try:
        is_callback = hasattr(update_obj, 'edit_message_text')
        msg_target = update_obj.message if is_callback else update_obj
        txt = "📰 **اخبار:**\n\n"
        try:
            feed = feedparser.parse("https://rss.orf.at/orf.xml")
            txt += "🇦🇹 **اتریش:**\n"
            for e in feed.entries[:4]:
                title = e.title.replace('*','').replace('_','').replace('`','')
                txt += f"• {title}\n{e.link}\n\n"
        except Exception as e:
            txt += f"خطا ORF: {e}\n"
        try:
            feed2 = feedparser.parse("https://feeds.bbci.co.uk/persian/rss.xml")
            txt += "🇮🇷 **ایران:**\n"
            for e in feed2.entries[:3]:
                title = e.title.replace('*','').replace('_','').replace('`','')
                txt += f"• {title}\n{e.link}\n\n"
        except:
            pass
        if len(txt) > 3900:
            txt = txt[:3900] + "..."
        if is_callback:
            await msg_target.reply_text(txt, reply_markup=main_menu(), parse_mode="Markdown", disable_web_page_preview=True)
            await update_obj.answer("✅")
        else:
            await msg_target.reply_text(txt, reply_markup=main_menu(), parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as ex:
        print(f"news error: {ex}")
        try:
            target = update_obj.message if hasattr(update_obj,'message') else update_obj
            await target.reply_text(f"خطا در اخبار، دوباره بزن: {ex}", reply_markup=main_menu())
        except: pass

async def send_price(update_obj):
    try:
        is_cb = hasattr(update_obj, 'edit_message_text')
        target = update_obj.message if is_cb else update_obj
        txt = f"💶 **قیمت - {datetime.now().strftime('%H:%M')}**\n\n"
        # EUR
        try:
            r = requests.get("https://apiv2.nobitex.ir/market/stats", params={"srcCurrency":"eur","dstCurrency":"irt"}, timeout=12).json()
            eur = int(float(r['stats']['eur-irt']['latest']))
            txt += f"🇪🇺 یورو آزاد: {eur:,} تومان\n"
        except Exception as e:
            print(f"eur nobitex err {e}")
            txt += "🇪🇺 یورو: ~ 85,000 تومان\n"
        try:
            r2 = requests.get("https://apiv2.nobitex.ir/market/stats", params={"srcCurrency":"usd","dstCurrency":"irt"}, timeout=12).json()
            usd = int(float(r2['stats']['usd-irt']['latest']))
            txt += f"🇺🇸 دلار آزاد: {usd:,} تومان\n"
        except:
            txt += "🇺🇸 دلار: ~ 78,000 تومان\n"
        try:
            r3 = requests.get("https://api.exchangerate-api.com/v4/latest/EUR", timeout=8).json()
            txt += f"\n1€ = {r3['rates']['USD']:.2f} $\n"
        except:
            pass
        txt += "\n🥇 طلا 18: ~3.6M تومان\nمنبع: Nobitex"
        if is_cb:
            await target.reply_text(txt, reply_markup=main_menu(), parse_mode="Markdown")
            await update_obj.answer()
        else:
            await target.reply_text(txt, reply_markup=main_menu(), parse_mode="Markdown")
    except Exception as ex:
        print(f"price error {ex}")
        target = update_obj.message if hasattr(update_obj,'message') else update_obj
        await target.reply_text(f"خطا قیمت: {ex}", reply_markup=main_menu())

async def send_weather(update_obj):
    try:
        is_cb = hasattr(update_obj, 'edit_message_text')
        target = update_obj.message if is_cb else update_obj
        url = "https://api.open-meteo.com/v1/forecast?latitude=48.2082&longitude=16.3738&current=temperature_2m,wind_speed_10m,weather_code&timezone=Europe/Vienna"
        r = requests.get(url, timeout=10).json()
        cur = r['current']
        temp = cur['temperature_2m']
        wind = cur['wind_speed_10m']
        code = cur['weather_code']
        wmap = {0:"صاف ☀️",1:"نیمه ابری 🌤️",2:"ابری ☁️",3:"ابری",45:"مه 🌫️",51:"باران ریز 🌧️",61:"باران 🌧️",71:"برف ❄️",95:"رعد و برق ⛈️"}
        desc = wmap.get(code, str(code))
        txt = f"🌤️ **هوای وین - {datetime.now().strftime('%H:%M')}**\n\n🌡️ {temp}°C\n{desc}\n💨 باد: {wind} km/h"
        if is_cb:
            await target.reply_text(txt, reply_markup=main_menu(), parse_mode="Markdown")
            await update_obj.answer()
        else:
            await target.reply_text(txt, reply_markup=main_menu(), parse_mode="Markdown")
    except Exception as ex:
        print(f"weather err {ex}")
        target = update_obj.message if hasattr(update_obj,'message') else update_obj
        await target.reply_text(f"خطا هوا: {ex}", reply_markup=main_menu())

def translate_real(text):
    try:
        has_fa = bool(re.search(r'[\u0600-\u06FF]', text))
        langpair = "fa|de" if has_fa else "de|fa"
        if not has_fa and not any(c in text.lower() for c in ['ä','ö','ü']):
            langpair = "en|fa"
        url = f"https://api.mymemory.translated.net/get?q={requests.utils.quote(text)}&langpair={langpair}"
        r = requests.get(url, timeout=10).json()
        return r['responseData']['translatedText']
    except Exception as e:
        print(f"trans err {e}")
        return None

def ai_answer(text):
    t = text.lower()
    if "meldezettel" in t or "ملدز" in t or "ثبت آدرس" in t:
        return "📋 **Meldezettel:**\nظرف 3 روز بعد اسباب کشی ثبت کن.\n📍 Magistrat منطقه\n📄 پاسپورت + قرارداد خونه + فرم\n💶 مجانی\n🌐 oesterreich.gv.at"
    if "اقامت" in t:
        return "🛂 **اقامت اتریش:**\n• Student\n• Rot-Weiß-Rot Karte (کاری)\n• Familienzusammenführung\nسایت: oesterreich.gv.at"
    if "کار" in t:
        return "💼 **کار وین:**\nams.at (رسمی)\nkarriere.at\nwillhaben.at/jobs\nlinkedin.com"
    if "دکتر" in t:
        return "🩺 **دکتر فارسی:**\nDr. Hosseini 1010\nDr. Rezaei 1150\nجستجو: docfinder.at زبان فارسی"
    if "فروشگاه" in t or "ایرانی" in t:
        return "🛒 **فروشگاه ایرانی:**\nYas Markt 1100 Laxenburger Str 48\nPars Markt 1150 Sechshauser Str"
    return None

async def download_music(update: Update, q: str):
    await update.message.reply_text(f"🔍 `{q}` در حال جستجو...", parse_mode="Markdown")
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
                    await update.message.reply_audio(audio=open(fp,'rb'), title=info.get('title','Music'), caption=f"🎵 {info.get('title')}")
                    os.remove(fp)
                    return
        except Exception as e:
            print(f"mp3 err {e}, try m4a")
            opts2 = {'format':'bestaudio','outtmpl':f'{tmpdir}/%(title)s.%(ext)s','noplaylist':True,'quiet':True,'default_search':'ytsearch1'}
            with yt_dlp.YoutubeDL(opts2) as ydl:
                info = ydl.extract_info(q, download=True)
                files = glob.glob(f"{tmpdir}/*")
                if files:
                    fp = files[0]
                    await update.message.reply_audio(audio=open(fp,'rb'), caption=f"🎵 {info.get('title')}")
                    os.remove(fp)
                    return
        url = f"https://www.youtube.com/results?search_query={q.replace(' ', '+')}"
        await update.message.reply_text("لینک یوتیوب:", reply_markup=music_menu(url))
    except Exception as e:
        print(f"music total err {e}")
        url = f"https://www.youtube.com/results?search_query={q.replace(' ', '+')}"
        await update.message.reply_text(f"لینک: {url}", reply_markup=music_menu(url))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    data = q.data
    print(f"button {data}")
    if data == "news":
        await send_news(q)
    elif data == "price":
        await send_price(q)
    elif data == "weather":
        await send_weather(q)
    elif data == "music":
        await q.answer()
        await q.message.reply_text("🎵 اسم آهنگ بفرست... مثلاً معین حسرت", parse_mode="Markdown")
        context.user_data["mode"] = "music"
    elif data == "translate":
        await q.answer()
        await q.message.reply_text("🌍 متن بفرست تا ترجمه کنم (فارسی↔آلمانی)", parse_mode="Markdown")
        context.user_data["mode"] = "translate"
    elif data == "guide":
        await q.answer()
        txt = "🏠 **راهنمای وین**\nMeldezettel / دکتر ایرانی / کار / فروشگاه\n\nسوالت رو بنویس مثلا: `Meldezettel چیه؟`"
        await q.message.reply_text(txt, reply_markup=main_menu(), parse_mode="Markdown")
    elif data == "ai":
        await q.answer()
        await q.message.reply_text("🤖 بپرس: Meldezettel / اقامت / دکتر / کار / فروشگاه", parse_mode="Markdown")
        context.user_data["mode"] = "ai"
    elif data == "back":
        await q.answer()
        await q.message.reply_text("منوی اصلی:", reply_markup=main_menu())

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.user_data.get("mode", "ai")
    text = update.message.text.strip()
    print(f"msg mode={mode} text={text}")
    if "هوا" in text or "weather" in text.lower():
        await send_weather(update.message)
        return
    if "قیمت" in text or "یورو" in text or "دلار" in text:
        await send_price(update.message)
        return
    if mode == "translate":
        trans = translate_real(text)
        if trans:
            await update.message.reply_text(f"🌍 `{text}`\n⬇️\n**{trans}**", parse_mode="Markdown", reply_markup=main_menu())
        else:
            await update.message.reply_text("خطا در ترجمه", reply_markup=main_menu())
        context.user_data["mode"] = "ai"
        return
    ai_resp = ai_answer(text)
    if ai_resp:
        await update.message.reply_text(ai_resp, parse_mode="Markdown", reply_markup=main_menu())
        return
    # موزیک اگر کوتاه
    if len(text.split()) <= 7 and len(text) < 50:
        await download_music(update, text)
    else:
        await update.message.reply_text("از منو انتخاب کن یا سوال اقامتی بپرس", reply_markup=main_menu())

flask_app = Flask(__name__)
@flask_app.route('/')
def home():
    return "🤖 PRO v3 - @Iraniane_moghime_Otrish_bot"
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
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("PRO v3 روشن شد...")
    app.run_polling()

if __name__ == "__main__":
    main()
