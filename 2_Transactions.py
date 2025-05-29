import streamlit as st
import pandas as pd
from datetime import date

from utils.db_helper import get_options, new_transaction, get_product_choices, update_open_qty, get_db
from utils.buy_helper import get_direction_id, get_or_create_product_id, get_or_create_trade_id
from utils.sell_helper import calc_sell_tax, calc_partial_sell_tax

st.set_page_config(page_title="OptionsTracker – Transactions", layout="wide", page_icon="📥")
st.title("📥 Record Transactions")


basis_options = get_options("SELECT id, name FROM basis_products")
type_options = get_options("SELECT id, name FROM product_types")
direction_options = get_options("SELECT id, name FROM directions")
currency_options = get_options("SELECT id, symbol FROM strike_currencies")

# Actions
tabs = st.tabs([
    "Buy",
    "Rebuy",
    "Sell",
    "Parital Sell",
    "Redemption",
    "Knock-out Loss"
])


# Buy action
with tabs[0]:
    st.subheader("💼 New Purchase")
    col1, col2 = st.columns(2)
    with col1:
        basis_asset = st.selectbox("Underlying Asset", basis_options, format_func=lambda x: x[1],
                                   placeholder="Underlying Asset", key="buy_basis_asset")
        product_type = st.selectbox("Product Type", type_options, format_func=lambda x: x[1], key="buy_product_type")
        if product_type[1].lower() == "warrant":
            strategy_filtered = ["Call", "Put"]
        else:
            strategy_filtered = ["Long", "Short"]
        strategy = st.selectbox("Strategy", strategy_filtered, key="buy_strategy")

    with col2:
        strike = st.number_input("Strike", step=1.0, key="buy_strike")
        currency = st.selectbox("Currency", currency_options, format_func=lambda x: x[1],
                                placeholder="Currency", key="buy_strike_currency")

    col3, col4, col5 = st.columns(3)
    with col3:
        qty = st.number_input("Quantity", min_value=1, key="buy_qty")
    with col4:
        price = st.number_input("Price per Unit", min_value=0.0001, key="buy_price")
    with col5:
        fee = st.number_input("Fee", value=1.0, key="buy_fee")
    total_price = st.number_input("= Total Price", value=(price * qty) + fee, key="buy_total_price")
    price_correct = 0 if total_price != ((price * qty) + fee) else 1
    txn_date = st.date_input("Transaction Date", value=date.today(), format="DD.MM.YYYY", key="buy_transaction_date")

    col6, col7, col8 = st.columns(3)
    with col6:
        wkn = st.text_input("WKN", value="", key="buy_wkn")
    with col7:
        name = st.text_input("Name", value="", key="buy_name")
    with col8:
        if product_type[1] == "Optionsschein":
            expiry_date = st.date_input("Expiry Date", format="DD.MM.YYYY", key="buy_expiry_date")
        else:
            expiry_date = None

    if st.button("Save Purchase"):
        direction = get_direction_id(strategy)
        product_id = get_or_create_product_id(basis_id=basis_asset[0], product_type_id=product_type[0],
                                              direction_id=direction, strike=strike, strike_currency_id=currency[0],
                                              wkn=wkn, name=name, expiry_date=expiry_date)
        new_transaction(trade_id=get_or_create_trade_id(product_id), date=txn_date, product_id=product_id, price=price, qty=qty,
                        fee=fee, tax=0.0, total_price=total_price, price_correct=price_correct, action_id=1,
                        open_qty=qty, gain=0)
        st.rerun()


# Rebuy action
with tabs[1]:
    st.subheader("🔄 Additional Purchase (Rebuy)")
    choices = get_product_choices()
    if not choices:
        st.info("No existing products available.")
    else:
        selected_id = st.selectbox("Select Product", choices, format_func=lambda x: x[1])
        trade_id = selected_id[0]
        product_id = selected_id[3]
        open_qty = selected_id[2]
        st.caption(f"Trade ID: {trade_id}, Open Quantity: {open_qty}, Product_id: {product_id}")

        col1, col2, col3 = st.columns(3)
        with col1:
            qty = st.number_input("Quantity", min_value=1, key="rebuy_qty")
        with col2:
            price = st.number_input("Price per Unit", min_value=0.0001, key="rebuy_price")
        with col3:
            fee = st.number_input("Fee", value=1.0, key="rebuy_fee")

        total_price = st.number_input("= Total Price", value=(price * qty) + fee, key="total_price")
        price_correct = 0 if total_price != ((price * qty) + fee) else 1
        txn_date = st.date_input("Transaction Date", value=date.today(), key="rebuy_date", format="DD.MM.YYYY")

        if st.button("Save Rebuy"):
            new_transaction(trade_id=trade_id, date=txn_date, product_id=product_id, price=price, qty=qty,
                            fee=fee, tax=0.0, total_price=total_price, price_correct=price_correct, action_id=3,
                            open_qty=qty, gain=0)
            st.rerun()

