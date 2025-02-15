import logging
import os
import asyncio
import yt_dlp
import requests
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, FSInputFile
from aiogram.filters.command import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

BOT_TOKEN = "Bot_token"
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
    elif "pinterest.com" in link or "pin.it" in link:
        return "pinterest"
    return None

def media_quality_keyboard(platform: str):
    keyboard = []
    if platform == "youtube":
        qualities = ["720p", "480p", "360p"]
        for quality in qualities:
            keyboard.append([InlineKeyboardButton(text=f"{quality} ⚡", callback_data=f"{platform}_{quality}")])
        keyboard.append([InlineKeyboardButton(text="🎵 MP3 ⚡", callback_data=f"{platform}_mp3")])
    elif platform == "instagram" or platform == "pinterest":
        keyboard.append([InlineKeyboardButton(text="📹 Video ⚡", callback_data=f"{platform}_video")])
        if platform == "pinterest":
            keyboard.append([InlineKeyboardButton(text="🖼 Rasm ⚡", callback_data=f"{platform}_photo")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard) if keyboard else None

def get_pinterest_media(url, media_type="video"):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        if media_type == "video":
            media_tag = soup.find("meta", property="og:video")
        else:
            media_tag = soup.find("meta", property="og:image")
        
        if media_tag and media_tag.get("content"):
            return media_tag["content"]
    return None

def download_media(url, platform, quality="360p", media_type="video"):
    try:
        if platform == "pinterest":
            media_url = get_pinterest_media(url, media_type)
            if media_url:
                file_ext = "mp4" if media_type == "video" else "jpg"
                file_path = f"downloads/pinterest_media.{file_ext}"
                media_response = requests.get(media_url)
                if media_response.status_code == 200:
                    with open(file_path, "wb") as file:
                        file.write(media_response.content)
                    return file_path
            return None
        
        ydl_opts = {'outtmpl': 'downloads/%(title)s.%(ext)s', 'noplaylist': True}
        if platform == "youtube":
            quality_map = {
                "720p": "bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/best[ext=mp4]",
                "480p": "bestvideo[ext=mp4][height<=480]+bestaudio[ext=m4a]/best[ext=mp4]",
                "360p": "bestvideo[ext=mp4][height<=360]+bestaudio[ext=m4a]/best[ext=mp4]",
            }
            ydl_opts['format'] = quality_map.get(quality, "best[ext=mp4]")
        elif media_type == "mp3":
            ydl_opts["format"] = "bestaudio[ext=m4a]"
            ydl_opts["postprocessors"] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info_dict)
            if media_type == "mp3":
                file_path = file_path.rsplit('.', 1)[0] + '.mp3'
            return file_path if os.path.exists(file_path) else None
    except Exception as e:
        logger.error(f"Xatolik: {e}")
        return None

@dp.message(CommandStart())
async def start_command(message: Message, state: FSMContext):
    await state.clear()
    await message.reply("👋 Xush kelibsiz! YouTube, Instagram yoki Pinterest havolasini yuboring.")

@dp.message(F.text.startswith("http"))
async def handle_url(message: Message, state: FSMContext):
    url = message.text.strip()
    platform = aniqlash_link_turi(url)
    if platform:
        await state.update_data(url=url, platform=platform)
        keyboard = media_quality_keyboard(platform)
        await message.reply("📥 Yuklab olish variantini tanlang:", reply_markup=keyboard)
    else:
        await message.reply("❌ Xato: Faqat YouTube, Instagram yoki Pinterest havolasini yuboring.")

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
    file_path = download_media(url, platform, media_type=media_type)
    if file_path and os.path.exists(file_path):
        await callback_query.message.answer_document(FSInputFile(file_path))
        os.remove(file_path)
    else:
        await callback_query.message.reply("❌ Xato: Fayl topilmadi.")

async def main():
    logger.info("Bot ishga tushmoqda...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())