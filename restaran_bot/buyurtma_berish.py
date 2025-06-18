from aiogram import Router, F, types
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, LabeledPrice
from aiogram.fsm.context import FSMContext
from states import OrderState
from keyboards import food_menu_kb, main_menu_kb, payment_button_kb
from prices import PRICES
from datetime import datetime

router = Router()

@router.message(F.text == "📥 Buyurtma berish", OrderState.order_menu)
async def buyurtma_handler(message: Message, state: FSMContext):
    # State ni tekshiramiz
    current_state = await state.get_state()
    if current_state != OrderState.order_menu:
        await state.set_state(OrderState.order_menu)
    
    await state.update_data(previous_state=OrderState.order_menu)
    # Stol tanlanmagan bo'lsa, "Tanlanmagan" sifatida saqlaymiz
    data = await state.get_data()
    if 'selected_table' not in data:
        await state.update_data(selected_table="Dastavka")
    await message.answer("Menyudan tanlang:", reply_markup=food_menu_kb())
    await state.set_state(OrderState.buyurtma_menu)

# FastFood menyusi uchun handler
@router.message(F.text == "🍔 FastFood", OrderState.buyurtma_menu)
async def fastfood_menu(message: types.Message, state: FSMContext):
    await state.update_data(previous_state=OrderState.buyurtma_menu)
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🍔 Burger - " + str(PRICES['🍔 Burger']) + " so'm"), 
                KeyboardButton(text="🌭 Hot-Dog - " + str(PRICES['🌭 Hot-Dog']) + " so'm")
            ],
            [
                KeyboardButton(text="🍟 Fri - " + str(PRICES['🍟 Fri']) + " so'm"), 
                KeyboardButton(text="🍕 Pizza - " + str(PRICES['🍕 Pizza']) + " so'm")
            ],
            [
                KeyboardButton(text="🥪 Sendvich - " + str(PRICES['🥪 Sendvich']) + " so'm"), 
                KeyboardButton(text="🍗 Nuggets - " + str(PRICES['🍗 Nuggets']) + " so'm")
            ],
            [KeyboardButton(text="🔙 Orqaga")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer("FastFood menyusidan birini tanlang:", reply_markup=kb)
    await state.set_state(OrderState.choosing_fastfood)

# FastFood taomini tanlash
@router.message(F.text.regexp(r"^(🍔|🌭|🍟|🍕|🥪|🍗) .* - \d+,?\d* so'm$"), OrderState.choosing_fastfood)
async def fastfood_selected(message: types.Message, state: FSMContext):
    # Narxni olib tashlash uchun
    item_name = message.text.split(" - ")[0]
    item_price = PRICES.get(item_name, 0)
    await state.update_data(current_item=item_name, current_price=item_price)
    await message.answer(f"📏 {item_name} dan nechta buyurtma qilmoqchisiz? Iltimos, raqam yuboring (masalan, 2):")
    await state.set_state(OrderState.waiting_for_quantity)

# Tanlangan buyurtmalarni ko'rish
@router.message(F.text == "📋 Tanlangan buyurtmalarni ko'rish", OrderState.buyurtma_menu)
async def show_selected_items(message: types.Message, state: FSMContext):
    data = await state.get_data()
    orders_by_table = data.get('orders_by_table', {})
    
    if not orders_by_table:
        await message.answer("❌ Siz hali hech narsa tanlamadingiz. Iltimos, avval buyurtma bering.")
        await buyurtma_handler(message, state)
        return

    order_summary = "📋 Sizning tanlangan buyurtmalaringiz:\n\n"
    total_amount = 0
    
    for table, items in orders_by_table.items():
        if items:  # Faqat buyurtmalar mavjud bo'lsa ko'rsatamiz
            order_summary += f"📍 Stol: {table}\n"
            for item in items:
                item_price = item.get('price', PRICES.get(item['name'], 0))
                item_total = item_price * item['quantity']
                if 'litre' in item:
                    item_total = item_price * item['quantity'] * item['litre']
                    order_summary += f"- {item['name']} ({item['quantity']} ta, {item['litre']} {item['unit']}) - {item_total:,} so'm\n"
                else:
                    order_summary += f"- {item['name']} ({item['quantity']} ta) - {item_total:,} so'm\n"
                total_amount += item_total
            order_summary += "\n"

    order_summary += f"💰 Jami summa: {total_amount:,} so'm"
    await message.answer(order_summary)
    await buyurtma_handler(message, state)

# Buyurtmani yakunlash handler
@router.message(F.text == "✅ Zakaz berish", OrderState.buyurtma_menu)
async def finalize_order(message: Message, state: FSMContext):
    data = await state.get_data()
    orders_by_table = data.get('orders_by_table', {})
    
    if not orders_by_table:
        await message.answer("❌ Siz hali hech narsa tanlamadingiz. Iltimos, avval buyurtma bering.")
        await buyurtma_handler(message, state)
        return

    has_items = False
    total_amount = 0
    order_summary = "📋 Sizning buyurtmangiz:\n\n"
    
    for table, items in orders_by_table.items():
        if items:
            has_items = True
            order_summary += f"📍 {table}\n"
            for item in items:
                item_price = item.get('price', PRICES.get(item['name'], 0))
                item_total = item_price * item['quantity']
                if 'litre' in item:
                    item_total = item_price * item['quantity'] * item['litre']
                    order_summary += f"- {item['name']} ({item['quantity']} ta, {item['litre']} {item['unit']}) - {item_total:,} so'm\n"
                else:
                    order_summary += f"- {item['name']} ({item['quantity']} ta) - {item_total:,} so'm\n"
                total_amount += item_total
            order_summary += "\n"
    
    if not has_items:
        await message.answer("❌ Siz hali hech narsa tanlamadingiz. Iltimos, avval buyurtma bering.")
        await buyurtma_handler(message, state)
        return

    order_summary += f"💰 Jami summa: {total_amount:,} so'm"

    # To'lov uchun invoice yaratish
    await message.bot.send_invoice(
        chat_id=message.chat.id,
        title="Restoran buyurtmasi",
        description=order_summary,
        payload=f"order_{message.from_user.id}_{datetime.now().timestamp()}",
        provider_token="398062629:TEST:999999999_F91D8F69C042267444B74CC0B3C747757EB0E065",
        currency="UZS",
        prices=[
            LabeledPrice(
                label=f"Jami buyurtma summasi",
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

# Miqdor kiritish
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
    current_price = data.get('current_price', PRICES.get(current_item, 0))
    await state.update_data(quantity=quantity)

    if current_item in ["Pepsi", "Fanta", "Coca-Cola"]:
        await message.answer(f"📏 {quantity} ta {current_item} uchun litrni kiriting (masalan, 2 litr yoki 1.5 litr):")
        await state.set_state(OrderState.waiting_for_litre)
    else:
        selected_table = data.get('selected_table', "Tanlanmagan")
        orders_by_table = data.get('orders_by_table', {})
        if selected_table not in orders_by_table:
            orders_by_table[selected_table] = []
        
        item_total = current_price * quantity
        orders_by_table[selected_table].append({
            "name": current_item,
            "quantity": quantity,
            "price": current_price
        })
        
        await state.update_data(orders_by_table=orders_by_table)
        await message.answer(
            f"✅ {current_item} ({quantity} ta) - {item_total:,} so'm qo'shildi.\n"
            "Yana biror narsa buyurtma qilish uchun menyudan tanlang yoki "
            "'Tanlangan buyurtmalarni ko'rish' yoki 'Buyurtmani yakunlash' ni bosing."
        )
        await state.set_state(OrderState.buyurtma_menu)
        await show_selected_items(message, state)

# Litr kiritish
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
    current_price = data.get('current_price', PRICES.get(current_item, 0))
    quantity = data.get('quantity')
    selected_table = data.get('selected_table', "Tanlanmagan")
    orders_by_table = data.get('orders_by_table', {})

    if selected_table not in orders_by_table:
        orders_by_table[selected_table] = []

    item_total = current_price * quantity * litre
    orders_by_table[selected_table].append({
        "name": current_item,
        "quantity": quantity,
        "litre": litre,
        "unit": "litr",
        "price": current_price
    })
    
    await state.update_data(orders_by_table=orders_by_table)
    await message.answer(
        f"✅ {quantity} ta {current_item} ({litre} litr) - {item_total:,} so'm qo'shildi.\n"
        "Yana biror narsa buyurtma qilish uchun menyudan tanlang yoki "
        "'Tanlangan buyurtmalarni ko'rish' yoki 'Buyurtmani yakunlash' ni bosing."
    )
    await state.set_state(OrderState.buyurtma_menu)
    await show_selected_items(message, state)

# Salatlar menyusi
@router.message(F.text == "🥗 Salatlar", OrderState.buyurtma_menu)
async def salatlar_menu(message: types.Message, state: FSMContext):
    await state.update_data(previous_state=OrderState.buyurtma_menu)
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🥗 Olivye salat - " + str(PRICES['🥗 Olivye salat']) + " so'm"),
                KeyboardButton(text="🥗 Sezar salat - " + str(PRICES['🥗 Sezar salat']) + " so'm")
            ],
            [
                KeyboardButton(text="🥗 Mujskoy kapriz salat - " + str(PRICES['🥗 Mujskoy kapriz salat']) + " so'm"),
                KeyboardButton(text="🥗 Grecheskiy salat - " + str(PRICES['🥗 Grecheskiy salat']) + " so'm")
            ],
            [KeyboardButton(text="🔙 Orqaga")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer("Salatlardan birini tanlang:", reply_markup=kb)
    await state.set_state(OrderState.choosing_salat)

# Salat tanlash
@router.message(F.text.regexp(r"^🥗 .* salat - \d+,?\d* so'm$"), OrderState.choosing_salat)
async def salat_tanlandi(message: types.Message, state: FSMContext):
    item_name = message.text.split(" - ")[0]
    item_price = PRICES.get(item_name, 0)
    await state.update_data(current_item=item_name, current_price=item_price)
    await message.answer(f"📏 {item_name} dan nechta buyurtma qilmoqchisiz? Iltimos, raqam yuboring (masalan, 2):")
    await state.set_state(OrderState.waiting_for_quantity)

# 1-Ovqat menyusi
@router.message(F.text == "🍗 1 - Ovqat", OrderState.buyurtma_menu)
async def first_food_menu(message: types.Message, state: FSMContext):
    await state.update_data(previous_state=OrderState.buyurtma_menu)
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🍲 Mastava - " + str(PRICES['🍲 Mastava']) + " so'm"),
                KeyboardButton(text="🍲 Shorva - " + str(PRICES['🍲 Shorva']) + " so'm")
            ],
            [
                KeyboardButton(text="🍲 Lagmon - " + str(PRICES['🍲 Lagmon']) + " so'm"),
                KeyboardButton(text="🍲 Moshxorda - " + str(PRICES['🍲 Moshxorda']) + " so'm")
            ],
            [KeyboardButton(text="🔙 Orqaga")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer("1-kategoriya ovqatlaridan birini tanlang:", reply_markup=kb)
    await state.set_state(OrderState.choosing_first_food)

# 1-ovqat tanlash
@router.message(F.text.regexp(r"^🍲 .* - \d+,?\d* so'm$"), OrderState.choosing_first_food)
async def first_food_selected(message: types.Message, state: FSMContext):
    item_name = message.text.split(" - ")[0]
    item_price = PRICES.get(item_name, 0)
    await state.update_data(current_item=item_name, current_price=item_price)
    await message.answer(f"📏 {item_name} dan nechta buyurtma qilmoqchisiz? Iltimos, raqam yuboring (masalan, 2):")
    await state.set_state(OrderState.waiting_for_quantity)

# 2-Ovqat menyusi
@router.message(F.text == "🥘 2 - Ovqat", OrderState.buyurtma_menu)
async def second_food_menu(message: types.Message, state: FSMContext):
    await state.update_data(previous_state=OrderState.buyurtma_menu)
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🥘 Osh - " + str(PRICES['🥘 Osh']) + " so'm"),
                KeyboardButton(text="🥘 Qovurma lagmon - " + str(PRICES['🥘 Qovurma lagmon']) + " so'm")
            ],
            [
                KeyboardButton(text="🥘 Manti - " + str(PRICES['🥘 Manti']) + " so'm"),
                KeyboardButton(text="🥘 Chuchvara - " + str(PRICES['🥘 Chuchvara']) + " so'm")
            ],
            [KeyboardButton(text="🔙 Orqaga")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer("2-kategoriya ovqatlaridan birini tanlang:", reply_markup=kb)
    await state.set_state(OrderState.choosing_second_food)

# 2-ovqat tanlash
@router.message(F.text.regexp(r"^🥘 .* - \d+,?\d* so'm$"), OrderState.choosing_second_food)
async def second_food_selected(message: types.Message, state: FSMContext):
    item_name = message.text.split(" - ")[0]
    item_price = PRICES.get(item_name, 0)
    await state.update_data(current_item=item_name, current_price=item_price)
    await message.answer(f"📏 {item_name} dan nechta buyurtma qilmoqchisiz? Iltimos, raqam yuboring (masalan, 2):")
    await state.set_state(OrderState.waiting_for_quantity)

# Ichimliklar menyusi
@router.message(F.text == "🥤 Ichimliklar", OrderState.buyurtma_menu)
async def drinks_menu(message: types.Message, state: FSMContext):
    await state.update_data(previous_state=OrderState.buyurtma_menu)
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Pepsi - " + str(PRICES['Pepsi']) + " so'm/l"),
                KeyboardButton(text="Fanta - " + str(PRICES['Fanta']) + " so'm/l")
            ],
            [
                KeyboardButton(text="Coca-Cola - " + str(PRICES['Coca-Cola']) + " so'm/l"),
                KeyboardButton(text="Sprite - " + str(PRICES['Sprite']) + " so'm/l")
            ],
            [
                KeyboardButton(text="Limonad - " + str(PRICES['Limonad']) + " so'm"),
                KeyboardButton(text="Mirinda - " + str(PRICES['Mirinda']) + " so'm")
            ],
            [
                KeyboardButton(text="Red Bull - " + str(PRICES['Red Bull']) + " so'm"),
                KeyboardButton(text="Flesh - " + str(PRICES['Flesh']) + " so'm")
            ],
            [KeyboardButton(text="Adrenaline Rush - " + str(PRICES['Adrenaline Rush']) + " so'm")],
            [KeyboardButton(text="🔙 Orqaga")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer("Ichimliklardan birini tanlang:", reply_markup=kb)
    await state.set_state(OrderState.choosing_drinks)

# Ichimlik tanlash
@router.message(F.text.regexp(r"^.* - \d+,?\d* so'm(/l)?$"), OrderState.choosing_drinks)
async def drink_selected(message: types.Message, state: FSMContext):
    item_name = message.text.split(" - ")[0]
    item_price = PRICES.get(item_name, 0)
    await state.update_data(current_item=item_name, current_price=item_price)
    if item_name in ["Pepsi", "Fanta", "Coca-Cola"]:
        await message.answer(f"📏 {item_name} dan nechta buyurtma qilmoqchisiz? Iltimos, raqam yuboring (masalan, 2):")
    else:
        await message.answer(f"📏 {item_name} dan nechta buyurtma qilmoqchisiz? Iltimos, raqam yuboring (masalan, 2):")
    await state.set_state(OrderState.waiting_for_quantity)

# Issiq ichimliklar menyusi
@router.message(F.text == "🍵 Issiq ichimliklar", OrderState.buyurtma_menu)
async def hot_drinks_menu(message: types.Message, state: FSMContext):
    await state.update_data(previous_state=OrderState.buyurtma_menu)
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text='🍵 Qora choy - ' + str(PRICES['🍵 Qora choy']) + ' so\'m'),
                KeyboardButton(text='🍵 Ko\'k choy - ' + str(PRICES['🍵 Ko\'k choy']) + ' so\'m')
            ],
            [
                KeyboardButton(text='🍵 Limon choy - ' + str(PRICES['🍵 Limon choy']) + ' so\'m'),
                KeyboardButton(text='☕ Cappuccino - ' + str(PRICES['☕ Cappuccino']) + ' so\'m')
            ],
            [KeyboardButton(text='☕ Americano - ' + str(PRICES['☕ Americano']) + ' so\'m')],
            [KeyboardButton(text="🔙 Orqaga")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer("Issiq ichimliklardan birini tanlang:", reply_markup=kb)
    await state.set_state(OrderState.choosing_hot_drinks)

# Issiq ichimlik tanlash
@router.message(F.text.regexp(r"^(🍵|☕) .* - \d+,?\d* so'm$"), OrderState.choosing_hot_drinks)
async def hot_drink_selected(message: types.Message, state: FSMContext):
    item_name = message.text.split(" - ")[0]
    item_price = PRICES.get(item_name, 0)
    await state.update_data(current_item=item_name, current_price=item_price)
    await message.answer(f"📏 {item_name} dan nechta buyurtma qilmoqchisiz? Iltimos, raqam yuboring (masalan, 2):")
    await state.set_state(OrderState.waiting_for_quantity)

# Orqaga tugmasi uchun handler
@router.message(F.text == "🔙 Orqaga")
async def go_back(message: types.Message, state: FSMContext):
    data = await state.get_data()
    previous_state = data.get('previous_state', OrderState.order_menu)
    
    if previous_state == OrderState.order_menu:
        await message.answer("Asosiy menyu:", reply_markup=main_menu_kb())
        await state.set_state(OrderState.order_menu)
    elif previous_state == OrderState.buyurtma_menu:
        await buyurtma_handler(message, state)
    else:
        await message.answer("Menyudan tanlang:", reply_markup=food_menu_kb())
        await state.set_state(OrderState.buyurtma_menu)