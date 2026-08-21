"""
Запуск Telegram-бота ShopFlow.
"""

from shopflow.bot.handlers.client_handlers import register_client_handlers
from shopflow.config import BOT_TOKEN
from shopflow.database.crud import ShopCRUD
import telebot

bot = telebot.TeleBot(BOT_TOKEN)
crud = ShopCRUD()

register_client_handlers(bot, crud)

if __name__ == "__main__":
    print("🤖 Бот ShopFlow запущен и ожидает сообщений...")
    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"Ошибка polling бота (укажите BOT_TOKEN): {e}")

