# Media Yuklab Olish Bot - Texnik Hujjat 📱

## Loyiha haqida
**Nomi:** Media Yuklab Olish Bot (Telegram)  

## Bot Token olish va sozlash 🔑

1. [@BotFather](https://t.me/BotFather) ga boring
2. `/newbot` buyrug'ini yuboring
3. Botingiz uchun nom bering (masalan: Media Yuklovchi)
4. Botingiz uchun username bering (masalan: media_yuklovchi_bot)
5. BotFather sizga token beradi (Masalan: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)
6. Bu tokenni `config.py` fayliga qo'ying:
```python
BOT_TOKEN = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"  # O'z tokeningizni yozing
```

## Majburiy obuna kanallarini sozlash 📢
1. Kanalingizni username'ini va nomini `config.py` fayliga qo'shing:
```python
REQUIRED_CHANNELS = [
    {
        "username": "kanal_username",  # @ belgisisiz
        "title": "Kanal nomi"
    }
]
```
2. Botni kanalingizga admin qiling:
   - Kanalga kiring
   - Kanal sozlamalariga kiring
   - "Administratorlar" bo'limiga o'ting
   - "Administrator qo'shish" tugmasini bosing
   - Botingizni tanlang
   - Quyidagi huquqlarni bering:
     - Xabarlarni o'qish
     - Foydalanuvchilarni bloklash

## Maqsad 🎯
Telegram foydalanuvchilariga YouTube, Instagram va Pinterest platformalaridan media (video yoki rasm) yuklab olish imkoniyatini beruvchi bot yaratish.

## Asosiy funksiyalar 🛠

### 1. Foydalanuvchi bilan ishlash
- `/start` - botni ishga tushirish
- Majburiy obuna tizimi
- Havola yuborish va yuklab olish

### 2. Qo'llab-quvvatlanadigan platformalar
- YouTube 🎥
- Instagram 📸
- Pinterest 📌

### 3. Yuklab olish imkoniyatlari

#### YouTube
- Video formatlar:
  - 720p HD ⚡
  - 480p ⚡
  - 360p ⚡
- Audio format:
  - MP3 🎵

#### Instagram
- Video formatlar:
  - Reels
  - Post videolari
  - Stories

#### Pinterest
- Video 📹
- Rasm 🖼

## Texnik ma'lumotlar ⚙️

### Ishlatilgan texnologiyalar
- Python 3
- Telegram Bot API
- `aiogram` - bot frameworki
- `yt-dlp` - YouTube uchun
- `requests` - so'rovlar uchun
- `beautifulsoup4` - HTML parser

### Loyiha tuzilishi
```
dowland_bot/
├── bot.py            # Asosiy bot kodi
├── config.py         # Sozlamalar va token
├── utils.py          # Yordamchi funksiyalar
├── requirements.txt  # Kerakli kutubxonalar
└── downloads/        # Yuklab olingan fayllar
```

### O'rnatish va ishga tushirish

1. Kerakli kutubxonalarni o'rnatish:
```bash
pip install -r requirements.txt
```

2. `config.py` faylida bot tokenini sozlash:
```python
BOT_TOKEN = "YOUR_BOT_TOKEN"
REQUIRED_CHANNELS = [
    {"username": "channel_username", "title": "Channel Name"}
]
```

3. Botni ishga tushirish:
```bash
python bot.py
```

## Xavfsizlik 🔒
- Faqat ochiq profillardan yuklab olish
- Majburiy obuna tizimi
- Fayllarni vaqtincha saqlash

## Cheklovlar ⚠️
- YouTube video hajmi: maksimal 2GB
- Instagram: faqat ochiq profillar
- Pinterest: ochiq postlar


## Yangilanishlar tarixi 📅
- v1.0 (11.03.2024) - Botning birinchi versiyasi
  - YouTube qo'llab-quvvatlash
  - Instagram qo'llab-quvvatlash
  - Pinterest qo'llab-quvvatlash