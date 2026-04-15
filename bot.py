import requests
import yt_dlp
import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text

    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={query}&key={YOUTUBE_API_KEY}&maxResults=5&type=video"
    data = requests.get(url).json()

    buttons = []

    for item in data.get("items", []):
        title = item["snippet"]["title"]
        video_id = item["id"]["videoId"]
        video_url = f"https://www.youtube.com/watch?v={video_id}"

        buttons.append([
            InlineKeyboardButton(title[:50], callback_data=f"video|{video_url}")
        ])

    await update.message.reply_text(
        "نتایج:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

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

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data.startswith("video|"):
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

    elif data.startswith("dl|"):
        _, format_id, url = data.split("|")

        await query.message.reply_text("در حال دانلود...")

        file_path = download_video(url, format_id)

        await query.message.reply_video(video=open(file_path, "rb"))

        os.remove(file_path)

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search))
app.add_handler(CallbackQueryHandler(handle_buttons))

app.run_polling()
