from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📦 Товары"), KeyboardButton(text="🗂 Категории")],
        [KeyboardButton(text="📄 PDF с ценами"), KeyboardButton(text="📄 PDF без цен")],
    ],
    resize_keyboard=True,
    persistent=True,
)
