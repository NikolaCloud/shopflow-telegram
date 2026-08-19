"""
Сервис управления корзиной и расчета скидок.
"""

from typing import Any, Dict, List, Optional
from shopflow.database.crud import ShopCRUD


class CartService:
    def __init__(self, crud: Optional[ShopCRUD] = None):
        self.crud = crud or ShopCRUD()

    def get_user_cart_summary(self, user_id: int, promo_code_str: Optional[str] = None) -> Dict[str, Any]:
        items = self.crud.get_cart_items(user_id)
        subtotal = sum(it["price"] * it["quantity"] for it in items)
        discount = 0.0
        promo_info = None

        if promo_code_str:
            promo = self.crud.check_promo(promo_code_str)
            if promo:
                discount = round(subtotal * (promo["discount_percent"] / 100), 2)
                promo_info = f"{promo['code']} (-{promo['discount_percent']}%)"

        total = max(0.0, subtotal - discount)
        return {
            "items": items,
            "total_items_count": sum(it["quantity"] for it in items),
            "subtotal": subtotal,
            "discount": discount,
            "total": total,
            "promo_applied": promo_info
        }

    def add_item(self, user_id: int, product_id: int, quantity: int = 1):
        self.crud.add_to_cart(user_id, product_id, quantity)

    def remove_item(self, user_id: int, product_id: int):
        self.crud.remove_from_cart(user_id, product_id)

    def clear(self, user_id: int):
        self.crud.clear_cart(user_id)

