import logging
import asyncio
import sqlite3
import hashlib
import openai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from forex_python.converter import CurrencyRates

# 📌 Logging sozlamalari
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 📌 SQLite bazasini sozlash
conn = sqlite3.connect('users.db')
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    authenticated INTEGER,
    login_attempts INTEGER
)
''')
conn.commit()

# 📌 OpenAI API kalitini sozlash
openai.api_key = "OPENAI.API_KEY"

# 📌 OpenAI API dan foydalanish
def ask_openai(question):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Siz foydali yordamchi botsiz."},
                {"role": "user", "content": question}
            ]
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        logger.error(f"OpenAI API xatosi: {e}")
        return "Kechirasiz, javob berishda xatolik yuz berdi."

# 📌 Telegram bot tokeni va admin ID
TELEGRAM_TOKEN = "TELEGRAM_TOKEN"
ADMIN_ID = ADMEN_ID  # ID ni butun son sifatida saqlash

# 📌 Foydalanuvchi bazasi (xotirada saqlanadi)
users_db = {}
blocked_users = set()
MAX_LOGIN_ATTEMPTS = 3

# 📌 Valyuta juftliklari
CURRENCY_PAIRS = {
    'XAU/USD': '🔸 XAU/USD (Oltin va AQSh dollari)',
    'BTC/USD': '🔸 BTC/USD (Bitcoin va AQSh dollari)',
    'EUR/USD': '🔸 EUR/USD (Evro va AQSh dollari)',
    'USD/JPY': '🔸 USD/JPY (AQSh dollari va Yapon iyenasi)',
    'GBP/USD': '🔸 GBP/USD (Britaniya funt sterlingi va AQSh dollari)'
}

# 📌 Parolni shifrlash
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# 📌 Start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in users_db:
        await update.message.reply_text(
            "👋 Xush kelibsiz! Botdan foydalanish uchun parolni kiriting.\n"
            "Parolni /auth <parol> ko'rinishida yuboring."
        )
    else:
        await show_main_menu(update, context)

# 📌 Auth komandasi
async def auth_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id in blocked_users:
        await update.message.reply_text("❌ Siz bloklangansiz. Administrator bilan bog'laning.")
        return
    
    if context.args:
        password = context.args[0]
    else:
        password = update.message.text.strip()
    
    if password == "test123":  # O'zingizning parolingizni kiriting
        users_db[user_id] = {
            'authenticated': True,
            'login_attempts': 0
        }
        await update.message.reply_text("✅ Tizimga muvaffaqiyatli kirdingiz!")
        await show_main_menu(update, context)
    else:
        if user_id not in users_db:
            users_db[user_id] = {'authenticated': False, 'login_attempts': 1}
        else:
            users_db[user_id]['login_attempts'] += 1
            
        remaining_attempts = MAX_LOGIN_ATTEMPTS - users_db[user_id]['login_attempts']
        
        if remaining_attempts <= 0:
            blocked_users.add(user_id)
            await update.message.reply_text("❌ Siz bloklangansiz. Administrator bilan bog'laning.")
        else:
            await update.message.reply_text(
                f"❌ Noto'g'ri parol. {remaining_attempts} ta urinish qoldi."
            )

# 📌 Asosiy menyuni chiqarish
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(name, callback_data=f"pair_{key}")] for key, name in CURRENCY_PAIRS.items()]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.effective_message.reply_text(
        "🔍 Valyuta juftligini tanlang:",
        reply_markup=reply_markup
    )

# 📌 Tugmalarni qayta ishlash
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    if user_id not in users_db or not users_db[user_id].get('authenticated'):
        await query.answer("Iltimos, avval tizimga kiring!")
        return
    
    await query.answer()
    
    if query.data.startswith("pair_"):
        pair = query.data.replace("pair_", "")
        await start_analysis(query, pair)

# 📌 Analiz jarayonini boshlash
async def start_analysis(query, pair):
    # Progress bar yoki yuklash animatsiyasi
    message = await query.message.edit_text(
        f"⏳ {CURRENCY_PAIRS[pair]} tahlil qilinmoqda...\n"
        "Kutish vaqti: 5 soniya"
    )
    
    # Har bir bosqichni 5 soniyaga tushirish
    for i in range(5, 0, -1):
        await asyncio.sleep(5)  # Har bir bosqich 5 soniya bo'ladi
        await message.edit_text(
            f"⏳ {CURRENCY_PAIRS[pair]} tahlil qilinmoqda...\n"
            f"Kutish vaqti: {i * 5} soniya qoldi"
        )
    
    # Signal generatsiyasi
    signal = generate_mock_signal(pair)
    
    if signal is None:
        await message.edit_text("❌ Signal generatsiyasi xatosi. Iltimos, qayta urinib ko'ring.")
        return
    
    # Natijani chiqarish
    await message.edit_text(
        f"🔔 **Tijorat signali**:\n"
        f"Juftlik: {pair}\n"
        f"Pozitsiya: {signal['position']}\n"
        f"Kirish darajasi: {signal['entry']}\n"
        f"TP (Take Profit): {signal['tp']}\n"
        f"SL (Stop Loss): {signal['sl']}\n"
        f"📌 Izoh: TP - foyda olish darajalari, SL - zarar cheklash darajasi."
    )


# 📌 Sinov uchun taxminiy signal yaratish
def generate_mock_signal(pair):
    try:
        return {
            'position': 'Sell (short)',
            'entry': '2689',
            'tp': '2685, 2680',
            'sl': '2690'
        }
    except Exception as e:
        logger.error(f"Signal generatsiyasi xatosi: {e}")
        return None

# 📌 Admin paneli
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Sizda ruxsat yo'q.")
        return
    
    if not blocked_users:
        await update.message.reply_text("🚀 Bloklangan foydalanuvchilar yo'q.")
        return
    
    blocked_list = "\n".join([str(uid) for uid in blocked_users])
    await update.message.reply_text(f"🚨 Bloklangan foydalanuvchilar:\n{blocked_list}")

# 📌 Bloklangan foydalanuvchini ochish
async def unblock_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Sizda ruxsat yo'q.")
        return
    
    if not context.args:
        await update.message.reply_text("🛠 Foydalanuvchi ID sini kiriting: /unblock <user_id>")
        return
    
    unblock_id = int(context.args[0])
    if unblock_id in blocked_users:
        blocked_users.remove(unblock_id)
        await update.message.reply_text(f"✅ Foydalanuvchi {unblock_id} blokdan chiqarildi!")
    else:
        await update.message.reply_text("⚠️ Bunday foydalanuvchi bloklangan emas.")

# 📌 OpenAI yordamida savolga javob berish
async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in users_db or not users_db[user_id].get('authenticated'):
        await update.message.reply_text("Iltimos, avval tizimga kiring!")
        return
    
    if not context.args:
        await update.message.reply_text("Iltimos, savol yuboring: /ask <savol>")
        return
    
    question = " ".join(context.args)
    response = ask_openai(question)
    await update.message.reply_text(response)

# 📌 Asosiy funksiya
def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("auth", auth_handler))
    application.add_handler(CommandHandler("ask", ask_command))  # Yangi /ask buyrug'i
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CommandHandler("unblock", unblock_user))
    application.add_handler(CallbackQueryHandler(button_handler))

    application.run_polling(allowed_updates=Update.ALL_TYPES)

# 📌 Dastur ishga tushishi
if __name__ == '__main__':
    main()