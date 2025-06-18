from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
import asyncio
import logging
from handlers import router as handlers_router
from buyurtma_berish import router as buyurtma_router
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

async def main():
    # Bot obyektini yaratish va to'lov provayderini sozlash
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())
    
    # Routerlarni qo'shamiz
    dp.include_router(handlers_router)
    dp.include_router(buyurtma_router)
    
    # Botni ishga tushiramiz
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Bot stopped!')
