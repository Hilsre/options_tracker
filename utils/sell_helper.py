import streamlit as st
from utils.settings_handler import load_settings
from utils.db_helper import get_db

if "tax_rate" not in st.session_state:
    settings = load_settings()
    st.session_state["tax_rate"] = settings["tax_rate"]

tax_rate = st.session_state["tax_rate"]
tax_allowance = st.session_state["tax_allowance"]
loss_carryforward = st.session_state["loss_carryforward"]


def calc_sell_tax(price, qty, price_paid, fee):
    gross_gain = (price*qty) - price_paid - fee
    taxable_gain = gross_gain
    tax = 0
    if gross_gain > 0:
        used_loss = min(loss_carryforward, gross_gain)
        taxable_gain = taxable_gain - used_loss
        new_loss_carryforward = loss_carryforward - used_loss

        used_allowance = min(tax_allowance, taxable_gain)
        taxable_gain -= used_allowance
        new_allowance = tax_allowance - used_allowance

        tax = round((taxable_gain * tax_rate),2)

    else:
        tax = 0
        new_loss_carryforward = loss_carryforward + abs(gross_gain)
        new_allowance = tax_allowance

    return ((price*qty) - fee - tax), tax, new_loss_carryforward, new_allowance

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
    gross_gain = total_revenue - total_cost
    taxable_gain = gross_gain
    tax = 0
    if gross_gain > 0:
        used_loss = min(loss_carryforward, gross_gain)
        taxable_gain = gross_gain - used_loss
        new_loss_carryforward = loss_carryforward - used_loss

        used_allowance = min(tax_allowance, taxable_gain)
        taxable_gain -= used_allowance
        new_allowance = tax_allowance - used_allowance

        tax = round(taxable_gain * tax_rate, 2)

    else:
        tax = 0
        new_loss_carryforward = loss_carryforward + abs(gross_gain)
        new_allowance = tax_allowance

    price_correct = 1 if total_revenue == ((sell_price * sell_qty) - fee - tax) else 0

    return {
        "total_price": total_revenue-tax,
        "tax": tax,
        "gain": gross_gain-tax,
        "price_correct": price_correct,
        "loss_carryforward": new_loss_carryforward,
        "tax_allowance": new_allowance
    }, used_transactions

