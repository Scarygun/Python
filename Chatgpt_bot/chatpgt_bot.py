import os
import asyncio
import openai
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.client.bot import DefaultBotProperties  # Import DefaultBotProperties

# API Tokens
TELEGRAM_TOKEN = "YOUR_BOT_TOKEN"
OPENAI_API_KEY = "API_KEY"

# Set OpenAI API key
openai.api_key = OPENAI_API_KEY

# Create bot and dispatcher
bot = Bot(token=TELEGRAM_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))  # DefaultBotProperties orqali parse_mode

dp = Dispatcher()

# Function to get response from ChatGPT
async def get_gpt_response(prompt):
    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-4",  # You can use "gpt-3.5-turbo" for cost efficiency
            messages=[{"role": "user", "content": prompt}]
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        return f"Произошла ошибка: {str(e)}"

# Handler for /start command
@dp.message(Command("start"))
async def start_command(message: Message):
    await message.answer("👋 Salom! Men ChatGPT bilan ishlayotgan botman. Menga biror narsa yozing!")

# Message handler
@dp.message()
async def chat_with_gpt(message: Message):
    response = await get_gpt_response(message.text)
    await message.answer(response)

# Start the bot
async def main():
    print("🤖 Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
