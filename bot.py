import os
import yt_dlp

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

TOKEN = os.environ.get("BOT_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🎬 یوتیوب گردی", callback_data="youtube")]]
    await update.message.reply_text(
        "👋 سلام!\nلینک یوتیوب رو بفرست.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("📩 لینک یوتیوب رو بفرست:")


def download(url):
    ydl_opts = {
        "format": "best",
        "outtmpl": "video.%(ext)s",
        "noplaylist": True,
        "quiet": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text

    if "youtube" not in url and "youtu.be" not in url:
        await update.message.reply_text("❌ لینک اشتباهه")
        return

    await update.message.reply_text("⏳ در حال دانلود...")

    try:
        file_path = download(url)
        await update.message.reply_video(video=open(file_path, "rb"))
        os.remove(file_path)
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {e}")


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    app.run_polling()


if __name__ == "__main__":
    main()
