# Pinterest Media Downloader Bot

Pinterest-dan rasm va videolarni yuklab oluvchi Telegram bot.

## Imkoniyatlar

- Pinterest havolalaridan rasmlarni yuklab olish
- Pinterest havolalaridan videolarni yuklab olish
- Qisqa (pin.it) havolalarni qo'llab-quvvatlash
- Video va rasmlarni yuqori sifatda yuklash
- HLS (m3u8) formatidagi videolarni qo'llab-quvvatlash

## O'rnatish

1. Kerakli kutubxonalarni o'rnatish:
```bash
pip install -r requirements.txt
```

2. FFmpeg o'rnatish:
- Linux (Ubuntu/Debian):
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```
- Linux (Arch):
```bash
sudo pacman -S ffmpeg
```

3. `.env` faylini yaratish:
```
BOT_TOKEN=your_telegram_bot_token
```

## Ishga tushirish

```bash
python bot.py
```

## Foydalanish

1. Botni Telegramda toping
2. `/start` buyrug'ini yuboring
3. Pinterest havolasini yuboring (https://pinterest.com/pin/... yoki https://pin.it/...)
4. "Video yuklab olish" yoki "Rasm yuklab olish" tugmasini bosing
5. Bot sizga media faylni yuboradi

## Qo'llab-quvvatlanadigan havolalar

- Pinterest pin havolalari (https://pinterest.com/pin/...)
- Qisqa havolalar (https://pin.it/...)
- Story pin havolalari
- Video pin havolalari (HLS/m3u8 formatlarini ham qo'llab-quvvatlaydi)

## Xatoliklarni bartaraf etish

Agar bot video yuklay olmasa:
1. FFmpeg o'rnatilganligini tekshiring
2. Havola to'g'riligini tekshiring
3. Pinterest havolasi ochiq ekanligini tekshiring

## Texnik talablar

- Python 3.7+
- FFmpeg
- Internet aloqasi
- Telegram Bot Token 