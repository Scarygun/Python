from aiogram import types, Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import CallbackQuery, LabeledPrice, PreCheckoutQuery
from states import OrderState
import os
from aiogram.types import FSInputFile
from aiogram.types import Message
from datetime import datetime
import pytz
from keyboards import (
    phone_number_kb, location_kb, main_menu_kb, place_selection_kb,
    table_selection_kb, food_menu_kb, first_food_kb, second_food_kb,
    salads_kb, drinks_kb, hot_drinks_kb, back_kb, payment_button_kb
)

router = Router()

# --- /start ---
@router.message(F.text == "/start")
async def start_handler(message: types.Message, state: FSMContext):
    timezone = pytz.timezone("Asia/Tashkent")
    current_time = datetime.now(timezone)
    formatted_time = current_time.strftime("%I:%M %p %z on %A, %B %d, %Y")
    time_message = f"Today's date and time is {formatted_time}."

    instructions = (
        "📋 Botdan foydalanish bo'yicha ko'rsatma:\n\n"
        "1️⃣ Botni ishga tushirish uchun /start buyrug'ini yuboring.\n"
        "2️⃣ Telefon raqamingizni yuborish uchun 📞 Telefon raqamni yuborish tugmasini bosing.\n"
        "3️⃣ Gmail manzilingizni kiriting.\n"
        "4️⃣ Lokatsiyangizni yuborish uchun 📍 Lokatsiyani yuborish tugmasini bosing.\n"
        "5️⃣ Buyurtma berish(Dastavka) uchun 📥 Buyurtma berish tugmasini bosing.\n"
        "4️⃣ Restara uziga kelib ovqatlanaman desangiz 🪑 Stol tanlayman? tugmasini bosasiz.\n"
        "6️⃣ Menyudan ovqat yoki ichimlik tanlang va miqdorini kiriting.\n"
        "7️⃣ Tanlangan buyurtmalarni ko'rish uchun 📋 Tanlangan buyurtmalarni ko'rish tugmasini bosing.\n"
        "8️⃣ Buyurtmani yakunlash uchun ✅ Buyurtmani yakunlash tugmasini bosing.\n"
        "9️⃣ Orqaga qaytish uchun har qanday bosqichda 🔙 Orqaga tugmasini bosing.\n\n"
        "Buyurtmangizni tez va oson berish uchun bot sizga yordam beradi! 😊"
    )

    await message.answer(
        f"{time_message}\n\nAssalomu alaykum! Xush kelibsiz restaranizga!\n\n{instructions}\n\nIltimos, telefon raqamingizni yuboring:",
        reply_markup=phone_number_kb()
    )
    await state.update_data(previous_state=None, orders_by_table={})
    await state.set_state(OrderState.waiting_for_phone)

# --- Telefon raqam qabul qilish ---
@router.message(OrderState.waiting_for_phone, F.contact)
async def get_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number, previous_state=None)
    await message.answer("✅ Telefon qabul qilindi.\nEndi Gmail manzilingizni yuboring:", reply_markup=back_kb())
    await state.set_state(OrderState.waiting_for_gmail)

# --- Gmail qabul qilish ---
@router.message(OrderState.waiting_for_gmail)
async def get_gmail(message: types.Message, state: FSMContext):
    email = message.text.lower().strip()
    
    # Gmail formatini tekshirish
    if not email.endswith("@gmail.com"):
        await message.answer("❌ Noto'g'ri format! Iltimos, to'g'ri Gmail manzilini kiriting.\nMasalan: example@gmail.com")
        return
    
    # Gmail uzunligini tekshirish (minimum 10 belgi: a@gmail.com)
    if len(email) < 10:
        await message.answer("❌ Gmail manzili juda qisqa! Iltimos, to'g'ri Gmail manzilini kiriting.\nMasalan: example@gmail.com")
        return
    
    # Gmail formatini to'liq tekshirish
    import re
    gmail_pattern = r'^[a-zA-Z0-9._%+-]+@gmail\.com$'
    if not re.match(gmail_pattern, email):
        await message.answer("❌ Noto'g'ri Gmail formati! Gmail manzili faqat harflar, raqamlar va nuqta belgisidan iborat bo'lishi kerak.\nMasalan: example@gmail.com")
        return
    
    # Gmail to'g'ri bo'lsa, saqlash
    await state.update_data(gmail=email, previous_state=OrderState.waiting_for_phone)
    await message.answer("✅ Gmail manzili qabul qilindi.\nEndi lokatsiyangizni yuboring:", reply_markup=location_kb())
    await state.set_state(OrderState.waiting_for_location)

