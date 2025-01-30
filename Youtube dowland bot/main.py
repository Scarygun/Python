import logging
import os
import mimetypes
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters.command import CommandStart
import asyncio
import yt_dlp
from aiogram.types import FSInputFile

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Bot token
BOT_TOKEN = "API_TOKEN"

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Create downloads directory
os.makedirs("downloads", exist_ok=True)

# Keyboard for quality selection
def media_quality_keyboard(url: str, platform: str):
    keyboard = []
    if platform == "youtube":
        qualities = ["1080p", "720p", "480p", "360p", "240p", "144p"]
        for quality in qualities:
            keyboard.append([InlineKeyboardButton(text=f"{quality} \u26a1", callback_data=f"{platform}_{quality}_{url}")])
        keyboard.append([InlineKeyboardButton(text="\ud83c\udfb5 MP3 \u26a1", callback_data=f"{platform}_mp3_{url}")])
    elif platform == "instagram":
        keyboard.append([InlineKeyboardButton(text="\ud83c\udfa5 Video \u26a1", callback_data=f"{platform}_video_{url}")])
        keyboard.append([InlineKeyboardButton(text="\ud83c\udfb5 MP3 \u26a1", callback_data=f"{platform}_mp3_{url}")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Download YouTube video or audio
def download_youtube_media(url, quality="360p", media_type="video"):
    try:
        if media_type == "mp3":
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': 'downloads/%(title)s.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': False,
            }
        else:
            quality_map = {
                "1080p": "bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4]",
                "720p": "bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/best[ext=mp4]",
                "480p": "bestvideo[ext=mp4][height<=480]+bestaudio[ext=m4a]/best[ext=mp4]",
                "360p": "bestvideo[ext=mp4][height<=360]+bestaudio[ext=m4a]/best[ext=mp4]",
                "240p": "bestvideo[ext=mp4][height<=240]+bestaudio[ext=m4a]/best[ext=mp4]",
                "144p": "bestvideo[ext=mp4][height<=144]+bestaudio[ext=m4a]/best[ext=mp4]",
            }
            selected_format = quality_map.get(quality, "best[ext=mp4]")
            ydl_opts = {
                'format': selected_format,
                'outtmpl': 'downloads/%(title)s.%(ext)s',
                'noplaylist': True,
                'quiet': False,
                'merge_output_format': 'mp4',
            }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info_dict)
            if media_type == "mp3":
                file_path = file_path.rsplit('.', 1)[0] + '.mp3'

            if os.path.exists(file_path):
                logger.info(f"Media downloaded: {file_path}")
                return file_path
            else:
                logger.warning(f"File not found after download: {file_path}")
                return None

    except Exception as e:
        logger.error(f"Error downloading media: {e}")
        return None

# Download Instagram media
def download_instagram_media(url, media_type="video"):
    try:
        ydl_opts = {
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'quiet': False,
        }

        if media_type == "mp3":
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info_dict)
            if media_type == "mp3":
                file_path = file_path.rsplit('.', 1)[0] + '.mp3'

            if os.path.exists(file_path):
                logger.info(f"Instagram media downloaded: {file_path}")
                return file_path
            else:
                logger.warning(f"File not found after download: {file_path}")
                return None

    except Exception as e:
        logger.error(f"Error downloading Instagram media: {e}")
        return None

# Start command
@dp.message(CommandStart())
async def start_command(message: Message):
    await message.reply("Welcome to the Media Downloader Bot! Send a YouTube or Instagram link to get started.")

# Handle URLs
@dp.message(F.text.startswith("http"))
async def handle_url(message: Message):
    url = message.text.strip()
    logger.info(f"Received URL: {url}")

    if "youtube.com" in url or "youtu.be" in url:
        platform = "youtube"
    elif "instagram.com" in url:
        platform = "instagram"
    else:
        await message.reply("Unsupported platform. Please provide a YouTube or Instagram link.")
        return

    await message.reply("Choose the download option:", reply_markup=media_quality_keyboard(url, platform))

# Handle quality selection
@dp.callback_query()
async def handle_quality_selection(callback_query: CallbackQuery):
    data = callback_query.data
    parts = data.split("_")
    platform = parts[0]
    media_type = parts[1]
    url = "_".join(parts[2:])

    await callback_query.message.edit_text(f"📥 Downloading {media_type}...")

    try:
        if platform == "youtube":
            file_path = download_youtube_media(url, quality=media_type if media_type != "mp3" else "360p", media_type=media_type)
        elif platform == "instagram":
            file_path = download_instagram_media(url, media_type=media_type)

        if file_path and os.path.exists(file_path):
            if os.path.getsize(file_path) <= 50 * 1024 * 1024:  # 50MB limit
                input_file = FSInputFile(file_path)
                mime_type, _ = mimetypes.guess_type(file_path)

                if mime_type and mime_type.startswith("audio"):
                    await callback_query.message.answer_audio(input_file)
                elif mime_type and mime_type.startswith("video"):
                    await callback_query.message.answer_video(input_file)
                else:
                    await callback_query.message.reply("Error: Unknown file format.")
            else:
                await callback_query.message.reply(f"File is too large. Please download it manually: {file_path}")

            os.remove(file_path)  # Clean up
        else:
            await callback_query.message.reply("Error: File not found.")
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        await callback_query.message.reply("An error occurred while processing your request.")

# Start the bot
async def main():
    logger.info("Starting bot...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
