"""
Веб-админка и Telegram Mini App (WebApp) сервер на FastAPI.
Запуск: python -m shopflow.web_admin.server
"""

import json
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import uvicorn
from shopflow.config import STORE_NAME, WEB_ADMIN_PORT
from shopflow.database.crud import ShopCRUD

web_app = FastAPI(title=f"{STORE_NAME} - Web Portal")
crud = ShopCRUD()


@web_app.get("/", response_class=HTMLResponse)
def admin_portal():
    analytics = crud.get_admin_analytics()
    orders = crud.get_all_orders(limit=25)
    products = crud.get_products()

    order_rows = []
    for o in orders:
        status_col = "#10b981" if o['status'] == "PAID" else ("#3b82f6" if o['status'] == "PROCESSING" else ("#ef4444" if o['status'] == "CANCELLED" else "#f59e0b"))
        order_rows.append(f"""
        <tr>
            <td><b>#{o['order_num']}</b></td>
            <td>{o['first_name']} (@{o['username'] or '—'})</td>
            <td>{o['contact_phone']}</td>
            <td><span style="background:{status_col}; color:#fff; padding:3px 8px; border-radius:4px; font-size:11px; font-weight:bold;">{o['status']}</span></td>
            <td style="font-weight:bold; color:#10b981;">{o['total_amount']:,.0f} ₽</td>
            <td>{o['created_at']}</td>
            <td>
                <button onclick="updateStatus({o['id']}, 'PAID')" class="btn-sm btn-pay">Оплачен</button>
                <button onclick="updateStatus({o['id']}, 'DELIVERED')" class="btn-sm btn-deliv">Доставлен</button>
            </td>
        </tr>
        """)

    top_prod_rows = "".join([f"<tr><td>{p['product_name']}</td><td style='text-align:right;'><b>{p['qty']} шт.</b></td><td style='text-align:right; color:#10b981;'>{p['total']:,.0f} ₽</td></tr>" for p in analytics.get("top_products", [])])

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<title>{STORE_NAME} — Панель управления & WebApp</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
  body {{ background: #0f172a; color: #f8fafc; padding: 30px; }}
  .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; padding-bottom: 16px; border-bottom: 1px solid #334155; }}
  .logo {{ font-size: 22px; font-weight: 800; }}
  .logo span {{ color: #38bdf8; }}

  .nav-tabs {{ display: flex; gap: 10px; margin-bottom: 24px; }}
  .nav-tab {{ background: #1e293b; color: #94a3b8; padding: 10px 18px; border-radius: 8px; font-size: 13px; font-weight: 600; text-decoration: none; border: 1px solid #334155; }}
  .nav-tab.active {{ background: #2563eb; color: #fff; border-color: #2563eb; }}

  .kpi-row {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 24px; }}
  .kpi-card {{ background: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 18px; }}
  .kpi-lbl {{ font-size: 11px; text-transform: uppercase; color: #94a3b8; font-weight: 600; }}
  .kpi-val {{ font-size: 26px; font-weight: 800; margin-top: 4px; }}

  .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 20px; margin-bottom: 24px; }}
  .card-title {{ font-size: 16px; font-weight: 700; margin-bottom: 14px; color: #e2e8f0; }}

  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th {{ text-align: left; color: #94a3b8; font-size: 11px; text-transform: uppercase; padding: 10px; border-bottom: 1px solid #334155; }}
  td {{ padding: 10px; border-bottom: 1px solid #283548; color: #cbd5e1; }}
  
  .btn-sm {{ border: none; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: 600; cursor: pointer; }}
  .btn-pay {{ background: #065f46; color: #34d399; }}
  .btn-deliv {{ background: #1e3a8a; color: #93c5fd; margin-left: 4px; }}
</style>
</head>
<body>
  <div class="header">
    <div class="logo"><span>⚡</span> {STORE_NAME} — Admin Operations</div>
    <div><a href="/webapp" target="_blank" class="nav-tab active">📱 Открыть Telegram WebApp Витрину</a></div>
  </div>

  <div class="kpi-row">
    <div class="kpi-card">
      <div class="kpi-lbl">Выручка магазина</div>
      <div class="kpi-val" style="color:#10b981;">{analytics['total_revenue']:,.0f} ₽</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-lbl">Всего заказов</div>
      <div class="kpi-val" style="color:#38bdf8;">{analytics['total_orders']}</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-lbl">Клиентская база</div>
      <div class="kpi-val" style="color:#f59e0b;">{analytics['total_users']} покупателей</div>
    </div>
  </div>

  <div style="display:grid; grid-template-columns: 2fr 1fr; gap:20px;">
    <div class="card">
      <div class="card-title">📦 Лента последних заказов</div>
      <table>
        <thead>
          <tr>
            <th>Заказ</th>
            <th>Клиент</th>
            <th>Телефон</th>
            <th>Статус</th>
            <th>Сумма</th>
            <th>Дата</th>
            <th>Действия</th>
          </tr>
        </thead>
        <tbody>
          {''.join(order_rows)}
        </tbody>
      </table>
    </div>

    <div class="card">
      <div class="card-title">🔥 Топ продаж</div>
      <table>
        <thead>
          <tr>
            <th>Товар</th>
            <th style="text-align:right;">Продажи</th>
            <th style="text-align:right;">Оборот</th>
          </tr>
        </thead>
        <tbody>
          {top_prod_rows}
        </tbody>
      </table>
    </div>
  </div>

<script>
  async function updateStatus(id, st) {{
    await fetch('/api/orders/' + id + '/status?status=' + st, {{ method: 'POST' }});
    location.reload();
  }}
</script>
</body>
</html>"""


@web_app.get("/webapp", response_class=HTMLResponse)
def telegram_webapp_demo():
    """Интерактивная Telegram Mini App (WebApp) витрина для клиентов."""
    products = crud.get_products()
    prod_cards = []
    for p in products:
        prod_cards.append(f"""
        <div class="p-card">
            <div class="p-img">{p['image_emoji']}</div>
            <div class="p-name">{p['name']}</div>
            <div class="p-desc">{p['description']}</div>
            <div class="p-bottom">
                <div class="p-price">{p['price']:,.0f} ₽</div>
                <button class="btn-buy" onclick="buyItem('{p['name']}', {p['price']})">+ В корзину</button>
            </div>
        </div>
        """)

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ShopFlow Telegram Mini App</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
  body {{ background: #17212b; color: #fff; padding: 16px; padding-bottom: 70px; }}
  .top-title {{ font-size: 18px; font-weight: 700; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; }}
  .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
  .p-card {{ background: #242f3d; border-radius: 12px; padding: 12px; display: flex; flex-direction: column; justify-content: space-between; }}
  .p-img {{ font-size: 36px; text-align: center; margin: 8px 0; }}
  .p-name {{ font-size: 13px; font-weight: 600; line-height: 1.3; }}
  .p-desc {{ font-size: 11px; color: #8292a2; margin: 4px 0 10px; line-height: 1.3; }}
  .p-bottom {{ display: flex; justify-content: space-between; align-items: center; margin-top: auto; }}
  .p-price {{ font-size: 14px; font-weight: 700; color: #64b5f6; }}
  .btn-buy {{ background: #2f6ea5; color: #fff; border: none; padding: 6px 10px; border-radius: 6px; font-size: 11px; font-weight: 600; cursor: pointer; }}
  
  .bottom-bar {{ position: fixed; bottom: 0; left: 0; right: 0; background: #242f3d; padding: 12px 16px; border-top: 1px solid #17212b; display: flex; justify-content: space-between; align-items: center; }}
  .btn-checkout {{ background: #2ea6ff; color: #fff; border: none; padding: 10px 20px; border-radius: 8px; font-weight: 700; font-size: 13px; cursor: pointer; }}
</style>
</head>
<body>
  <div class="top-title">⚡ ShopFlow Mini App Catalog</div>
  <div class="grid">
    {''.join(prod_cards)}
  </div>

  <div class="bottom-bar">
    <div>
      <div style="font-size:11px; color:#8292a2;">Корзина:</div>
      <div id="cartCount" style="font-weight:700;">0 товаров (0 ₽)</div>
    </div>
    <button class="btn-checkout" onclick="alert('Заказ оформлен через Telegram WebApp API!')">Оформить заказ</button>
  </div>

<script>
  let total = 0;
  let count = 0;
  function buyItem(name, price) {{
    total += price;
    count += 1;
    document.getElementById('cartCount').innerText = count + ' тов. (' + total.toLocaleString() + ' ₽)';
  }}
</script>
</body>
</html>"""


@web_app.post("/api/orders/{order_id}/status")
def update_status_api(order_id: int, status: str):
    crud.update_order_status(order_id, status)
    return {"status": "ok", "order_id": order_id, "new_status": status}


if __name__ == "__main__":
    uvicorn.run("shopflow.web_admin.server:web_app", host="127.0.0.1", port=WEB_ADMIN_PORT, reload=True)

