import logging
import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, FSInputFile
from aiogram.filters.command import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN, REQUIRED_CHANNELS
from utils import check_subscriptions, aniqlash_link_turi, media_quality_keyboard, download_media

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=MemoryStorage())
os.makedirs("downloads", exist_ok=True)

class DownloadState(StatesGroup):
    waiting_for_url = State()

@dp.message(CommandStart())
async def start_command(message: Message, state: FSMContext):
    """Start komandasi va obuna tekshiruvi."""
    user_id = message.from_user.id
    not_subscribed = await check_subscriptions(bot, user_id)

    if not_subscribed:
        text = "🚨 Botdan to‘liq foydalanish uchun quyidagi kanallarga obuna bo‘lishingiz kerak:\n\n"
        for channel in not_subscribed:
            text += f"👉 <a href='https://t.me/{channel['username']}'>{channel['title']}</a>  🔴\n"
        text += "\n✅ Obuna bo‘lgandan so‘ng \"Tasdiqlash\" tugmasini bosing."
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="confirm_subscription")]
        ])
        await message.answer(text, disable_web_page_preview=True, reply_markup=keyboard)
    else:
        await state.clear()
        await message.reply("👋 Xush kelibsiz! YouTube, Instagram yoki Pinterest havolasini yuboring.")

@dp.message(F.text.startswith("http"))
async def handle_url(message: Message, state: FSMContext):
    """URLni qabul qilish va platformani aniqlash."""
    url = message.text.strip()
    platform = aniqlash_link_turi(url)
    if platform:
        await state.update_data(url=url, platform=platform)
        keyboard = media_quality_keyboard(platform)
        await message.reply("📥 Yuklab olish variantini tanlang:", reply_markup=keyboard)
    else:
        await message.reply("❌ Xato: Faqat YouTube, Instagram yoki Pinterest havolasini yuboring.")

@dp.callback_query(F.data == "confirm_subscription")
async def confirm_subscription(callback_query: CallbackQuery):
    """Obunani tasdiqlash."""
    user_id = callback_query.from_user.id
    not_subscribed = await check_subscriptions(bot, user_id)
    if not not_subscribed:
        await callback_query.message.edit_text("✅ Tabriklayman! Siz barcha funksiyalardan foydalanishingiz mumkin.")
    else:
        await callback_query.answer("❌ Siz hali ham kanalga obuna bo‘lmadingiz. Iltimos, avval obuna bo‘ling!", show_alert=True)

@dp.callback_query(F.data.startswith("youtube_") | F.data.startswith("instagram_") | F.data.startswith("pinterest_"))
async def handle_quality_selection(callback_query: CallbackQuery, state: FSMContext):
    """Yuklab olish variantini tanlash."""
    data = await state.get_data()
    url = data.get("url")
    platform = data.get("platform")
    media_type = callback_query.data.split("_")[1]

    if not url:
        await callback_query.message.reply("❌ Xato: URL topilmadi. Iltimos, qaytadan havola yuboring.")
        return

    await callback_query.message.edit_text(f"📥 Yuklab olinmoqda: {media_type}...")

    file_path = download_media(url, platform, media_type=media_type)
    if file_path and os.path.exists(file_path):
        await callback_query.message.answer_document(FSInputFile(file_path))
        os.remove(file_path)
    else:
        await callback_query.message.reply("❌ Xato: Fayl topilmadi.")

async def main():
    """Asosiy funksiya."""
    logger.info("Bot ishga tushmoqda...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