# --- Lokatsiya qabul qilish ---
@router.message(OrderState.waiting_for_location, F.location)
async def get_location(message: types.Message, state: FSMContext):
    await state.update_data(location={
        "latitude": message.location.latitude,
        "longitude": message.location.longitude
    }, previous_state=OrderState.waiting_for_gmail)
    data = await state.get_data()
    await message.answer(
        f"✅ Ma'lumotlar saqlandi:\n\n"
        f"📞 Telefon: {data['phone']}\n"
        f"📧 Gmail: {data['gmail']}\n"
        f"📍 Lokatsiya: {data['location']['latitude']}, {data['location']['longitude']}",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(OrderState.order_menu)
    await show_order_menu(message, state)

# --- Bosh sahifaga qaytish ---
@router.message(F.text == "🏠 Bosh sahifaga qaytish")
async def back_to_home(message: types.Message, state: FSMContext):
    # Holatni tozalash
    await state.clear()
    # Yangi state o'rnatish
    await state.set_state(OrderState.order_menu)
    await show_order_menu(message, state)

# --- Order menyu ko'rsatuvchi funksiya ---
async def show_order_menu(message: types.Message, state: FSMContext):
    # State ni tekshiramiz va o'rnatamiz
    current_state = await state.get_state()
    if not current_state:
        await state.set_state(OrderState.order_menu)
    await message.answer("🏠 Bosh sahifaga qaytdingiz. Iltimos, amal tanlang:", reply_markup=main_menu_kb())

# --- Stol tanlash ---
@router.message(F.text == "🪑 Stol tanlayman?", OrderState.order_menu)
async def choose_place(message: types.Message, state: FSMContext):
    await state.update_data(previous_state=OrderState.order_menu)
    await message.answer("Joy turini tanlang:", reply_markup=place_selection_kb())
    await state.set_state(OrderState.choosing_place)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@router.message(F.text.in_({"🏛 Banket zali", "🌳 Yozgi hovli", "🏓 Tennis zali", "🏠 Asosiy zal"}), OrderState.choosing_place)
async def zal_handler(message: types.Message, state: FSMContext):
    await state.update_data(previous_state=OrderState.choosing_place)
    zal_nomi = message.text
    rasm_fayllar = {
        "🏛 Banket zali": "banket_zal.jpg",
        "🌳 Yozgi hovli": "yozgi_hovli.jpg", 
        "🏠 Asosiy zal": "asosiy_zal.jpg",
        "🏓 Tennis zali": "tennis_zal.jpg"
    }

    file_name = rasm_fayllar.get(zal_nomi)
    rasm_path = os.path.join(BASE_DIR, "images", file_name)

    if os.path.exists(rasm_path):
        photo = FSInputFile(rasm_path)
        await message.answer_photo(photo=photo, caption=f"{zal_nomi} uchun mavjud stollar:")
    else:
        await message.answer(f"❌ Rasm topilmadi: {rasm_path}")

    await message.answer("Stolni tanlang:", reply_markup=table_selection_kb(zal_nomi))
    await state.set_state(OrderState.choosing_table)

# --- Stol tanlanganda ---
@router.message(F.text.regexp(r"^(🏛|🌳|🏠|🏓) .* – Stol [1-5]$"), OrderState.choosing_table)
async def stol_tanlandi(message: types.Message, state: FSMContext):
    await state.update_data(selected_table=message.text, previous_state=OrderState.choosing_table)
    data = await state.get_data()
    orders_by_table = data.get('orders_by_table', {})
    if message.text not in orders_by_table:
        orders_by_table[message.text] = []
    await state.update_data(orders_by_table=orders_by_table)
    await message.answer(f"✅ Siz {message.text} ni tanladingiz.", reply_markup=ReplyKeyboardRemove())
    await state.set_state(OrderState.buyurtma_menu)
    await show_buyurtma_menu(message, state)

# --- Kabina yoki Kabinka tanlanganda buyurtma menyusiga o'tish ---
@router.message(F.text.in_(["🔲 Kabina (1)", "🔘 Kabinka (2)"]), OrderState.choosing_place)
async def kabina_selected(message: types.Message, state: FSMContext):
    await state.update_data(selected_table=message.text, previous_state=OrderState.choosing_place)
    data = await state.get_data()
    orders_by_table = data.get('orders_by_table', {})
    if message.text not in orders_by_table:
        orders_by_table[message.text] = []
    await state.update_data(orders_by_table=orders_by_table)
    await message.answer(f"✅ Siz {message.text} ni tanladingiz.", reply_markup=ReplyKeyboardRemove())
    await state.set_state(OrderState.buyurtma_menu)
    await show_buyurtma_menu(message, state)

# --- Ovqat menyusi ---
async def show_buyurtma_menu(message: types.Message, state: FSMContext):
    await state.update_data(previous_state=OrderState.order_menu)
    data = await state.get_data()
    if 'selected_table' not in data:
        await state.update_data(selected_table="Tanlanmagan")
        orders_by_table = data.get('orders_by_table', {})
        if "Tanlanmagan" not in orders_by_table:
            orders_by_table["Tanlanmagan"] = []
        await state.update_data(orders_by_table=orders_by_table)
    await message.answer("Menyudan tanlang:", reply_markup=food_menu_kb())
    await state.set_state(OrderState.buyurtma_menu)

# --- Salatlar menyusi ---
@router.message(F.text == "🥗 Salatlar", OrderState.buyurtma_menu)
async def salatlar_menu(message: types.Message, state: FSMContext):
    await state.update_data(previous_state=OrderState.buyurtma_menu)
    await message.answer("Salatlardan birini tanlang:", reply_markup=salads_kb())
    await state.set_state(OrderState.choosing_salat)

# --- Salat tanlash ---
@router.message(F.text.regexp(r"^🥗 .* salat$"), OrderState.choosing_salat)
async def salat_tanlandi(message: types.Message, state: FSMContext):
    await state.update_data(current_item=message.text)
    await message.answer(f"📏 {message.text} dan nechta buyurtma qilmoqchisiz? Iltimos, raqam yuboring (masalan, 2):")
    await state.set_state(OrderState.waiting_for_quantity)

# --- 1 - Ovqat menyusi ---
@router.message(F.text == "🍗 1 - Ovqat", OrderState.buyurtma_menu)
async def first_food_menu(message: types.Message, state: FSMContext):
    await state.update_data(previous_state=OrderState.buyurtma_menu)
    await message.answer("1-kategoriya ovqatlaridan birini tanlang:", reply_markup=first_food_kb())
    await state.set_state(OrderState.choosing_first_food)

# --- 1-ovqat tanlash ---
@router.message(F.text.regexp(r"^🍲 .*"), OrderState.choosing_first_food)
async def first_food_selected(message: types.Message, state: FSMContext):
    await state.update_data(current_item=message.text)
    await message.answer(f"📏 {message.text} dan nechta buyurtma qilmoqchisiz? Iltimos, raqam yuboring (masalan, 2):")
    await state.set_state(OrderState.waiting_for_quantity)

# --- 2 - Ovqat menyusi ---
@router.message(F.text == "🥘 2 - Ovqat", OrderState.buyurtma_menu)
async def second_food_menu(message: types.Message, state: FSMContext):
    await state.update_data(previous_state=OrderState.buyurtma_menu)
    await message.answer("2-kategoriya ovqatlaridan birini tanlang:", reply_markup=second_food_kb())
    await state.set_state(OrderState.choosing_second_food)

# --- 2-ovqat tanlash ---
@router.message(F.text.regexp(r"^🥘 .*"), OrderState.choosing_second_food)
async def second_food_selected(message: types.Message, state: FSMContext):
    await state.update_data(current_item=message.text)
    await message.answer(f"📏 {message.text} dan nechta buyurtma qilmoqchisiz? Iltimos, raqam yuboring (masalan, 2):")
    await state.set_state(OrderState.waiting_for_quantity)

# --- Issiq ichimliklar menyusi ---
@router.message(F.text == "🍵 Issiq ichimliklar", OrderState.buyurtma_menu)
async def hot_drinks_menu(message: types.Message, state: FSMContext):
    await state.update_data(previous_state=OrderState.buyurtma_menu)
    await message.answer("Issiq ichimliklardan birini tanlang:", reply_markup=hot_drinks_kb())
    await state.set_state(OrderState.choosing_hot_drinks)

# --- Issiq ichimlik tanlash ---
@router.message(F.text.in_(["🍵 Qora choy", "🍵 Ko'k choy", "🍵 Limon choy", "☕ Cappuccino", "☕ Americano"]), OrderState.choosing_hot_drinks)
async def hot_drink_selected(message: types.Message, state: FSMContext):
    await state.update_data(current_item=message.text)
    await message.answer(f"📏 {message.text} dan nechta buyurtma qilmoqchisiz? Iltimos, raqam yuboring (masalan, 2):")
    await state.set_state(OrderState.waiting_for_quantity)

# --- Ichimliklar menyusi ---
@router.message(F.text == "🥤 Ichimliklar", OrderState.buyurtma_menu)
async def drinks_menu_handler(message: types.Message, state: FSMContext):
    await state.update_data(previous_state=OrderState.buyurtma_menu)
    await message.answer("Ichimliklar menyusi:", reply_markup=drinks_kb())
    await state.set_state(OrderState.choosing_drinks)

# --- Ichimlik tanlash ---
@router.message(F.text.in_(["Pepsi", "Fanta", "Coca-Cola", "Sprite", "Limonad", "Mirinda", "Red Bull", "Flesh", "Adrenaline Rush"]), OrderState.choosing_drinks)
async def drink_selected(message: types.Message, state: FSMContext):
    await state.update_data(current_item=message.text)
    await message.answer(f"📏 {message.text} dan nechta buyurtma qilmoqchisiz? Iltimos, raqam yuboring (masalan, 2):")
    await state.set_state(OrderState.waiting_for_quantity)

# --- Miqdor kiritish ---
@router.message(OrderState.waiting_for_quantity, F.text)
async def process_quantity(message: types.Message, state: FSMContext):
    try:
        quantity = int(message.text)
        if quantity <= 0:
            await message.answer("❌ Miqdor 0 dan katta bo'lishi kerak. Iltimos, to'g'ri raqam yuboring (masalan, 2):")
            return
    except ValueError:
        await message.answer("❌ Iltimos, faqat raqam yuboring (masalan, 2):")
        return

    data = await state.get_data()
    current_item = data.get('current_item')
    await state.update_data(quantity=quantity)

    if current_item in ["Pepsi", "Fanta", "Coca-Cola"]:
        await message.answer(f"📏 {quantity} ta {current_item} uchun litrni kiriting (masalan, 2 litr yoki 1.5 litr):")
        await state.set_state(OrderState.waiting_for_litre)
    else:
        selected_table = data.get('selected_table', "Tanlanmagan")
        orders_by_table = data.get('orders_by_table', {})
        if selected_table not in orders_by_table:
            orders_by_table[selected_table] = []
        orders_by_table[selected_table].append({"name": current_item, "quantity": quantity})
        await state.update_data(orders_by_table=orders_by_table)
        await message.answer(f"✅ {current_item} ({quantity} ta) tanlandi.\nYana biror narsa buyurtma qilish uchun menyudan tanlang yoki 'Tanlangan buyurtmalarni ko'rish' yoki 'Buyurtmani yakunlash' ni bosing.")
        await state.set_state(OrderState.buyurtma_menu)
        await show_buyurtma_menu(message, state)

# --- Litr kiritish ---
@router.message(OrderState.waiting_for_litre, F.text)
async def process_litre(message: types.Message, state: FSMContext):
    if not message.text.lower().endswith("litr"):
        await message.answer("❌ Iltimos, to'g'ri formatda kiriting (masalan, 2 litr yoki 1.5 litr):")
        return

    quantity_text = message.text.lower().replace("litr", "").strip()
    try:
        litre = float(quantity_text)
        if litre <= 0:
            await message.answer("❌ Litr 0 dan katta bo'lishi kerak. Iltimos, to'g'ri formatda yuboring (masalan, 2 litr):")
            return
    except ValueError:
        await message.answer("❌ Iltimos, to'g'ri formatda kiriting (masalan, 2 litr yoki 1.5 litr):")
        return

    data = await state.get_data()
    current_item = data.get('current_item')
    quantity = data.get('quantity')
    selected_table = data.get('selected_table', "Tanlanmagan")
    orders_by_table = data.get('orders_by_table', {})

    if selected_table not in orders_by_table:
        orders_by_table[selected_table] = []
    orders_by_table[selected_table].append({"name": current_item, "quantity": quantity, "litre": litre, "unit": "litr"})
    await state.update_data(orders_by_table=orders_by_table)

    await message.answer(f"✅ {quantity} ta {current_item} ({litre} litr) tanlandi.\nYana biror narsa buyurtma qilish uchun menyudan tanlang yoki 'Tanlangan buyurtmalarni ko'rish' yoki 'Buyurtmani yakunlash' ni bosing.")
    await state.set_state(OrderState.buyurtma_menu)
    await show_buyurtma_menu(message, state)

# --- Callbackni qayta ishlash ---
@router.callback_query(F.data == "show_drinks")
async def show_drinks_menu(callback: CallbackQuery, state: FSMContext):
    await state.update_data(previous_state=OrderState.buyurtma_menu)
    await callback.message.answer("Ichimliklar menyusi:", reply_markup=drinks_kb())
    await state.set_state(OrderState.choosing_drinks)
    await callback.answer()

# --- Tanlangan buyurtmalarni ko'rish ---
@router.message(F.text == "📋 Tanlangan buyurtmalarni ko'rish", OrderState.buyurtma_menu)
async def show_selected_items(message: types.Message, state: FSMContext):
    data = await state.get_data()
    orders_by_table = data.get('orders_by_table', {})
    
    if not orders_by_table:
        await message.answer("❌ Siz hali hech narsa tanlamadingiz. Iltimos, avval buyurtma bering.")
        await show_buyurtma_menu(message, state)
        return

    order_summary = "📋 Sizning tanlangan buyurtmalaringiz:\n\n"
    for table, items in orders_by_table.items():
        if items:
            order_summary += f"📍 Stol: {table}\n"
            for item in items:
                if 'litre' in item:
                    order_summary += f"- {item['name']} ({item['quantity']} ta, {item['litre']} {item['unit']})\n"
                else:
                    order_summary += f"- {item['name']} ({item['quantity']} ta)\n"
            order_summary += "\n"

    await message.answer(order_summary)
    await show_buyurtma_menu(message, state)

# --- Buyurtmani yakunlash ---
@router.message(F.text == "✅ Zakaz berish", OrderState.buyurtma_menu)
async def finish_order(message: types.Message, state: FSMContext):
    data = await state.get_data()
    orders_by_table = data.get('orders_by_table', {})
    if not orders_by_table:
        await message.answer("❌ Siz hali hech narsa tanlamadingiz. Iltimos, avval buyurtma bering.")
        await show_buyurtma_menu(message, state)
        return

    has_items = False
    total_items = 0
    order_summary = "📋 Sizning buyurtmangiz:\n\n"
    
    for table, items in orders_by_table.items():
        if items:
            has_items = True
            order_summary += f"📍 {table}\n"
            for item in items:
                total_items += item['quantity']
                if 'litre' in item:
                    order_summary += f"- {item['name']} ({item['quantity']} ta, {item['litre']} {item['unit']})\n"
                else:
                    order_summary += f"- {item['name']} ({item['quantity']} ta)\n"
            order_summary += "\n"

    if not has_items:
        await message.answer("❌ Siz hali hech narsa tanlamadingiz. Iltimos, avval buyurtma bering.")
        await show_buyurtma_menu(message, state)
        return

    # Har bir buyurtma uchun 5000 so'm
    total_amount = total_items * 5000

    # To'lov uchun invoice yaratish
    await message.bot.send_invoice(
        chat_id=message.chat.id,
        title="Restoran buyurtmasi",
        description=order_summary,
        payload=f"order_{message.from_user.id}_{datetime.now().timestamp()}",
        provider_token="CLIKC_TOKEN",
        currency="UZS",
        prices=[
            LabeledPrice(
                label=f"Jami {total_items} ta buyurtma",
                amount=total_amount * 100  # Summani tiyinda ko'rsatish kerak
            )
        ],
        max_tip_amount=100000000,
        suggested_tip_amounts=[500000, 1000000, 2000000, 5000000],
        start_parameter="restoran_bot",
        provider_data=None,
        photo_url=None,
        photo_size=None,
        photo_width=None,
        photo_height=None,
        need_name=True,
        need_phone_number=True,
        need_email=False,
        need_shipping_address=True,
        send_phone_number_to_provider=False,
        send_email_to_provider=False,
        is_flexible=False,
        disable_notification=False,
        protect_content=False,
        reply_to_message_id=None,
        allow_sending_without_reply=True,
        reply_markup=None,
        request_timeout=None
    )

# Pre-checkout so'rovini qayta ishlash
@router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery, bot: Bot):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

