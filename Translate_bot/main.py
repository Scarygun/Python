from telebot import TeleBot, types
from translator import tarjima

# Telegram bot tokeningizni kiriting
BOT_TOKEN = "API_TOKEN"
bot = TeleBot(BOT_TOKEN)

# Foydalanuvchilarning tanlangan tillarini saqlash uchun lug‘at
foydalanuvchi_tillari = {}

# Tillar ro'yxati
tillar = {
    "O'zbekcha": "uz",
    "Inglizcha": "en",
    "Ruscha": "ru",
    "Fransuzcha": "fr",
    "Koreyscha": "ko",
    "Tojikcha": "tg"
}

# Start komandasi uchun handler
@bot.message_handler(commands=["start"])
def start(xabar: types.Message):
    foydalanuvchi_tillari[xabar.from_user.id] = "uz"  # Standart til - o'zbek tili
    bot.send_message(
        xabar.from_user.id,
        "Assalomu alaykum! Ushbu bot matnlarni tarjima qilishda yordam beradi.\n"
        "Tarjima qilish uchun matn yuboring yoki /language komandasini bosib tilni tanlang."
    )

# Tillarni tanlash komandasi
@bot.message_handler(commands=["language"])
def choose_language(xabar: types.Message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    for til in tillar.keys():
        markup.add(types.KeyboardButton(til))
    bot.send_message(
        xabar.from_user.id,
        "Iltimos, tarjima qilish uchun tilni tanlang:",
        reply_markup=markup
    )

# Foydalanuvchi tanlagan tilda javob qaytarish
@bot.message_handler(func=lambda message: message.text in tillar.keys())
def set_language(xabar: types.Message):
    tanlangan_til = tillar[xabar.text]
    foydalanuvchi_tillari[xabar.from_user.id] = tanlangan_til
    bot.send_message(
        xabar.from_user.id,
        f"Tarjima uchun tanlangan til: {xabar.text}. Endi matn yuborishingiz mumkin.",
        reply_markup=types.ReplyKeyboardRemove()
    )

# Tarjima qilish uchun handler
@bot.message_handler(func=lambda message: True)
def translate_message(xabar: types.Message):
    tanlangan_til = foydalanuvchi_tillari.get(xabar.from_user.id, "uz")  # Standart til o'zbekcha
    javob = tarjima(xabar.text, tanlangan_til)
    bot.send_message(xabar.from_user.id, javob)

# Botni ishga tushirish
print("Bot ishlayapti...")
bot.polling()
