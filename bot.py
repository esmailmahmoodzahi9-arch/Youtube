import yt_dlp
import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN")

# ------------------- استارت -------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [
        [InlineKeyboardButton("🎬 یوتیوب‌گردی", callback_data="start_youtube")]
    ]

    await update.message.reply_text(
        "سلام 👋\n\nبه ربات یوتیوب‌گردی خوش اومدی 😎\nروی دکمه زیر بزن تا شروع کنیم:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ------------------- سرچ -------------------
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # فقط وقتی کاربر وارد حالت یوتیوب شده
    if not context.user_data.get("search_mode"):
        return

    query = update.message.text

    ydl_opts = {
        "quiet": True,
        "extract_flat": True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch5:{query}", download=False)

    buttons = []

    for entry in info["entries"]:
        title = entry["title"]
        video_id = entry["id"]
        video_url = f"https://www.youtube.com/watch?v={video_id}"

        buttons.append([
            InlineKeyboardButton(
                title[:50],
                callback_data=f"video|{video_url}"
            )
        ])

    await update.message.reply_text(
        "نتایج جستجو:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ------------------- کیفیت‌ها -------------------
def get_formats(url):
    ydl_opts = {"quiet": True}

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    formats = []
    for f in info["formats"]:
        if f.get("height") and f.get("ext") == "mp4":
            formats.append({
                "id": f["format_id"],
                "quality": f"{f['height']}p"
            })

    return formats[:6]

# ------------------- دانلود -------------------
def download_video(url, format_id):
    ydl_opts = {
        "format": format_id,
        "outtmpl": "video.%(ext)s",
        "quiet": True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    for file in os.listdir():
        if file.startswith("video."):
            return file

# ------------------- دکمه‌ها -------------------
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    # ورود به حالت یوتیوب
    if data == "start_youtube":
        context.user_data["search_mode"] = True

        await query.message.reply_text(
            "🔎 حالا اسم ویدیو یا هر چیزی میخوای جستجو کن:"
        )

    # انتخاب ویدیو
    elif data.startswith("video|"):
        url = data.split("|")[1]

        formats = get_formats(url)

        buttons = []
        for f in formats:
            buttons.append([
                InlineKeyboardButton(
                    f["quality"],
                    callback_data=f"dl|{f['id']}|{url}"
                )
            ])

        await query.message.reply_text(
            "کیفیت رو انتخاب کن:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    # دانلود
    elif data.startswith("dl|"):
        _, format_id, url = data.split("|")

        await query.message.reply_text("⏳ در حال دانلود...")

        file_path = download_video(url, format_id)

        await query.message.reply_video(video=open(file_path, "rb"))

        os.remove(file_path)

# ------------------- اجرا -------------------
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search))
app.add_handler(CallbackQueryHandler(handle_buttons))

print("Bot is running...")
app.run_polling()
