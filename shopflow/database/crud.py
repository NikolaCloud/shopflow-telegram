"""
CRUD-операции базы данных для пользователей, корзины, каталога и заказов.
"""

from datetime import datetime
import random
from typing import Any, Dict, List, Optional
from shopflow.database.connection import DatabaseConnection


class ShopCRUD:
    def __init__(self, db: Optional[DatabaseConnection] = None):
        self.db = db or DatabaseConnection()

    def get_or_create_user(self, telegram_id: int, first_name: str, username: Optional[str] = None) -> Dict[str, Any]:
        with self.db.get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
            row = c.fetchone()
            if row:
                return dict(row)

            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("""
                INSERT INTO users (telegram_id, username, first_name, created_at)
                VALUES (?, ?, ?, ?)
            """, (telegram_id, username, first_name, now))
            conn.commit()
            new_id = c.lastrowid
            return {"id": new_id, "telegram_id": telegram_id, "username": username, "first_name": first_name, "phone": None, "created_at": now}

    def update_user_phone(self, user_id: int, phone: str):
        with self.db.get_connection() as conn:
            c = conn.cursor()
            c.execute("UPDATE users SET phone = ? WHERE id = ?", (phone, user_id))
            conn.commit()

    def get_categories(self) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM categories ORDER BY id ASC")
            return [dict(r) for r in c.fetchall()]

    def get_products(self, category_id: Optional[int] = None) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            c = conn.cursor()
            if category_id:
                c.execute("SELECT * FROM products WHERE category_id = ? AND stock > 0 ORDER BY id ASC", (category_id,))
            else:
                c.execute("SELECT * FROM products WHERE stock > 0 ORDER BY id ASC")
            return [dict(r) for r in c.fetchall()]

    def get_product_by_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM products WHERE id = ?", (product_id,))
            row = c.fetchone()
            return dict(row) if row else None

    # Корзина
    def add_to_cart(self, user_id: int, product_id: int, quantity: int = 1):
        with self.db.get_connection() as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO cart (user_id, product_id, quantity)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, product_id) DO UPDATE SET quantity = quantity + ?
            """, (user_id, product_id, quantity, quantity))
            conn.commit()

    def get_cart_items(self, user_id: int) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            c = conn.cursor()
            c.execute("""
                SELECT c.id as cart_id, c.quantity, p.id as product_id, p.name, p.price, p.image_emoji
                FROM cart c
                JOIN products p ON c.product_id = p.id
                WHERE c.user_id = ?
            """, (user_id,))
            return [dict(r) for r in c.fetchall()]

    def remove_from_cart(self, user_id: int, product_id: int):
        with self.db.get_connection() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM cart WHERE user_id = ? AND product_id = ?", (user_id, product_id))
            conn.commit()

    def clear_cart(self, user_id: int):
        with self.db.get_connection() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
            conn.commit()

    # Промокоды
    def check_promo(self, code: str) -> Optional[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM promo_codes WHERE code = ? AND is_active = 1", (code.upper().strip(),))
            row = c.fetchone()
            return dict(row) if row else None

    # Оформление заказа
    def create_order(self, user_id: int, shipping_address: str, contact_phone: str, promo_code_str: Optional[str] = None) -> Optional[Dict[str, Any]]:
        items = self.get_cart_items(user_id)
        if not items:
            return None

        subtotal = sum(it["price"] * it["quantity"] for it in items)
        discount = 0.0

        if promo_code_str:
            promo = self.check_promo(promo_code_str)
            if promo:
                discount = round(subtotal * (promo["discount_percent"] / 100), 2)

        total = max(0.0, subtotal - discount)
        order_num = f"ORD-{random.randint(1000, 9999)}"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with self.db.get_connection() as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO orders (order_num, user_id, total_amount, discount_amount, status, shipping_address, contact_phone, promo_code, created_at)
                VALUES (?, ?, ?, ?, 'NEW', ?, ?, ?, ?)
            """, (order_num, user_id, total, discount, shipping_address, contact_phone, promo_code_str, now))
            order_id = c.lastrowid

            order_items = [
                (order_id, it["product_id"], it["name"], it["price"], it["quantity"])
                for it in items
            ]
            c.executemany("""
                INSERT INTO order_items (order_id, product_id, product_name, price, quantity)
                VALUES (?, ?, ?, ?, ?)
            """, order_items)

            # Очистка корзины
            c.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
            conn.commit()

        return {
            "id": order_id,
            "order_num": order_num,
            "total_amount": total,
            "discount_amount": discount,
            "status": "NEW",
            "items_count": len(items)
        }

    def get_user_orders(self, user_id: int) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC", (user_id,))
            return [dict(r) for r in c.fetchall()]

    def get_all_orders(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            c = conn.cursor()
            c.execute("""
                SELECT o.*, u.first_name, u.username, u.telegram_id
                FROM orders o
                JOIN users u ON o.user_id = u.id
                ORDER BY o.id DESC LIMIT ?
            """, (limit,))
            return [dict(r) for r in c.fetchall()]

    def update_order_status(self, order_id: int, new_status: str):
        with self.db.get_connection() as conn:
            c = conn.cursor()
            c.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
            conn.commit()

    def get_admin_analytics(self) -> Dict[str, Any]:
        with self.db.get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM orders")
            total_orders = c.fetchone()[0]

            c.execute("SELECT SUM(total_amount) FROM orders WHERE status != 'CANCELLED'")
            rev = c.fetchone()[0]
            total_revenue = round(rev, 2) if rev else 0.0

            c.execute("SELECT COUNT(*) FROM users")
            total_users = c.fetchone()[0]

            c.execute("""
                SELECT product_name, SUM(quantity) as qty, SUM(price * quantity) as total
                FROM order_items
                GROUP BY product_name
                ORDER BY qty DESC LIMIT 5
            """)
            top_products = [dict(r) for r in c.fetchall()]

            return {
                "total_orders": total_orders,
                "total_revenue": total_revenue,
                "total_users": total_users,
                "top_products": top_products
            }

