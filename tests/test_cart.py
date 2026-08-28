"""
Тесты сервиса корзины, промокодов и расчета заказов ShopFlow.
"""

from shopflow.database.crud import ShopCRUD
from shopflow.services.cart_service import CartService


def test_cart_operations():
    crud = ShopCRUD()
    cart = CartService(crud)

    user = crud.get_or_create_user(888888, "Test User", "test_user")
    cart.clear(user["id"])

    # Добавление товаров
    cart.add_item(user["id"], product_id=1, quantity=1)  # iPhone: 134,990
    cart.add_item(user["id"], product_id=3, quantity=2)  # AirPods: 24,990 x 2 = 49,980

    summary = cart.get_user_cart_summary(user["id"])
    expected_subtotal = 134990.0 + (24990.0 * 2)
    assert summary["subtotal"] == expected_subtotal
    assert summary["total_items_count"] == 3

    # Проверка применения промокода START10 (10%)
    summary_promo = cart.get_user_cart_summary(user["id"], promo_code_str="START10")
    expected_discount = round(expected_subtotal * 0.10, 2)
    assert summary_promo["discount"] == expected_discount
    assert summary_promo["total"] == expected_subtotal - expected_discount

    cart.clear(user["id"])

