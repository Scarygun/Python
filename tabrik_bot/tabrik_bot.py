import logging
import openai
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
)

# 🔑 Konfiguratsiya
TOKEN = "TELEGRAM_TOKEN"
OPENAI_API_KEY = "OPENAI_API_KEY"

client = openai.OpenAI(api_key=OPENAI_API_KEY)

bot = Bot(token=TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

# 🎧 Emoji tanlash klaviaturasi
emoji_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🎉"), KeyboardButton(text="🎊"), KeyboardButton(text="🥳")],
        [KeyboardButton(text="💖"), KeyboardButton(text="🎁"), KeyboardButton(text="🌟")],
        [KeyboardButton(text="✅"), KeyboardButton(text="🚀"), KeyboardButton(text="🔥")],
        [KeyboardButton(text="⬅️ Ortga")]
    ],
    resize_keyboard=True
)

# 🔄 Foydalanuvchi ma'lumotlarini saqlash
user_data = {}

@dp.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    text = message.text

    if user_id not in user_data:
        user_data[user_id] = {}

    if text == "/start":
        user_data[user_id] = {}
        await message.answer("Tabriklash uchun odamning ismini kiriting:")
    elif "name" not in user_data[user_id]:
        user_data[user_id]["name"] = text
        await message.answer("Jinsni tanlang:", reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Erkak")], [KeyboardButton(text="Ayol")]],
            resize_keyboard=True
        ))
    elif text in ["Erkak", "Ayol"]:
        user_data[user_id]["gender"] = text
        await message.answer("Bayramni tanlang:", reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Tug‘ilgan kun"), KeyboardButton(text="Yangi yil")],
                [KeyboardButton(text="8-mart"), KeyboardButton(text="14-fevral")],
                [KeyboardButton(text="23-fevral"), KeyboardButton(text="Boshqa")]
            ],
            resize_keyboard=True
        ))
    elif text in ["Tug‘ilgan kun", "Yangi yil", "8-mart", "14-fevral", "23-fevral", "Boshqa"]:
        if text == "23-fevral":
            user_data[user_id]["holiday"] = "Vatan himoyachilari kuni"
        else:
            user_data[user_id]["holiday"] = text
        await message.answer("Tabrik matni uzunligini tanlang:", reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Qisqa")],
                [KeyboardButton(text="O‘rtacha")],
                [KeyboardButton(text="Uzun")]
            ],
            resize_keyboard=True
        ))
    elif text in ["Qisqa", "O‘rtacha", "Uzun"]:
        user_data[user_id]["length"] = text
        await message.answer("Tabrik uslubini tanlang:", reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Rasmiy")],
                [KeyboardButton(text="Oddiy")],
                [KeyboardButton(text="Ijodiy")]
            ],
            resize_keyboard=True
        ))
    elif text in ["Rasmiy", "Oddiy", "Ijodiy"]:
        user_data[user_id]["style"] = text
        await generate_greeting(message)
    elif user_id in user_data and "waiting_for_emoji" in user_data[user_id]:
        if text == "⬅️ Ortga":
            user_data[user_id].pop("waiting_for_emoji")
            await message.answer("Boshqa variantni tanlang:", reply_markup=types.ReplyKeyboardRemove())
        else:
            user_data[user_id]["emoji"] = text
            await update_greeting_with_emoji(message)

async def generate_greeting(message: types.Message):
    user_info = user_data[message.from_user.id]
    prompt = (f"{user_info['gender'].lower()} uchun {user_info['length'].lower()} "
              f"{user_info['style'].lower()} tabrik yozing. Ism: {user_info['name']}, bayram: {user_info['holiday']}.")

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )

    greeting_text = response.choices[0].message.content.strip()
    user_data[message.from_user.id]["greeting"] = greeting_text
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Yana variant", callback_data="regenerate")],
        [InlineKeyboardButton(text="Emoji qo‘shish", callback_data="add_emoji")],
        [InlineKeyboardButton(text="Tabrik so‘zini o‘zgartirish", callback_data="customize")]
    ])
    await message.answer(greeting_text, reply_markup=kb)

@dp.callback_query(lambda call: call.data == "add_emoji")
async def add_emoji(call: types.CallbackQuery):
    user_data[call.from_user.id]["waiting_for_emoji"] = True
    await call.message.answer("Tabrik matniga qanday emoji qo‘shmoqchisiz?", reply_markup=emoji_kb)
    await call.answer()

async def update_greeting_with_emoji(message: types.Message):
    user_id = message.from_user.id
    emoji = user_data[user_id].get("emoji", "")
    greeting_text = user_data[user_id].get("greeting", "")
    
    if greeting_text:
        updated_greeting = f"{greeting_text} {emoji}"
        await message.answer(updated_greeting, reply_markup=types.ReplyKeyboardRemove())

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