# Sell action
with tabs[2]:
    st.subheader(f"📈 Record Sell")
    choices = get_product_choices()

    if not choices:
        st.info("No open positions available.")
    else:
        selected_id = st.selectbox("Select Position", choices, format_func=lambda x: x[1])
        trade_id = selected_id[0]
        product_id = selected_id[3]
        open_qty = selected_id[2]
        price_paid = selected_id[4]
        st.caption(f"Trade ID: {trade_id}, Open Quantity: {open_qty}, Product_id: {product_id}, Price_Paid: {price_paid}")

        col1, col2, col3 = st.columns(3)
        with col1:
            qty = st.number_input("Quantity", value=open_qty, key="sell_qty", disabled=True)
        with col2:
            price = st.number_input("Price per Unit", min_value=0.0, key="sell_price")
        with col3:
            fee = st.number_input("Fee", value=1.0, key="sell_fee")
        temp = calc_sell_tax(price, qty, price_paid, fee)
        temp_total_price = temp[0]
        tax = temp[1]
        col4, col5 = st.columns(2)
        with col4:
            total_price = st.number_input("= Total Price (after tax)", value=temp_total_price, key="total_sell_price")
            price_correct = 0 if total_price != ((price * qty) - fee - tax) else 1
        with col5:
            tax = st.number_input("Tax", value=tax, key="sell_tax")
        gain = st.number_input("Estimated gain/loss:", value=total_price-price_paid, disabled=True)

        txn_date = st.date_input("Transaction Date", value=date.today(), key="sell_date", format="DD.MM.YYYY")


        if st.button("Save Sale"):
            new_transaction(trade_id=trade_id, date=txn_date, product_id=product_id, price=price, qty=open_qty, fee=fee,
                    tax=tax, total_price=total_price, price_correct=price_correct, action_id=2, open_qty=0, gain=round(gain,2))
            update_open_qty(trade_id, open_qty=0)
            st.rerun()

# Parital Sell action
with tabs[3]:
    st.subheader(f"📈 Record Partial Sell")
    choices = get_product_choices()

    if not choices:
        st.info("No open positions available.")
    else:
        selected_id = st.selectbox("Select Position", choices, format_func=lambda x: x[1], key="partial_sell_select_position")
        trade_id = selected_id[0]
        product_id = selected_id[3]
        open_qty = selected_id[2]
        price_paid = selected_id[4]
        st.caption(f"Trade ID: {trade_id}, Open Quantity: {open_qty}, Product_id: {product_id}, Price_Paid: {price_paid}")

        col1, col2, col3 = st.columns(3)
        with col1:
            qty = st.number_input("Quantity", min_value=0,max_value=open_qty, key="partial_sell_qty")
        with col2:
            price = st.number_input("Price per Unit", min_value=0.0, key="partial_sell_price")
        with col3:
            fee = st.number_input("Fee", value=1.0, key="partial_sell_fee")
        temp = calc_partial_sell_tax(trade_id=trade_id, sell_qty=qty, sell_price=price, fee=fee)
        temp_calc = temp[0]
        total_price = temp_calc["total_price"]
        tax = temp_calc["tax"]
        gain = temp_calc["gain"]
        price_correct = temp_calc["price_correct"]
        col4, col5 = st.columns(2)
        with col4:
            total_price = st.number_input("= Total Price (after tax)", value=total_price, key="partial_total_sell_price")
        with col5:
            tax = st.number_input("Tax", value=tax, key="partial_sell_tax")
        gain = st.number_input("Estimated gain/loss:", value=gain, disabled=True, key="partial_sell_gain")

        txn_date = st.date_input("Transaction Date", value=date.today(), key="partial_sell_date", format="DD.MM.YYYY")


        if st.button("Save partial Sale"):
            new_transaction(trade_id=trade_id, date=txn_date, product_id=product_id, price=price, qty=qty, fee=fee,
                    tax=tax, total_price=total_price, price_correct=price_correct, action_id=4, open_qty=None, gain=round(gain,2))

            conn = get_db()
            print(temp)
            for txn_id, used_qty in temp[1]:
                res = conn.execute("SELECT open_qty FROM transactions WHERE id = ?", (txn_id,)).fetchone()
                if res is not None:
                    current_qty = res[0]
                    new_qty = max(current_qty - used_qty, 0)
                    conn.execute("UPDATE transactions SET open_qty = ? WHERE id = ?", (new_qty, txn_id))
            conn.commit()
            st.rerun()


