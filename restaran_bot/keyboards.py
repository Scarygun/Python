from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton

def phone_number_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📞 Telefon raqamni yuborish", request_contact=True)],
        ],
        resize_keyboard=True
    )

def location_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Lokatsiyani yuborish", request_location=True)],
        ],
        resize_keyboard=True
    )

def main_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📥 Buyurtma berish")],
            [KeyboardButton(text="🪑 Stol tanlayman?")],
        ],
        resize_keyboard=True
    )

def place_selection_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏛 Banket zali"), KeyboardButton(text="🔲 Kabina (1)")],
            [KeyboardButton(text="🌳 Yozgi hovli"), KeyboardButton(text="🔘 Kabinka (2)")],
            [KeyboardButton(text="🏓 Tennis zali"), KeyboardButton(text="🏠 Asosiy zal")],
            [KeyboardButton(text="🔙 Orqaga")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def table_selection_kb(zal_nomi):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=f"{zal_nomi} – Stol 1"), KeyboardButton(text=f"{zal_nomi} – Stol 2")],
            [KeyboardButton(text=f"{zal_nomi} – Stol 3"), KeyboardButton(text=f"{zal_nomi} – Stol 4")],
            [KeyboardButton(text=f"{zal_nomi} – Stol 5")],
            [KeyboardButton(text="🔙 Orqaga")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def food_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🍗 1 - Ovqat"), KeyboardButton(text="🥘 2 - Ovqat")],
            [KeyboardButton(text="🍔 FastFood"), KeyboardButton(text="🥤 Ichimliklar")],
            [KeyboardButton(text="🥗 Salatlar"), KeyboardButton(text="🍵 Issiq ichimliklar")],
            [KeyboardButton(text="📋 Tanlangan buyurtmalarni ko'rish")],
            [KeyboardButton(text="✅ Zakaz berish")],
            [KeyboardButton(text="🔙 Orqaga")]
        ],
        resize_keyboard=True
    )

def first_food_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🍲 Mastava"), KeyboardButton(text="🍲 Shoʻrva")],
            [KeyboardButton(text="🍲 Moshxoʻrda"), KeyboardButton(text="🍲 Chuchvara")],
            [KeyboardButton(text="🍲 Noxat shoʻrva")],
            [KeyboardButton(text="🔙 Orqaga")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def second_food_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🥘 Osh"), KeyboardButton(text="🥘 Lag'mon")],
            [KeyboardButton(text="🥘 Norin"), KeyboardButton(text="🥘 Kabob")],
            [KeyboardButton(text="🥘 Qozon kabob")],
            [KeyboardButton(text="🔙 Orqaga")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def salads_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🥗 Olivye salat"), KeyboardButton(text="🥗 Vinegret salat")],
            [KeyboardButton(text="🥗 Grek salat"), KeyboardButton(text="🥗 Sezar salat")],
            [KeyboardButton(text="🔙 Orqaga")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def drinks_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Pepsi"), KeyboardButton(text="Fanta")],
            [KeyboardButton(text="Coca-Cola"), KeyboardButton(text="Sprite")],
            [KeyboardButton(text="Limonad"), KeyboardButton(text="Mirinda")],
            [KeyboardButton(text="Red Bull"), KeyboardButton(text="Flesh")],
            [KeyboardButton(text="Adrenaline Rush")],
            [KeyboardButton(text="🔙 Orqaga")]
        ],
        resize_keyboard=True
    )

def hot_drinks_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🍵 Qora choy"), KeyboardButton(text="🍵 Ko'k choy")],
            [KeyboardButton(text="🍵 Limon choy")],
            [KeyboardButton(text="☕ Cappuccino"), KeyboardButton(text="☕ Americano")],
            [KeyboardButton(text="🔙 Orqaga")]
        ],
        resize_keyboard=True
    )

def payment_button_kb(amount: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"Pay {amount:,} UZS",
                callback_data=f"pay_{amount}"
            )],
        ]
    )

def back_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 Orqaga")]],
        resize_keyboard=True
    )
