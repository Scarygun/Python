import logging
import os
import asyncio
import yt_dlp
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, FSInputFile
from aiogram.filters.command import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

# Logging sozlamalari
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Bot tokeni
BOT_TOKEN = "YOUR_BOT_TOKEN"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

os.makedirs("downloads", exist_ok=True)

class DownloadState(StatesGroup):
    waiting_for_url = State()

def aniqlash_link_turi(link):
    if "instagram.com" in link or "instagr.am" in link:
        return "instagram"
    elif "youtube.com" in link or "youtu.be" in link:
        return "youtube"
    return None

def media_quality_keyboard(platform: str):
    keyboard = []
    if platform == "youtube":
        qualities = ["720p", "480p", "360p"]
        for quality in qualities:
            keyboard.append([InlineKeyboardButton(text=f"{quality} ⚡", callback_data=f"{platform}_{quality}")])
        keyboard.append([InlineKeyboardButton(text="🎵 MP3 ⚡", callback_data=f"{platform}_mp3")])
    elif platform == "instagram":
        keyboard.append([InlineKeyboardButton(text="📹 Video ⚡", callback_data=f"{platform}_video")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard) if keyboard else None

def download_media(url, platform, quality="360p", media_type="video"):
    try:
        ydl_opts = {'outtmpl': 'downloads/%(title)s.%(ext)s', 'noplaylist': True}
        if platform == "youtube":
            quality_map = {
                "720p": "bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/best[ext=mp4]",
                "480p": "bestvideo[ext=mp4][height<=480]+bestaudio[ext=m4a]/best[ext=mp4]",
                "360p": "bestvideo[ext=mp4][height<=360]+bestaudio[ext=m4a]/best[ext=mp4]",
            }
            if media_type == "mp3":
                ydl_opts["format"] = "bestaudio[ext=m4a]"
                ydl_opts["postprocessors"] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            else:
                ydl_opts['format'] = quality_map.get(quality, "best[ext=mp4]")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info_dict)

            if media_type == "mp3":
                file_path = file_path.rsplit('.', 1)[0] + '.mp3'

            if os.path.exists(file_path):
                logger.info(f"Fayl yuklandi: {file_path}")
                return file_path
            else:
                logger.error(f"Fayl topilmadi: {file_path}")
                return None
    except Exception as e:
        logger.error(f"Xatolik: {e}")
        return None

def split_file(file_path, chunk_size=49 * 1024 * 1024):
    file_size = os.path.getsize(file_path)
    file_parts = []
    with open(file_path, "rb") as f:
        part_num = 1
        while chunk := f.read(chunk_size):
            part_file = f"{file_path}.part{part_num}"
            with open(part_file, "wb") as part:
                part.write(chunk)
            file_parts.append(part_file)
            part_num += 1
    return file_parts

async def send_large_file(message, file_path):
    file_parts = split_file(file_path)
    for part in file_parts:
        input_file = FSInputFile(part)
        await message.answer_document(input_file)
        os.remove(part)

@dp.message(CommandStart())
async def start_command(message: Message, state: FSMContext):
    await state.clear()
    await message.reply("👋 Xush kelibsiz! YouTube yoki Instagram havolasini yuboring.")

@dp.message(F.text.startswith("http"))
async def handle_url(message: Message, state: FSMContext):
    url = message.text.strip()
    platform = aniqlash_link_turi(url)
    if platform:
        await state.update_data(url=url, platform=platform)
        keyboard = media_quality_keyboard(platform)
        await message.reply("📥 Yuklab olish variantini tanlang:", reply_markup=keyboard)
    else:
        await message.reply("❌ Xato: Faqat YouTube yoki Instagram havolasini yuboring.")

@dp.callback_query()
async def handle_quality_selection(callback_query: CallbackQuery, state: FSMContext):
    data = callback_query.data.split("_")
    platform, media_type = data[0], data[1]
    user_data = await state.get_data()
    url = user_data.get("url")
    if not url:
        await callback_query.message.reply("❌ Xato: URL topilmadi.")
        return
    await callback_query.message.edit_text(f"📥 Yuklab olinmoqda: {media_type}...")
    file_path = download_media(url, platform, quality=media_type if media_type != "mp3" else "360p", media_type=media_type)
    if file_path and os.path.exists(file_path):
        if os.path.getsize(file_path) > 50 * 1024 * 1024:
            await send_large_file(callback_query.message, file_path)
        else:
            await callback_query.message.answer_document(FSInputFile(file_path))
        os.remove(file_path)
    else:
        await callback_query.message.reply("❌ Xato: Fayl topilmadi.")

async def main():
    logger.info("Bot ishga tushmoqda...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
