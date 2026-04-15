import os
import yt_dlp

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

TOKEN = os.environ.get("BOT_TOKEN")


# ───────── START ─────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎬 یوتیوب گردی", callback_data="youtube")]
    ]

    await update.message.reply_text(
        "👋 سلام!\nلینک یوتیوب رو بفرست تا کیفیت انتخاب کنی.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ───────── BUTTON ─────────
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "youtube":
        await query.message.reply_text("📩 لینک یوتیوب رو بفرست:")


# ───────── GET VIDEO INFO (NO DOWNLOAD) ─────────
def get_formats(url):
    ydl_opts = {
        "quiet": True,
        "skip_download": True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

        formats = []
        for f in info["formats"]:
            if f.get("height"):
                if f["height"] in [360, 480, 720, 1080]:
                    formats.append((f["height"], f["format_id"]))

        # حذف تکراری‌ها
        seen = {}
        for h, fid in formats:
            seen[h] = fid

        return seen


# ───────── DOWNLOAD ─────────
def download_video(url, format_id):
    ydl_opts = {
        "format": format_id,
        "outtmpl": "video.%(ext)s",
        "noplaylist": True,
        "quiet": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)


# ───────── MESSAGE (URL RECEIVER) ─────────
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text

    if "youtube.com" not in url and "youtu.be" not in url:
        await update.message.reply_text("❌ فقط لینک یوتیوب بفرست.")
        return

    context.user_data["url"] = url

    formats = get_formats(url)

    keyboard = [
        [InlineKeyboardButton(f"🎬 {h}p", callback_data=f"q_{fid}")]
        for h, fid in formats.items()
    ]

    await update.message.reply_text(
        "📊 کیفیت رو انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ───────── QUALITY SELECT ─────────
async def quality_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    format_id = query.data.replace("q_", "")
    url = context.user_data.get("url")

    if not url:
        await query.message.reply_text("❌ لینک پیدا نشد دوباره بفرست.")
        return

    await query.message.reply_text("⏳ در حال دانلود...")

    try:
        file_path = download_video(url, format_id)

        await query.message.reply_video(video=open(file_path, "rb"))

        os.remove(file_path)

    except Exception as e:
        await query.message.reply_text(f"❌ خطا:\n{e}")


# ───────── MAIN ─────────
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button, pattern="youtube"))
    app.add_handler(CallbackQueryHandler(quality_handler, pattern="q_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
