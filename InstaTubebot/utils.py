import os
import yt_dlp
import requests
from bs4 import BeautifulSoup
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import logging

def sanitize_filename(name):
    """ Fayl nomidan noto'g'ri belgilarni olib tashlash """
    return "".join(c if c.isalnum() or c in " ._-()" else "_" for c in name)

async def check_subscriptions(bot, user_id):
    """Foydalanuvchi barcha kerakli kanallarga obuna bo'lganligini tekshirish."""
    from config import REQUIRED_CHANNELS
    not_subscribed = []
    
    for channel in REQUIRED_CHANNELS:
        try:
            channel_username = channel['username']
            
            # Avval kanalning mavjudligini tekshiramiz
            try:
                chat = await bot.get_chat(f"@{channel_username}")
                logging.info(f"Channel found: {chat.title}")
            except Exception as e:
                logging.error(f"Channel not found: @{channel_username}")
                not_subscribed.append(channel)
                continue
            
            try:
                chat_member = await bot.get_chat_member(chat_id=f"@{channel_username}", user_id=user_id)
                logging.info(f"User {user_id} status in @{channel_username}: {chat_member.status}")
                
                if chat_member.status not in ["member", "administrator", "creator"]:
                    logging.info(f"User is not subscribed to @{channel_username}")
                    not_subscribed.append(channel)
                else:
                    logging.info(f"User is subscribed to @{channel_username}")
            except Exception as e:
                logging.error(f"Error checking membership: {str(e)}")
                not_subscribed.append(channel)
                
        except Exception as e:
            logging.error(f"General error: {str(e)}")
            not_subscribed.append(channel)
            
    return not_subscribed

def aniqlash_link_turi(link):
    """Link turini aniqlash."""
    if "instagram.com" in link or "instagr.am" in link:
        return "instagram"
    elif "youtube.com" in link or "youtu.be" in link:
        return "youtube"
    elif "pinterest.com" in link or "pin.it" in link:
        return "pinterest"
    return None

def media_quality_keyboard(platform: str):
    """Media yuklab olish uchun tugmalar yaratish."""
    keyboard = []
    if platform == "youtube":
        qualities = ["720p", "480p", "360p"]
        for quality in qualities:
            keyboard.append([InlineKeyboardButton(text=f"{quality} ⚡", callback_data=f"{platform}_{quality}")])
        keyboard.append([InlineKeyboardButton(text="🎵 MP3 ⚡", callback_data=f"{platform}_mp3")])
    elif platform in ["instagram", "pinterest"]:
        keyboard.append([InlineKeyboardButton(text="📹 Video ⚡", callback_data=f"{platform}_video")])
        if platform == "pinterest":
            keyboard.append([InlineKeyboardButton(text="🖼 Rasm ⚡", callback_data=f"{platform}_photo")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard) if keyboard else None

def download_pinterest_media(url, media_type="video"):
    """Pinterest-dan video yoki rasm yuklab olish."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Xatolikni tekshirish
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        if media_type == "photo":
            # Rasmni topish
            img_tags = soup.find_all('img', {'src': True})
            max_size_img = None
            max_size = 0
            
            for img in img_tags:
                src = img.get('src', '')
                if 'originals' in src:
                    max_size_img = src
                    break
                elif '.jpg' in src or '.png' in src:
                    size = len(src)
                    if size > max_size:
                        max_size = size
                        max_size_img = src
            
            if max_size_img:
                media_url = max_size_img
            else:
                logging.error("❌ Xatolik: Pinterest rasmini topib bo'lmadi!")
                return None
                
        else:  # video
            # Video manzilini topish
            video_url = None
            
            # Meta teglardan qidirish
            meta_tags = soup.find_all('meta', {'property': 'og:video'})
            if meta_tags:
                video_url = meta_tags[0].get('content')
            
            if not video_url:
                # Video tegidan qidirish
                video_tags = soup.find_all('video', {'src': True})
                if video_tags:
                    video_url = video_tags[0].get('src')
            
            if not video_url:
                # source tegidan qidirish
                source_tags = soup.find_all('source', {'src': True})
                if source_tags:
                    video_url = source_tags[0].get('src')
            
            if video_url:
                media_url = video_url
            else:
                logging.error("❌ Xatolik: Pinterest videosini topib bo'lmadi!")
                return None

        # Media faylni yuklab olish
        file_ext = "jpg" if media_type == "photo" else "mp4"
        file_path = f"downloads/pinterest_{media_type}.{file_ext}"
        
        media_response = requests.get(media_url, headers=headers)
        media_response.raise_for_status()
        
        with open(file_path, "wb") as file:
            file.write(media_response.content)
            
        logging.info(f"✅ {media_type.capitalize()} muvaffaqiyatli yuklandi: {file_path}")
        return file_path
        
    except requests.RequestException as e:
        logging.error(f"❌ So'rov xatoligi: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"❌ Kutilmagan xatolik: {str(e)}")
        return None

def download_media(url, platform, media_type="video"):
    """Media yuklab olish funksiyasi."""
    if platform == "pinterest":
        return download_pinterest_media(url, media_type)

    file_ext = "mp3" if media_type == "mp3" else "mp4"
    file_path = f"downloads/{platform}_{media_type}.{file_ext}"
    
    ydl_opts = {
        "outtmpl": file_path.replace(".mp3", ""),
        "format": "bestaudio/best" if media_type == "mp3" else "best",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }] if media_type == "mp3" else []
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    final_path = file_path if os.path.exists(file_path) else file_path + ".mp3"
    
    if os.path.exists(final_path):
        return final_path
    else:
        print(f"❌ Xatolik: Fayl topilmadi: {final_path}")
        return None
