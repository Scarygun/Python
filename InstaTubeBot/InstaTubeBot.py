import logging
import os
import mimetypes
import re
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
BOT_TOKEN = "7646311191:AAFSQrbFcu5puH--m-TJekKSEGRzQs1dAWM"

# Bot va dispatcherni inicializatsiya qilish
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Yuklash uchun katalog yaratish
os.makedirs("downloads", exist_ok=True)

# URL’larni saqlash uchun FSM (Finite State Machine)
class DownloadState(StatesGroup):
    waiting_for_url = State()

# Platformani aniqlash funksiyasi
def aniqlash_link_turi(link):
    if "instagram.com" in link or "instagr.am" in link:
        return "instagram"
    elif "youtube.com" in link or "youtu.be" in link:
        return "youtube"
    return None

# Media sifatini tanlash uchun klaviatura
def media_quality_keyboard(platform: str):
    keyboard = []
    if platform == "youtube":
        qualities = ["720p", "480p", "360p", "240p", "144p"]
        for quality in qualities:
            keyboard.append([InlineKeyboardButton(text=f"{quality} ⚡", callback_data=f"{platform}_{quality}")])
        keyboard.append([InlineKeyboardButton(text="🎵 MP3 ⚡", callback_data=f"{platform}_mp3")])
    elif platform == "instagram":
        keyboard.append([InlineKeyboardButton(text="📹 Video ⚡", callback_data=f"{platform}_video")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard) if keyboard else None

# Yuklab olish funksiyasi
def download_media(url, platform, quality="360p", media_type="video"):
    try:
        ydl_opts = {'outtmpl': 'downloads/%(title)s.%(ext)s', 'noplaylist': True}

        if platform == "youtube":
            quality_map = {
                "720p": "bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/best[ext=mp4]",
                "480p": "bestvideo[ext=mp4][height<=480]+bestaudio[ext=m4a]/best[ext=mp4]",
                "360p": "bestvideo[ext=mp4][height<=360]+bestaudio[ext=m4a]/best[ext=mp4]",
            }
            ydl_opts['format'] = quality_map.get(quality, "best[ext=mp4]")
        elif media_type == "mp3":
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
            
            return file_path if os.path.exists(file_path) else None
    except Exception as e:
        logger.error(f"Yuklab olishda xato: {e}")
        return None

# Katta fayllarni kichik qismlarga ajratish funksiyasi
def split_file(file_path, chunk_size=49 * 1024 * 1024):  # 49MB
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

# Katta fayllarni qismlarga bo'lib yuborish funksiyasi
async def send_large_file(message, file_path):
    file_parts = split_file(file_path)

    for part in file_parts:
        input_file = FSInputFile(part)
        await message.answer_document(input_file)
        os.remove(part)  # Fayl qismlarini o‘chirib tashlash

# Start buyrug‘i
@dp.message(CommandStart())
async def start_command(message: Message, state: FSMContext):
    await state.clear()
    await message.reply("👋 Xush kelibsiz! YouTube yoki Instagram havolasini yuboring.")

# URL’larni qayta ishlash
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

# Sifatni tanlashga javob berish
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
        mime_type, _ = mimetypes.guess_type(file_path)
        
        if mime_type and mime_type.startswith("audio"):
            await callback_query.message.answer_audio(FSInputFile(file_path))
        elif mime_type and mime_type.startswith("video"):
            # Kichik video fayllarni yuborish
            if os.path.getsize(file_path) <= 50 * 1024 * 1024:  # Agar fayl 50MB dan kichik bo'lsa
                await callback_query.message.answer_video(FSInputFile(file_path))
            else:
                # Katta video faylni qismlarga bo'lib yuborish
                await send_large_file(callback_query.message, file_path)
        else:
            await callback_query.message.reply("❌ Xato: Nomalum fayl formati.")
        
        os.remove(file_path)
    else:
        await callback_query.message.reply("❌ Xato: Fayl topilmadi.")

# Botni ishga tushurish
async def main():
    logger.info("Bot ishga tushmoqda...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
