from utils.db_helper import get_db


def calc_sell_tax(price, qty, price_paid, fee):
    diff = (price*qty) - price_paid - fee
    tax = 0
    if diff > 0:
        tax = round((diff * 0.2782),2)

    return ((price*qty) - fee - tax), tax

def calc_partial_sell_tax(trade_id, sell_qty, sell_price, fee):
    conn = get_db()
    rows = conn.execute("""
        SELECT id, qty, open_qty, price, total_price
        FROM transactions
        WHERE trade_id = ? AND action_id IN (1,3) AND open_qty > 0
        ORDER BY date ASC, id ASC
    """, (trade_id,)).fetchall()

    remaining = sell_qty
    total_cost = 0
    sold_qty = 0
    used_transactions = []

    for row in rows:
        if remaining == 0:
            break

        txn_id, qty, open_qty, buy_price, buy_total = row
        used_qty = min(remaining, open_qty)

        cost_part = (buy_total / qty) * used_qty
        total_cost += cost_part
        sold_qty += used_qty
        remaining -= used_qty

        used_transactions.append((txn_id, used_qty))

    total_revenue = (sell_price * sell_qty) - fee
    gain = total_revenue - total_cost
    tax = round(gain * 0.2782, 2) if gain > 0 else 0.0
    price_correct = 1 if total_revenue == ((sell_price * sell_qty) - fee - tax) else 0

    return {
        "total_price": total_revenue-tax,
        "tax": tax,
        "gain": gain,
        "price_correct": price_correct
    }, used_transactions

