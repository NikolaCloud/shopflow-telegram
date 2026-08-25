"""
Комплексный запуск платформы ShopFlow:
1. Веб-панель управления и WebApp витрина (FastAPI на http://localhost:8080)
2. Фоновый Telegram-бот
"""

import threading
import time
import uvicorn
from shopflow.bot.handlers.client_handlers import register_client_handlers
from shopflow.config import BOT_TOKEN, WEB_ADMIN_PORT
from shopflow.database.crud import ShopCRUD
from shopflow.web_admin.server import web_app
import telebot

def run_bot():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("ℹ️ BOT_TOKEN не задан. Бот работает в режиме эмулятора через WebApp на http://localhost:8080/webapp")
        return

    bot = telebot.TeleBot(BOT_TOKEN)
    crud = ShopCRUD()
    register_client_handlers(bot, crud)
    print("🤖 Telegram-бот успешно запущен в фоновом потоке...")
    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"Ошибка polling: {e}")

def run_web():
    print(f"🌐 Панель управления магазином доступна: http://localhost:{WEB_ADMIN_PORT}")
    print(f"📱 Telegram Mini App витрина доступна: http://localhost:{WEB_ADMIN_PORT}/webapp")
    uvicorn.run(web_app, host="127.0.0.1", port=WEB_ADMIN_PORT, log_level="warning")

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    run_web()

