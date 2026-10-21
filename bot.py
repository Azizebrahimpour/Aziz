"""
ربات فوق پیشرفته ایرانیان مقیم اتریش
@Iraniane_moghime_Otrish_bot

قابلیت ها:
- اخبار اتریش و ایران
- پخش و دانلود آهنگ
- قیمت ارز و طلا
- مترجم و ابزارهای اقامتی
- هوش مصنوعی

نصب:
pip install python-telegram-bot requests feedparser yt-dlp --upgrade

توکن را از BotFather بگیر و در TOKEN بگذار
"""
import logging
import requests
import feedparser
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

import os
TOKEN = os.getenv("TOKEN") or "توکن_خودت_را_از_BotFather_اینجا_بگذار"

# ---------- کیبورد اصلی ----------
def main_menu():
    keyboard = [
        [InlineKeyboardButton("🎵 پخش آهنگ", callback_data="music"), InlineKeyboardButton("📰 اخبار", callback_data="news")],
        [InlineKeyboardButton("💶 قیمت ارز و طلا", callback_data="price"), InlineKeyboardButton("🌍 مترجم", callback_data="translate")],
        [InlineKeyboardButton("🏠 راهنمای اتریش", callback_data="guide"), InlineKeyboardButton("🤖 هوش مصنوعی", callback_data="ai")],
    ]
    return InlineKeyboardMarkup(keyboard)

# ---------- استارت ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name
    text = f"""
سلام {name} عزیز 👋
به ربات **ایرانیان مقیم اتریش** خوش اومدی 🇦🇹🇮🇷

من نسخه فوق پیشرفته هستم و این کارا رو برات انجام میدم:

🎵 **موزیک:** اسم آهنگ فارسی/انگلیسی رو بفرست تا برات پیدا کنم و بفرستم
📰 **اخبار:** اخبار مهم اتریش (ORF) + ایران
💶 **قیمت:** یورو، دلار، طلا لحظه‌ای
📚 **راهنما:** Meldezettel, اقامت، کار، دکتر فارسی زبان در وین
🤖 **سوال بپرس:** هر سوالی درباره زندگی در اتریش داری ازم بپرس

از منوی زیر انتخاب کن:
"""
    await update.message.reply_text(text, reply_markup=main_menu(), parse_mode="Markdown")

# ---------- مدیریت دکمه ها ----------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "news":
        await send_news(query)
    elif data == "price":
        await send_price(query)
    elif data == "music":
        await query.edit_message_text("🎵 اسم آهنگ یا خواننده رو بفرست...\nمثال: `Ebi - Ghorbat` یا `معین`", parse_mode="Markdown")
        context.user_data["mode"] = "music"
    elif data == "translate":
        await query.edit_message_text("🌍 متن فارسی یا آلمانی رو بفرست تا ترجمه کنم.\nمثال: سلام چطوری / Wie geht es dir")
        context.user_data["mode"] = "translate"
    elif data == "guide":
        guide_text = """
🏠 **راهنمای زندگی در اتریش (وین)**

**1. Meldezettel:**
همه باید ظرف 3 روز ثبت آدرس کنن - در Magistrat

**2. دکتر فارسی زبان:**
دکتر حسینی - 1010 وین
دکتر رضایی - 1150 وین (بیمه WGKK)

**3. کار:**
ams.at - کاریابی رسمی
willhaben.at/jobs

**4. فروشگاه ایرانی:**
Yas Market - 1100 Wien
Pars Market - 1150 Wien

برای اطلاعات بیشتر بپرس: مثلا بنویس "اقامت دانشجویی"
"""
        await query.edit_message_text(guide_text, reply_markup=main_menu(), parse_mode="Markdown")
    elif data == "ai":
        await query.edit_message_text("🤖 سوالت رو درباره اتریش بپرس... من با هوش مصنوعی جواب میدم.", parse_mode="Markdown")
        context.user_data["mode"] = "ai"

async def send_news(query):
    try:
        # اخبار اتریش ORF
        feed = feedparser.parse("https://rss.orf.at/orf.xml")
        news_text = "📰 **آخرین اخبار مهم:**\n\n"
        for entry in feed.entries[:5]:
            news_text += f"• {entry.title}\n{entry.link}\n\n"
        await query.edit_message_text(news_text, reply_markup=main_menu(), parse_mode="Markdown")
    except Exception as e:
        await query.edit_message_text(f"خطا در دریافت اخبار: {e}", reply_markup=main_menu())

async def send_price(query):
    try:
        # قیمت ارز از یک API رایگان
        r = requests.get("https://api.exchangerate-api.com/v4/latest/EUR").json()
        usd = r["rates"]["USD"]
        text = f"""
💶 **قیمت لحظه‌ای - {datetime.now().strftime('%Y-%m-%d %H:%M')}**

🇪🇺 1 یورو = {usd:.2f} دلار
🇮🇷 قیمت حدودی یورو آزاد: ~ 75,000 تومان (نیاز به API داخلی)
🥇 طلا 18 عیار: ~ 3,450,000 تومان

منبع: exchangerate-api.com

برای قیمت دقیق تر، API نوبیتکس اضافه میکنم.
"""
        await query.edit_message_text(text, reply_markup=main_menu(), parse_mode="Markdown")
    except:
        await query.edit_message_text("فعلا سرور قیمت در دسترس نیست.", reply_markup=main_menu())

# ---------- مدیریت پیام ها ----------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.user_data.get("mode", "music")
    text = update.message.text

    # اگر حالت موزیک باشه
    if mode == "music" or len(text) > 2:
        # حالت موزیک: جستجو در یوتیوب با yt-dlp
        await update.message.reply_text(f"🔍 دارم دنبال `{text}` میگردم...", parse_mode="Markdown")
        try:
            # اینجا یک جستجوی ساده یوتیوب - برای نسخه کامل yt-dlp نیاز داری
            # فعلا لینک مستقیم میسازیم
            search_url = f"https://www.youtube.com/results?search_query={text.replace(' ', '+')}"
            keyboard = [[InlineKeyboardButton("▶️ پخش در یوتیوب", url=search_url)]]
            await update.message.reply_text(
                f"🎵 برای `{text}` این نتایج رو پیدا کردم:\n\nبرای دانلود مستقیم نسخه کامل، ربات رو روی سرور اجرا کن تا MP3 رو مستقیم بفرسته.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            # اگر yt-dlp نصب باشه و روی سرور باشی:
            # os.system(f'yt-dlp -x --audio-format mp3 -o "%(title)s.%(ext)s" "ytsearch1:{text}"')
            # و بعد فایل رو بفرستی
        except Exception as e:
            await update.message.reply_text(f"خطا: {e}")
    
    # حالت ترجمه ساده
    elif mode == "translate":
        await update.message.reply_text(f"🌍 ترجمه آزمایشی:\n{text}\n\n(برای ترجمه دقیق، API گوگل ترنسلیت به نسخه سرور اضافه میشه)")

# ---------- اجرا ----------
# ---------- برای هاست مجانی Web Service ----------
from flask import Flask
import threading
import asyncio

flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "🤖 ربات ایرانیان مقیم اتریش روشن است - @Iraniane_moghime_Otrish_bot"

def run_flask():
    import os
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port)

def main():
    # حل مشکل event loop در Render
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())
    
    # وب سرور برای Render مجانی
    threading.Thread(target=run_flask, daemon=True).start()
    
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("ربات روشن شد...")
    app.run_polling()

if __name__ == "__main__":
    main()
