import logging
import wikipedia
from http.client import responses

import wikipedia
from aiogram import Bot, Dispatcher, executor, types

API_TOKEN = '7876134054:AAHUshrfNZxfqFYLtWs6x6imzEFE-ZIEEUs'
wikipedia.set_lang('uz')

# Muhim xabarlarni o'tkazib yubormaslik uchun loglarni sozlab, yoqib qo'yamiz
logging.basicConfig(level=logging.INFO)

# Bot obyekti
bot = Bot(token= API_TOKEN)
# Bot uchun dispetcher
dp = Dispatcher(bot)

# Botga jo'natilgan /start buyrug'ini qabul qilib olish uchun handler
@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    # foydalanuvchiga javoban salom beradi
    await message.reply("Uzbekbotga Xush kelibsiz!")



# Foydalanuvchilardan kelgan matnni(textni) qabul qilib olish uchun handler
@dp.message_handler(content_types=['text'])
async def uzbekbot(message: types.Message):
        try:
            respond = wikipedia.summary(message.text)
            await message.reply(respond)
        except:
            await message.reply("Bu mavzuga oid maqola topilmadi")


if __name__ == '__main__':
    # Botimizni ishga tushiramiz
    executor.start_polling(dp,skip_updates=True)