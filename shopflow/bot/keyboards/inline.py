"""
Генераторы Inline-клавиатур Telegram для каталога, корзины и Mini App.
"""

from typing import Any, Dict, List
from telebot import types


def get_categories_inline_keyboard(categories: List[Dict[str, Any]]) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=1)
    for cat in categories:
        markup.add(types.InlineKeyboardButton(f"{cat['icon']} {cat['name']}", callback_data=f"cat_{cat['id']}"))
    markup.add(types.InlineKeyboardButton("🌐 Открыть WebApp Каталог", web_app=types.WebAppInfo(url="http://localhost:8080/webapp")))
    return markup


def get_products_inline_keyboard(products: List[Dict[str, Any]], category_id: int) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=1)
    for p in products:
        markup.add(types.InlineKeyboardButton(
            f"{p['image_emoji']} {p['name']} — {p['price']:,.0f} ₽",
            callback_data=f"prod_{p['id']}"
        ))
    markup.add(types.InlineKeyboardButton("⬅️ Назад к категориям", callback_data="back_categories"))
    return markup


def get_product_detail_keyboard(product_id: int, category_id: int) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("➕ В корзину", callback_data=f"add_{product_id}"),
        types.InlineKeyboardButton("🛒 Перейти в корзину", callback_data="open_cart")
    )
    markup.add(types.InlineKeyboardButton("⬅️ К списку товаров", callback_data=f"cat_{category_id}"))
    return markup


def get_cart_keyboard(cart_items: List[Dict[str, Any]]) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=2)
    for it in cart_items:
        markup.add(
            types.InlineKeyboardButton(f"❌ {it['name'][:18]}...", callback_data=f"del_{it['product_id']}"),
            types.InlineKeyboardButton(f"{it['quantity']} шт. × {it['price']:,.0f} ₽", callback_data="noop")
        )
    markup.add(
        types.InlineKeyboardButton("🎟️ Ввести промокод", callback_data="apply_promo"),
        types.InlineKeyboardButton("🗑️ Очистить корзину", callback_data="clear_cart")
    )
    markup.add(types.InlineKeyboardButton("💳 Оформить заказ", callback_data="checkout_start"))
    return markup


def get_order_actions_keyboard(order_id: int) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("💳 Оплатить картой / СБП (Демо)", callback_data=f"pay_{order_id}"))
    return markup

