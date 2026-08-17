"""
Инициализация базы данных SQLite и посев начального каталога товаров и промокодов.
"""

from datetime import datetime
import sqlite3
from shopflow.config import DB_PATH


class DatabaseConnection:
    def __init__(self, db_path=DB_PATH):
        self.db_path = str(db_path)
        self.init_schema()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_schema(self):
        with self.get_connection() as conn:
            c = conn.cursor()
            # Таблица пользователей
            c.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT NOT NULL,
                    phone TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            # Категории
            c.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    icon TEXT NOT NULL
                )
            """)
            # Товары
            c.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    price REAL NOT NULL,
                    stock INTEGER NOT NULL DEFAULT 10,
                    image_emoji TEXT NOT NULL DEFAULT '📦',
                    FOREIGN KEY (category_id) REFERENCES categories(id)
                )
            """)
            # Корзина
            c.execute("""
                CREATE TABLE IF NOT EXISTS cart (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (product_id) REFERENCES products(id),
                    UNIQUE(user_id, product_id)
                )
            """)
            # Заказы
            c.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_num TEXT UNIQUE NOT NULL,
                    user_id INTEGER NOT NULL,
                    total_amount REAL NOT NULL,
                    discount_amount REAL NOT NULL DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'NEW',
                    shipping_address TEXT NOT NULL,
                    contact_phone TEXT NOT NULL,
                    promo_code TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            # Позиции заказов
            c.execute("""
                CREATE TABLE IF NOT EXISTS order_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    product_name TEXT NOT NULL,
                    price REAL NOT NULL,
                    quantity INTEGER NOT NULL,
                    FOREIGN KEY (order_id) REFERENCES orders(id)
                )
            """)
            # Промокоды
            c.execute("""
                CREATE TABLE IF NOT EXISTS promo_codes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    discount_percent INTEGER NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1
                )
            """)
            conn.commit()

        self._seed_default_data()

    def _seed_default_data(self):
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM categories")
            if c.fetchone()[0] == 0:
                categories = [
                    (1, "Смартфоны & Гаджеты", "📱"),
                    (2, "Аудио & Наушники", "🎧"),
                    (3, "Аксессуары & Питание", "⚡"),
                ]
                c.executemany("INSERT INTO categories (id, name, icon) VALUES (?, ?, ?)", categories)

                products = [
                    (1, 1, "iPhone 16 Pro Max 256GB", "Флагманский смартфон с титановым корпусом и камерой 48 МП", 134990.0, 8, "📱"),
                    (2, 1, "Samsung Galaxy S24 Ultra", "Экран Dynamic AMOLED 2X, перо S-Pen, зум 100x", 119990.0, 12, "📲"),
                    (3, 2, "Apple AirPods Pro 2 (USB-C)", "Активное шумоподавление нового поколения и режим прозрачности", 24990.0, 25, "🎧"),
                    (4, 2, "Sony WH-1000XM5 Black", "Премиальные полноразмерные наушники с лучшим ANC в классе", 34990.0, 14, "🎵"),
                    (5, 3, "Беспроводная зарядка MagSafe", "Оригинальное магнитное зарядное устройство мощностью 15 Вт", 4990.0, 40, "⚡"),
                    (6, 3, "PowerBank Baseus Blade 20000mAh", "Ультратонкий внешний аккумулятор с быстрой зарядкой 100 Вт", 7490.0, 18, "🔋"),
                ]
                c.executemany("INSERT INTO products (id, category_id, name, description, price, stock, image_emoji) VALUES (?, ?, ?, ?, ?, ?, ?)", products)

                promos = [
                    ("START10", 10, 1),
                    ("WELCOME20", 20, 1),
                ]
                c.executemany("INSERT INTO promo_codes (code, discount_percent, is_active) VALUES (?, ?, ?)", promos)

                # Начальный демо-пользователь и заказы для красивой аналитики
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                c.execute("INSERT OR IGNORE INTO users (id, telegram_id, username, first_name, phone, created_at) VALUES (1, 999999, 'alex_demo', 'Александр', '+7 999 123-45-67', ?)", (now,))

                orders = [
                    (1, "ORD-8491", 1, 159980.0, 0.0, "PAID", "г. Москва, ул. Тверская, д. 12, кв. 45", "+7 999 123-45-67", None, now),
                    (2, "ORD-8492", 1, 24990.0, 2499.0, "PROCESSING", "г. Санкт-Петербург, Невский пр., д. 80", "+7 999 765-43-21", "START10", now),
                ]
                c.executemany("INSERT OR IGNORE INTO orders (id, order_num, user_id, total_amount, discount_amount, status, shipping_address, contact_phone, promo_code, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", orders)

                order_items = [
                    (1, 1, 1, "iPhone 16 Pro Max 256GB", 134990.0, 1),
                    (2, 1, 3, "Apple AirPods Pro 2 (USB-C)", 24990.0, 1),
                    (3, 2, 3, "Apple AirPods Pro 2 (USB-C)", 24990.0, 1),
                ]
                c.executemany("INSERT OR IGNORE INTO order_items (id, order_id, product_id, product_name, price, quantity) VALUES (?, ?, ?, ?, ?, ?)", order_items)
                conn.commit()