# Muvaffaqiyatli to'lov
@router.message(F.successful_payment)
async def successful_payment(message: Message, state: FSMContext):
    await message.answer(
        "✅ To'lov muvaffaqiyatli amalga oshirildi!\n"
        "Buyurtmangiz qabul qilindi. Tez orada yetkazib beriladi!"
    )
    await state.clear()
    await state.set_state(OrderState.order_menu)
    await message.answer(
        "🏠 Bosh sahifaga qaytdingiz. Iltimos, amal tanlang:", 
        reply_markup=main_menu_kb()
    )

# Update go_back function to handle new state
@router.message(F.text == "🔙 Orqaga")
async def go_back(message: types.Message, state: FSMContext):
    data = await state.get_data()
    current_state = await state.get_state()

    if current_state == OrderState.waiting_for_phone:
        await message.answer("Bu boshlang'ich bosqich, orqaga qaytib bo'lmaydi.", reply_markup=ReplyKeyboardRemove())
        return

    elif current_state == OrderState.waiting_for_gmail:
        await state.set_state(OrderState.waiting_for_phone)
        await message.answer("Ortga qaytdik.\nIltimos, telefon raqamingizni yuboring:", reply_markup=phone_number_kb())

    elif current_state == OrderState.waiting_for_location:
        await state.set_state(OrderState.waiting_for_gmail)
        await state.update_data(previous_state=OrderState.waiting_for_phone)
        await message.answer("Ortga qaytdik.\nIltimos, Gmail manzilingizni yuboring:", reply_markup=back_kb())

    elif current_state == OrderState.order_menu:
        await state.set_state(OrderState.waiting_for_location)
        await state.update_data(previous_state=OrderState.waiting_for_gmail)
        await message.answer("Ortga qaytdik.\nEndi lokatsiyangizni yuboring:", reply_markup=location_kb())

    elif current_state == OrderState.choosing_place:
        await state.set_state(OrderState.order_menu)
        await show_order_menu(message, state)

    elif current_state == OrderState.choosing_table:
        await state.set_state(OrderState.choosing_place)
        await message.answer("Ortga qaytdik.\nJoy turini tanlang:", reply_markup=place_selection_kb())

    elif current_state == OrderState.buyurtma_menu:
        await state.set_state(OrderState.order_menu)
        await show_order_menu(message, state)

    elif current_state == OrderState.choosing_payment:
        await state.set_state(OrderState.showing_order_summary)
        await finish_order(message, state)

    elif current_state == OrderState.waiting_for_quantity:
        if data.get('current_item') in ["Pepsi", "Fanta", "Coca-Cola"]:
            await state.set_state(OrderState.choosing_drinks)
            await message.answer("Ortga qaytdik.\nIchimliklar menyusi:", reply_markup=drinks_kb())
        else:
            await state.set_state(OrderState.buyurtma_menu)
            await show_buyurtma_menu(message, state)

    elif current_state == OrderState.waiting_for_litre:
        await state.set_state(OrderState.waiting_for_quantity)
        data = await state.get_data()
        current_item = data.get('current_item')
        await message.answer(f"Ortga qaytdik.\n📏 {current_item} dan nechta buyurtma qilmoqchisiz? Iltimos, raqam yuboring (masalan, 2):")

    elif current_state in [OrderState.choosing_salat, OrderState.choosing_fastfood, OrderState.choosing_first_food,
                          OrderState.choosing_second_food, OrderState.choosing_drinks, OrderState.choosing_hot_drinks]:
        await state.set_state(OrderState.buyurtma_menu)
        await show_buyurtma_menu(message, state)

    elif current_state == OrderState.showing_order_summary:
        await state.set_state(OrderState.buyurtma_menu)
        await show_buyurtma_menu(message, state)

    else:
        await state.set_state(OrderState.order_menu)
        await show_order_menu(message, state)
