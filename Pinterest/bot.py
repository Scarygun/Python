import os
import re
import json
import tempfile
import requests
import yt_dlp
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')

# Callback data constants
VIDEO_CALLBACK = "download_video"
IMAGE_CALLBACK = "download_image"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Salom! Men Pinterest-dan rasm va videolarni yuklab olishga yordam beraman.\n"
        "Pinterest havolasini yuboring va men sizga media faylni yuborib beraman."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Pinterest havolasini yuboring va men sizga rasm yoki videoni yuklab beraman.\n"
        "Masalan: https://pin.it/... yoki https://pinterest.com/pin/..."
    )

async def download_pinterest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not is_pinterest_url(url):
        await update.message.reply_text("Iltimos, to'g'ri Pinterest havolasini yuboring!")
        return

    # Save URL in context for later use
    context.user_data['pinterest_url'] = url

    # Create inline keyboard with two buttons
    keyboard = [
        [
            InlineKeyboardButton("Video yuklab olish", callback_data=VIDEO_CALLBACK),
            InlineKeyboardButton("Rasm yuklab olish", callback_data=IMAGE_CALLBACK),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Qanday turdagi media faylni yuklab olmoqchisiz?",
        reply_markup=reply_markup
    )

async def download_and_send_video(message, video_url):
    print(f"Downloading video from: {video_url}")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = os.path.join(temp_dir, 'video.mp4')
        
        # First, let's get available formats
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        
        try:
            print("Checking available formats...")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    info = ydl.extract_info(video_url, download=False)
                    formats = info.get('formats', [])
                    if formats:
                        print(f"Available formats: {[f.get('format_id', 'unknown') for f in formats]}")
                        # Get the best format
                        best_format = formats[-1]['format_id']
                    else:
                        best_format = 'best'
                except Exception as e:
                    print(f"Format check failed: {str(e)}")
                    best_format = 'best'

            print(f"Using format: {best_format}")
            
            # Now download with the best format
            ydl_opts = {
                'format': best_format,
                'outtmpl': output_path,
                'quiet': False,
                'no_warnings': False,
                'extract_flat': False,
                'merge_output_format': 'mp4',
                'hls_prefer_ffmpeg': True,
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                }],
            }
            
            print("Starting video download with yt-dlp...")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    print("Attempting primary download method...")
                    info = ydl.extract_info(video_url, download=True)
                    print(f"Download info: {info.get('title', 'No title')} - Format: {info.get('format', 'Unknown')}")
                except Exception as e1:
                    print(f"Primary download failed: {str(e1)}")
                    try:
                        print("Attempting alternative download method...")
                        # Try with simpler options
                        ydl_opts.update({
                            'format': 'best',
                            'postprocessors': [],
                        })
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl2:
                            info = ydl2.extract_info(video_url, download=True)
                            print(f"Alternative download info: {info.get('title', 'No title')} - Format: {info.get('format', 'Unknown')}")
                    except Exception as e2:
                        print(f"Alternative download failed: {str(e2)}")
                        raise e2
            
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                print(f"Video downloaded to: {output_path} (Size: {file_size} bytes)")
                
                if file_size == 0:
                    print("Downloaded file is empty")
                    await message.reply_text("Video yuklab olishda xatolik: Fayl bo'sh")
                    return False
                
                # Try to send as video first
                try:
                    print("Trying to send as video...")
                    with open(output_path, 'rb') as video_file:
                        await message.reply_video(
                            video_file,
                            caption="Pinterest video",
                            supports_streaming=True
                        )
                        return True
                except Exception as e:
                    print(f"Error sending as video: {str(e)}")
                    # If sending as video fails, try sending as document
                    try:
                        print("Trying to send as document...")
                        with open(output_path, 'rb') as video_file:
                            await message.reply_document(
                                video_file,
                                filename="pinterest_video.mp4",
                                caption="Pinterest video"
                            )
                            return True
                    except Exception as e2:
                        print(f"Error sending as document: {str(e2)}")
                        await message.reply_text(f"Video yuborishda xatolik: {str(e2)}")
                        raise e2
            else:
                print(f"Output file not found: {output_path}")
                await message.reply_text("Video yuklab olishda xatolik: Fayl topilmadi")
                return False
                
        except Exception as e:
            error_msg = str(e)
            print(f"Error downloading video: {error_msg}")
            if "Unsupported URL" in error_msg:
                await message.reply_text("Kechirasiz, bu formatdagi videoni yuklab ololmayman")
            else:
                await message.reply_text(f"Video yuklab olishda xatolik: {error_msg}")
            return False

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    url = context.user_data.get('pinterest_url')
    if not url:
        await query.message.reply_text("Xatolik yuz berdi. Iltimos, havolani qayta yuboring.")
        return

    await query.message.edit_text("Yuklanmoqda... Iltimos kuting.")
    
    try:
        media_url = get_pinterest_media_url(url, query.data == VIDEO_CALLBACK)
        if not media_url:
            await query.message.edit_text("Kechirasiz, bu havoladan media faylni yuklab ololmadim.")
            return

        print(f"Found media URL: {media_url}")
        # Delete the "Loading..." message
        await query.message.delete()

        # Check if this is a video URL
        is_video_url = any(x in media_url.lower() for x in ['video', '.mp4', '.mov', '.m3u8', 'vid.', '/v/'])
        
        if query.data == VIDEO_CALLBACK:
            if is_video_url:
                success = await download_and_send_video(query.message, media_url)
                if not success:
                    await query.message.reply_text(f"Video yuklab olishda xatolik yuz berdi. Video havolasi: {media_url}")
            else:
                await query.message.reply_text("Kechirasiz, bu havola video emas, rasm ekan.")
        else:  # IMAGE_CALLBACK
            if not is_video_url and any(media_url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                await query.message.reply_photo(media_url)
            else:
                await query.message.reply_text("Kechirasiz, bu havola rasm emas, video ekan.")
            
    except Exception as e:
        print(f"Callback error: {str(e)}")
        await query.message.edit_text(f"Xatolik yuz berdi: {str(e)}")

def is_pinterest_url(url: str) -> bool:
    pinterest_patterns = [
        r'https?://(?:www\.)?pinterest\.com/pin/.*',
        r'https?://pin\.it/.*'
    ]
    return any(re.match(pattern, url) for pattern in pinterest_patterns)

def clean_pinterest_url(url: str) -> str:
    # Remove sent parameters and other unnecessary parts
    if '/sent/' in url:
        url = url.split('/sent/')[0]
    # Remove any additional parameters
    if '?' in url:
        url = url.split('?')[0]
    return url

def expand_pinterest_url(short_url: str) -> str:
    try:
        response = requests.head(short_url, allow_redirects=True)
        expanded_url = response.url
        # Clean the expanded URL
        return clean_pinterest_url(expanded_url)
    except Exception as e:
        print(f"Error expanding URL: {str(e)}")
        return short_url

def get_pinterest_media_url(pin_url: str, prefer_video: bool = False) -> str:
    try:
        # Expand short URL if needed
        if 'pin.it' in pin_url:
            print(f"Expanding short URL: {pin_url}")
            pin_url = expand_pinterest_url(pin_url)
            print(f"Expanded URL: {pin_url}")

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'Cookie': '_auth=1'
        }

        print(f"Downloading URL: {pin_url}")
        response = requests.get(pin_url, headers=headers, allow_redirects=True)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try to find video URL directly in the HTML
            if prefer_video:
                # Look for video in JSON-LD
                json_ld = soup.find('script', {'type': 'application/ld+json'})
                if json_ld and json_ld.string:
                    try:
                        ld_data = json.loads(json_ld.string)
                        if isinstance(ld_data, list):
                            for item in ld_data:
                                if item.get('@type') == 'VideoObject' and item.get('contentUrl'):
                                    print(f"Found video in JSON-LD: {item['contentUrl']}")
                                    return item['contentUrl']
                    except Exception as e:
                        print(f"Error parsing JSON-LD: {str(e)}")

                # Look for video tags
                video_tags = soup.find_all('video')
                for video in video_tags:
                    src = video.get('src')
                    if src and (src.endswith('.mp4') or 'pinimg.com' in src):
                        print(f"Found video tag with src: {src}")
                        return src
            
            # Pinterest data in JSON format
            data_scripts = soup.find_all('script', {'type': 'application/json'})
            print(f"Found {len(data_scripts)} JSON scripts")
            
            for script in data_scripts:
                if not script.string:
                    continue
                    
                try:
                    data = json.loads(script.string)
                    
                    # Check for video in resource response
                    if 'resourceResponses' in data:
                        print("Found resourceResponses")
                        for response in data['resourceResponses']:
                            if 'response' in response and 'data' in response['response']:
                                response_data = response['response']['data']
                                if 'videos' in response_data:
                                    videos = response_data['videos']
                                    if isinstance(videos, dict) and 'video_list' in videos:
                                        video_list = videos['video_list']
                                        if video_list:
                                            print("Found video in resourceResponses")
                                            best_video = next((v for v in video_list.values()), None)
                                            if best_video and 'url' in best_video:
                                                return best_video['url']
                    
                    # Check in props
                    if 'props' in data and 'initialReduxState' in data['props']:
                        print("Found initialReduxState")
                        pins = data['props']['initialReduxState'].get('pins', {})
                        if pins:
                            pin_id = list(pins.keys())[0]
                            pin_data = pins[pin_id]
                            print(f"Found pin data for ID: {pin_id}")
                            
                            if prefer_video:
                                # Check for video
                                if 'videos' in pin_data:
                                    print("Found videos in pin_data")
                                    videos = pin_data['videos']
                                    if isinstance(videos, dict) and 'video_list' in videos:
                                        video_list = videos['video_list']
                                        if video_list:
                                            print("Found video list")
                                            if 'V_720P' in video_list:
                                                print("Found 720P video")
                                                return video_list['V_720P']['url']
                                            elif video_list:
                                                first_format = list(video_list.keys())[0]
                                                print(f"Using {first_format} video")
                                                return video_list[first_format]['url']
                                
                                # Check story pin data
                                if 'story_pin_data' in pin_data:
                                    print("Checking story_pin_data")
                                    story = pin_data['story_pin_data']
                                    if story and 'pages' in story:
                                        for page in story['pages']:
                                            if 'blocks' in page:
                                                for block in page['blocks']:
                                                    if block.get('type') == 'video':
                                                        video = block.get('video', {})
                                                        if 'video_list' in video:
                                                            video_list = video['video_list']
                                                            if video_list:
                                                                return list(video_list.values())[0]['url']
                            
                            # Get image if no video found or not preferred
                            if not prefer_video and 'images' in pin_data:
                                print("Found images in pin_data")
                                images = pin_data['images']
                                if 'orig' in images:
                                    return images['orig']['url']
                                elif images:
                                    return list(images.values())[0]['url']
                
                except Exception as e:
                    print(f"Error parsing JSON: {str(e)}")
                    continue
            
            # Fallback to meta tags
            if prefer_video:
                for meta_property in ['og:video:url', 'og:video', 'twitter:player:stream']:
                    meta = soup.find('meta', {'property': meta_property}) or soup.find('meta', {'name': meta_property})
                    if meta and meta.get('content'):
                        print(f"Found video in meta tag: {meta_property}")
                        return meta['content']
            else:
                for meta_property in ['og:image', 'twitter:image']:
                    meta = soup.find('meta', {'property': meta_property}) or soup.find('meta', {'name': meta_property})
                    if meta and meta.get('content'):
                        print(f"Found image in meta tag: {meta_property}")
                        return meta['content']
            
            print("No media found in the page")
            return None
            
        else:
            print(f"Failed to fetch page. Status code: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_pinterest))
    application.add_handler(CallbackQueryHandler(button_callback))

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main() 