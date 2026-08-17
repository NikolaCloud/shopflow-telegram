"""
Модели предметной области ShopFlow: пользователи, товары, корзина, заказы и промокоды.
"""

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


@dataclass
class User:
    id: int
    telegram_id: int
    username: Optional[str]
    first_name: str
    phone: Optional[str]
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Category:
    id: int
    name: str
    icon: str


@dataclass
class Product:
    id: int
    category_id: int
    name: str
    description: str
    price: float
    stock: int
    image_emoji: str


@dataclass
class CartItem:
    id: int
    user_id: int
    product_id: int
    product_name: str
    price: float
    quantity: int


@dataclass
class Order:
    id: int
    order_num: str
    user_id: int
    total_amount: float
    discount_amount: float
    status: str       # NEW, PAID, PROCESSING, DELIVERED, CANCELLED
    shipping_address: str
    contact_phone: str
    promo_code: Optional[str]
    created_at: str
    items: Optional[List[Dict[str, Any]]] = None


@dataclass
class PromoCode:
    id: int
    code: str
    discount_percent: int
    is_active: int

