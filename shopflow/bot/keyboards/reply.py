"""
Главная Reply-клавиатура Telegram.
"""

from telebot import types


def get_main_reply_keyboard(is_admin: bool = False) -> types.ReplyKeyboardMarkup:
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🛍️ Каталог товаров"),
        types.KeyboardButton("🛒 Моя корзина"),
        types.KeyboardButton("📦 История заказов"),
        types.KeyboardButton("ℹ️ О магазине & Гарантия")
    )
    if is_admin:
        markup.add(types.KeyboardButton("⚙️ Админ-панель"))
    return markup

