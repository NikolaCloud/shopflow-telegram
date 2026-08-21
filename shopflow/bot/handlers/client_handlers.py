"""
Обработчики команд и сценариев клиентов (каталог, корзина, чекаут).
"""

from typing import Dict
from shopflow.bot.keyboards.inline import (
    get_cart_keyboard,
    get_categories_inline_keyboard,
    get_order_actions_keyboard,
    get_product_detail_keyboard,
    get_products_inline_keyboard,
)
from shopflow.bot.keyboards.reply import get_main_reply_keyboard
from shopflow.config import ADMIN_IDS, STORE_NAME
from shopflow.database.crud import ShopCRUD
from shopflow.services.cart_service import CartService
import telebot

# Временное FSM-состояние чекаута
checkout_states: Dict[int, Dict] = {}


def register_client_handlers(bot: telebot.TeleBot, crud: ShopCRUD):
    cart_service = CartService(crud)

    @bot.message_handler(commands=["start", "help"])
    def cmd_start(message):
        user = crud.get_or_create_user(
            telegram_id=message.from_user.id,
            first_name=message.from_user.first_name,
            username=message.from_user.username
        )
        is_admin = message.from_user.id in ADMIN_IDS

        text = (
            f"Здравствуйте, {message.from_user.first_name}! 👋\n\n"
            f"Добро пожаловать в **{STORE_NAME}**.\n"
            "У нас вы можете заказать оригинальную технику и аксессуары с официальной гарантией и быстрой доставкой.\n\n"
            "Выберите интересующий раздел в меню ниже:"
        )
        bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=get_main_reply_keyboard(is_admin))

    @bot.message_handler(func=lambda msg: msg.text == "🛍️ Каталог товаров")
    def show_categories(message):
        cats = crud.get_categories()
        bot.send_message(
            message.chat.id,
            "📂 **Категории каталога:**\nВыберите нужный раздел или откройте WebApp-витрину:",
            parse_mode="Markdown",
            reply_markup=get_categories_inline_keyboard(cats)
        )

    @bot.callback_query_handler(func=lambda c: c.data == "back_categories")
    def cb_back_categories(call):
        cats = crud.get_categories()
        bot.edit_message_text(
            "📂 **Категории каталога:**",
            call.message.chat.id, call.message.message_id,
            parse_mode="Markdown",
            reply_markup=get_categories_inline_keyboard(cats)
        )

    @bot.callback_query_handler(func=lambda c: c.data.startswith("cat_"))
    def cb_show_category_products(call):
        cat_id = int(call.data.replace("cat_", ""))
        products = crud.get_products(category_id=cat_id)
        if not products:
            bot.answer_callback_query(call.id, "В этой категории пока нет товаров в наличии.")
            return

        bot.edit_message_text(
            "📦 **Выберите товар для просмотра характеристик:**",
            call.message.chat.id, call.message.message_id,
            parse_mode="Markdown",
            reply_markup=get_products_inline_keyboard(products, cat_id)
        )

    @bot.callback_query_handler(func=lambda c: c.data.startswith("prod_"))
    def cb_show_product_detail(call):
        prod_id = int(call.data.replace("prod_", ""))
        p = crud.get_product_by_id(prod_id)
        if not p:
            bot.answer_callback_query(call.id, "Товар не найден.")
            return

        text = (
            f"{p['image_emoji']} **{p['name']}**\n\n"
            f"📝 {p['description']}\n\n"
            f"💰 Стоимость: **{p['price']:,.0f} ₽**\n"
            f"📦 В наличии на складе: {p['stock']} шт."
        )
        bot.edit_message_text(
            text,
            call.message.chat.id, call.message.message_id,
            parse_mode="Markdown",
            reply_markup=get_product_detail_keyboard(p['id'], p['category_id'])
        )

    @bot.callback_query_handler(func=lambda c: c.data.startswith("add_"))
    def cb_add_to_cart(call):
        prod_id = int(call.data.replace("add_", ""))
        user = crud.get_or_create_user(call.from_user.id, call.from_user.first_name, call.from_user.username)
        cart_service.add_item(user["id"], prod_id, quantity=1)
        bot.answer_callback_query(call.id, "✅ Товар успешно добавлен в корзину!", show_alert=False)

    @bot.message_handler(func=lambda msg: msg.text == "🛒 Моя корзина")
    @bot.callback_query_handler(func=lambda c: c.data == "open_cart")
    def show_cart(event):
        chat_id = event.chat.id if hasattr(event, "chat") else event.message.chat.id
        from_user = event.from_user
        user = crud.get_or_create_user(from_user.id, from_user.first_name, from_user.username)
        state = checkout_states.get(user["id"], {})
        promo = state.get("promo")

        cart_data = cart_service.get_user_cart_summary(user["id"], promo_code_str=promo)
        if not cart_data["items"]:
            text = "🛒 Ваша корзина пуста.\nОткройте каталог, чтобы добавить товары!"
            if hasattr(event, "message"):
                bot.send_message(chat_id, text)
            else:
                bot.send_message(chat_id, text)
            return

        lines = ["🛒 **Ваша корзина:**\n"]
        for it in cart_data["items"]:
            lines.append(f"• {it['image_emoji']} {it['name']} — {it['quantity']} шт. × {it['price']:,.0f} ₽")

        lines.append(f"\nСумма: **{cart_data['subtotal']:,.0f} ₽**")
        if cart_data["discount"] > 0:
            lines.append(f"Скидка по промокоду ({cart_data['promo_applied']}): **-{cart_data['discount']:,.0f} ₽**")
        lines.append(f"Итого к оплате: **{cart_data['total']:,.0f} ₽**")

        bot.send_message(chat_id, "\n".join(lines), parse_mode="Markdown", reply_markup=get_cart_keyboard(cart_data["items"]))

    @bot.callback_query_handler(func=lambda c: c.data.startswith("del_"))
    def cb_delete_cart_item(call):
        prod_id = int(call.data.replace("del_", ""))
        user = crud.get_or_create_user(call.from_user.id, call.from_user.first_name, call.from_user.username)
        cart_service.remove_item(user["id"], prod_id)
        bot.answer_callback_query(call.id, "Товар удален из корзины.")
        show_cart(call)

    @bot.callback_query_handler(func=lambda c: c.data == "clear_cart")
    def cb_clear_cart(call):
        user = crud.get_or_create_user(call.from_user.id, call.from_user.first_name, call.from_user.username)
        cart_service.clear(user["id"])
        bot.answer_callback_query(call.id, "Корзина очищена.")
        bot.edit_message_text("🛒 Ваша корзина очищена.", call.message.chat.id, call.message.message_id)

    @bot.callback_query_handler(func=lambda c: c.data == "apply_promo")
    def cb_apply_promo(call):
        bot.send_message(call.message.chat.id, "Введите промокод (например: `START10` или `WELCOME20`):", parse_mode="Markdown")
        bot.register_next_step_handler(call.message, process_promo_code)

    def process_promo_code(message):
        code = message.text.strip().upper()
        promo = crud.check_promo(code)
        user = crud.get_or_create_user(message.from_user.id, message.from_user.first_name, message.from_user.username)
        if promo:
            checkout_states[user["id"]] = {"promo": code}
            bot.send_message(message.chat.id, f"🎉 Промокод **{code}** активирован (-{promo['discount_percent']}%)!", parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, "❌ Промокод не найден или срок действия истек.")
        show_cart(message)

    # ================= FSM ОФОРМЛЕНИЯ ЗАКАЗА =================
    @bot.callback_query_handler(func=lambda c: c.data == "checkout_start")
    def cb_start_checkout(call):
        user = crud.get_or_create_user(call.from_user.id, call.from_user.first_name, call.from_user.username)
        items = crud.get_cart_items(user["id"])
        if not items:
            bot.answer_callback_query(call.id, "Корзина пуста!")
            return

        bot.send_message(call.message.chat.id, "📦 Шаг 1 из 2:\nУкажите адрес доставки (Город, улица, дом, квартира):")
        bot.register_next_step_handler(call.message, process_address_step)

    def process_address_step(message):
        user = crud.get_or_create_user(message.from_user.id, message.from_user.first_name, message.from_user.username)
        if user["id"] not in checkout_states:
            checkout_states[user["id"]] = {}
        checkout_states[user["id"]]["address"] = message.text.strip()

        bot.send_message(message.chat.id, "📞 Шаг 2 из 2:\nВведите ваш контактный номер телефона для связи с курьером:")
        bot.register_next_step_handler(message, process_phone_step)

    def process_phone_step(message):
        user = crud.get_or_create_user(message.from_user.id, message.from_user.first_name, message.from_user.username)
        state = checkout_states.get(user["id"], {})
        phone = message.text.strip()
        address = state.get("address", "Самовывоз")
        promo = state.get("promo")

        order = crud.create_order(
            user_id=user["id"],
            shipping_address=address,
            contact_phone=phone,
            promo_code_str=promo
        )

        if not order:
            bot.send_message(message.chat.id, "Ошибка при создании заказа. Проверьте корзину.")
            return

        checkout_states[user["id"]] = {}  # Сброс FSM

        text = (
            f"🎉 **Заказ успешно оформлен!**\n\n"
            f"Номер заказа: **#{order['order_num']}**\n"
            f"Адрес доставки: {address}\n"
            f"Сумма к оплате: **{order['total_amount']:,.0f} ₽**\n"
            f"Статус: `NEW (Ожидает подтверждения)`\n\n"
            "Менеджер свяжется с вами по указанному телефону в течение 10 минут."
        )
        bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=get_order_actions_keyboard(order["id"]))

    @bot.callback_query_handler(func=lambda c: c.data.startswith("pay_"))
    def cb_pay_order(call):
        order_id = int(call.data.replace("pay_", ""))
        crud.update_order_status(order_id, "PAID")
        bot.answer_callback_query(call.id, "💳 Оплата успешно проведена (Демо-режим)!", show_alert=True)
        bot.edit_message_text(
            f"✅ **Заказ #{order_id} успешно оплачен!**\nСтатус изменен на: `PAID`. Передан на склад сборки.",
            call.message.chat.id, call.message.message_id,
            parse_mode="Markdown"
        )

    @bot.message_handler(func=lambda msg: msg.text == "📦 История заказов")
    def show_order_history(message):
        user = crud.get_or_create_user(message.from_user.id, message.from_user.first_name, message.from_user.username)
        orders = crud.get_user_orders(user["id"])
        if not orders:
            bot.send_message(message.chat.id, "У вас пока нет оформленных заказов.")
            return

        lines = ["📦 **История ваших заказов:**\n"]
        for o in orders:
            lines.append(f"• Заказ **#{o['order_num']}** — {o['total_amount']:,.0f} ₽ [{o['status']}] от {o['created_at']}")

        bot.send_message(message.chat.id, "\n".join(lines), parse_mode="Markdown")

    @bot.message_handler(func=lambda msg: msg.text == "ℹ️ О магазине & Гарантия")
    def show_info(message):
        text = (
            f"🏢 **{STORE_NAME}**\n\n"
            "• Только 100% оригинальная продукция с гарантией 1 год.\n"
            "• Быстрая курьерская доставка по всей стране.\n"
            "• Оплата при получении картой или наличными курьеру.\n\n"
            "💬 Поддержка: @shopflow_support"
        )
        bot.send_message(message.chat.id, text, parse_mode="Markdown")