# redemption action
with tabs[4]:
    st.subheader(f"📉 Record redemption")
    choices = get_product_choices()

    if not choices:
        st.info("No open positions available.")
    else:
        selected_id = st.selectbox("Select Position", choices, format_func=lambda x: x[1],
                                   key="redemption_select_position")
        trade_id = selected_id[0]
        product_id = selected_id[3]
        open_qty = selected_id[2]
        price_paid = selected_id[4]
        st.caption(
            f"Trade ID: {trade_id}, Open Quantity: {open_qty}, Product_id: {product_id}, Price_Paid: {price_paid}")

        total_price = st.number_input("= Total Price",key="redemption_price", step=1.0)

        gain = st.number_input("Estimated gain/loss:", value=total_price - price_paid, disabled=True, key="redemption_gain")

        txn_date = st.date_input("Transaction Date", value=date.today(), key="redemption_date", format="DD.MM.YYYY")

        if st.button("Save redemption"):
            new_transaction(trade_id=trade_id, date=txn_date, product_id=product_id, price=0, qty=0, fee=0,
                            tax=0, total_price=total_price, price_correct=1, action_id=5, open_qty=None,
                            gain=round(gain, 2))
            update_open_qty(trade_id=trade_id, open_qty=0)
            st.rerun()


# knock-out action
with tabs[5]:
    st.subheader(f"☠️ ️Record Knock-out Loss")
    choices = get_product_choices()

    if not choices:
        st.info("No open positions available.")
    else:
        selected_id = st.selectbox("Select Position", choices, format_func=lambda x: x[1],
                                   key="ko_select_position")
        trade_id = selected_id[0]
        product_id = selected_id[3]
        open_qty = selected_id[2]
        price_paid = selected_id[4]
        st.caption(
            f"Trade ID: {trade_id}, Open Quantity: {open_qty}, Product_id: {product_id}, Price_Paid: {price_paid}")

        gain = st.number_input("Estimated gain/loss:", value=-price_paid, disabled=True, key="ko_gain")

        txn_date = st.date_input("Transaction Date", value=date.today(), key="ko_date", format="DD.MM.YYYY")

        if st.button("Save KO"):
            new_transaction(trade_id=trade_id, date=txn_date, product_id=product_id, price=0, qty=0, fee=0,
                            tax=0, total_price=0, price_correct=1, action_id=6, open_qty=None,
                            gain=round(gain, 2))
            update_open_qty(trade_id=trade_id, open_qty=0)
            st.rerun()


st.divider()

# Show last transactions
st.subheader("📄 Recent Transactions")
conn = get_db()
query = """
    SELECT d.name || '@' || CAST(p.strike AS TEXT) || sc.symbol || ' ' || bp.name,
           t.price,
           t.qty,
           t.tax,
           t.total_price,
           a.name,
           t.open_qty,
           t.date
    FROM transactions t
    JOIN products p ON t.product_id = p.id
    JOIN directions d ON p.direction_id = d.id
    JOIN basis_products bp ON p.basis_product_id = bp.id
    JOIN strike_currencies sc ON p.strike_currency_id = sc.id
    JOIN actions a ON t.action_id = a.id
    ORDER BY t.id DESC
    LIMIT 10
"""
column_names = ["Name", "Price", "Quantity", "Tax", "Total", "Action", "Open Quantity", "Date"]

try:
    rows = conn.execute(query).fetchall()
    df = pd.DataFrame(rows, columns=column_names)
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
except Exception as e:
    st.error(f"Error loading data: {e}")
    df = pd.DataFrame()

st.dataframe(df, use_container_width=True)
