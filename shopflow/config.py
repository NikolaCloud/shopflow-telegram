"""
Конфигурация платформы ShopFlow Telegram.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "shopflow.db"

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_IDS = [int(i.strip()) for i in os.getenv("ADMIN_IDS", "999999,123456").split(",") if i.strip()]

STORE_NAME = "ShopFlow Digital & Tech"
CURRENCY_SYMBOL = "₽"
WEB_ADMIN_PORT = 8080

