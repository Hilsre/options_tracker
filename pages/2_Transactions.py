import streamlit as st
import pandas as pd
from datetime import date


from utils.db_helper import (get_options, new_transaction, get_product_choices, update_open_qty, get_db,
                             update_loss_carryforward, update_tax_allowance)
from utils.buy_helper import get_direction_id, get_or_create_product_id, get_or_create_trade_id
from utils.sell_helper import calc_sell_tax, calc_partial_sell_tax, tax_allowance
from utils.settings_handler import get_lang, load_settings

st.set_page_config(page_title="OptionsTracker – Transactions", layout="wide", page_icon="📥")

if "tax_rate" not in st.session_state or "date_format" not in st.session_state:
    settings = load_settings()
    for key, value in settings.items():
        st.session_state[key] = value

T = get_lang()
tax_rate = st.session_state["tax_rate"]
date_format = st.session_state["date_format"]

st.title(T["title"])


basis_options = get_options("SELECT id, name FROM basis_products")
type_options = get_options("SELECT id, name FROM product_types")
direction_options = get_options("SELECT id, name FROM directions")
currency_options = get_options("SELECT id, symbol FROM strike_currencies")

# Actions
tabs = st.tabs([
    T["buy_tab"],
    T["rebuy_tab"],
    T["sell_tab"],
    T["partial_sell_tab"],
    T["redemption_tab"],
    T["knockout_tab"]
])


# Buy action
with tabs[0]:
    st.subheader(T["purchase_site"])
    col1, col2 = st.columns(2)
    with col1:
        basis_asset = st.selectbox(T["base_value"], basis_options, format_func=lambda x: x[1],
                                   placeholder=T["base_value"], key="buy_basis_asset")
        type_translations = T.get("type_translations", {})
        product_type = st.selectbox(T["product_type"], type_options, format_func=lambda x: type_translations.get(x[1],x[1]), key="buy_product_type")
        if product_type[1].lower() == "warrant":
            strategy_filtered = ["Call", "Put"]
        else:
            strategy_filtered = ["Long", "Short"]
        strategy = st.selectbox(T["strategy"], strategy_filtered, key="buy_strategy")

    with col2:
        strike = st.number_input(T["strike"], step=1.0, key="buy_strike")
        currency = st.selectbox(T["currency"], currency_options, format_func=lambda x: x[1],
                                placeholder=T["currency"], key="buy_strike_currency")

    col3, col4, col5 = st.columns(3)
    with col3:
        qty = st.number_input(T["quantity"], min_value=1, key="buy_qty")
    with col4:
        price = st.number_input(T["price_per_unit"], min_value=0.0001, key="buy_price")
    with col5:
        fee = st.number_input(T["fee"], value=1.0, key="buy_fee")
    total_price = st.number_input(T["total_price"], value=(price * qty) + fee, key="buy_total_price")
    price_correct = 0 if total_price != ((price * qty) + fee) else 1
    txn_date = st.date_input(T["transaction_date"], value=date.today(), format=date_format, key="buy_transaction_date")

    col6, col7, col8 = st.columns(3)
    with col6:
        wkn = st.text_input("WKN", value="", key="buy_wkn")
    with col7:
        name = st.text_input("Name", value="", key="buy_name")
    with col8:
        if product_type[1].lower() == "warrant":
            expiry_date = st.date_input(T["expiry_date"], format=date_format, key="buy_expiry_date")
        else:
            expiry_date = None

    if st.button(T["save_purchase"]):
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
    st.subheader(T["rebuy_site"])
    choices = get_product_choices()
    if not choices:
        st.info(T["no_existing_product"])
    else:
        selected_id = st.selectbox(T["select_product"], choices, format_func=lambda x: x[1])
        trade_id = selected_id[0]
        product_id = selected_id[3]
        open_qty = selected_id[2]
        st.caption(f"Trade ID: {trade_id}")

        col1, col2, col3 = st.columns(3)
        with col1:
            qty = st.number_input(T["quantity"], min_value=1, key="rebuy_qty")
            st.caption(f"{T['open_qty_col']}: {open_qty}")
        with col2:
            price = st.number_input(T["price_per_unit"], min_value=0.0001, key="rebuy_price")
        with col3:
            fee = st.number_input(T["fee"], value=1.0, key="rebuy_fee")

        total_price = st.number_input(T["total_price"], value=(price * qty) + fee, key="total_price")
        price_correct = 0 if total_price != ((price * qty) + fee) else 1
        txn_date = st.date_input(T["transaction_date"], value=date.today(), key="rebuy_date", format=date_format)

        if st.button(T["save_rebuy"]):
            new_transaction(trade_id=trade_id, date=txn_date, product_id=product_id, price=price, qty=qty,
                            fee=fee, tax=0.0, total_price=total_price, price_correct=price_correct, action_id=3,
                            open_qty=qty, gain=0)
            st.rerun()

# Sell action
with tabs[2]:
    st.subheader(T["sell_site"])
    choices = get_product_choices()

    if not choices:
        st.info(T["no_open_pos"])
    else:
        selected_id = st.selectbox(T["select_position"], choices, format_func=lambda x: x[1])
        trade_id = selected_id[0]
        product_id = selected_id[3]
        open_qty = selected_id[2]
        price_paid = selected_id[4]
        st.caption(f"Trade ID: {trade_id}")


        col1, col2, col3 = st.columns(3)
        with col1:
            qty = st.number_input(T["quantity"], value=open_qty, key="sell_qty", disabled=True)
            st.caption(f"{T['open_qty_col']}: {open_qty}")
        with col2:
            price = st.number_input(T["price_per_unit"], min_value=0.0, key="sell_price")
        with col3:
            fee = st.number_input(T["fee"], value=1.0, key="sell_fee")
        temp = calc_sell_tax(price, qty, price_paid, fee)
        temp_total_price = temp[0]
        tax = temp[1]
        loss_carryforward = temp[2]
        tax_allowance = temp[3]
        col4, col5 = st.columns(2)
        with col4:
            total_price = st.number_input(T["total_price_tax"], value=temp_total_price, key="total_sell_price")
            price_correct = 0 if total_price != ((price * qty) - fee - tax) else 1
            st.caption(f"{T['total_price']}: {price_paid}")
        with col5:
            tax = st.number_input(T["tax"], value=tax, key="sell_tax")
            col6,col7,col8= st.columns(3)
            with col6:
                st.caption(f"{T['loss_carryforward_settings_site']}: {loss_carryforward}")
            with col7:
                st.caption(f"{T['tax_allowance_settings_site']}: {tax_allowance}")
        gain = st.number_input(T["estimated_gain_loss"], value=total_price-price_paid, disabled=True)

        txn_date = st.date_input(T["transaction_date"], value=date.today(), key="sell_date", format=date_format)


        if st.button(T["save_sale"]):
            new_transaction(trade_id=trade_id, date=txn_date, product_id=product_id, price=price, qty=open_qty, fee=fee,
                    tax=tax, total_price=total_price, price_correct=price_correct, action_id=2, open_qty=0, gain=round(gain,2))
            update_open_qty(trade_id, open_qty=0)
            update_loss_carryforward(loss_carryforward)
            update_tax_allowance(tax_allowance)
            st.rerun()

# Parital Sell action
with tabs[3]:
    st.subheader(T["partial_sell_site"])
    choices = get_product_choices()

    if not choices:
        st.info(T["no_open_pos"])
    else:
        selected_id = st.selectbox(T["select_position"], choices, format_func=lambda x: x[1], key="partial_sell_select_position")
        trade_id = selected_id[0]
        product_id = selected_id[3]
        open_qty = selected_id[2]
        price_paid = selected_id[4]
        st.caption(f"Trade ID: {trade_id}")

        col1, col2, col3 = st.columns(3)
        with col1:
            qty = st.number_input(T["quantity"], min_value=0,max_value=open_qty, key="partial_sell_qty")
            st.caption(f"{T['open_qty_col']}: {open_qty}")
        with col2:
            price = st.number_input(T["price_per_unit"], min_value=0.0, key="partial_sell_price")
        with col3:
            fee = st.number_input(T["fee"], value=1.0, key="partial_sell_fee")
        temp = calc_partial_sell_tax(trade_id=trade_id, sell_qty=qty, sell_price=price, fee=fee)
        temp_calc = temp[0]
        total_price = temp_calc["total_price"]
        tax = temp_calc["tax"]
        gain = temp_calc["gain"]
        price_correct = temp_calc["price_correct"]
        loss_carryforward = temp_calc["loss_carryforward"]
        tax_allowance = temp_calc["tax_allowance"]
        col4, col5 = st.columns(2)
        with col4:
            total_price = st.number_input(T["total_price_tax"], value=total_price, key="partial_total_sell_price")
            st.caption(f"{T['total_price']}: {price_paid}")
        with col5:
            tax = st.number_input(T["tax"], value=tax, key="partial_sell_tax")
            col6,col7,col8= st.columns(3)
            with col6:
                st.caption(f"{T['loss_carryforward_settings_site']}: {loss_carryforward}")
            with col7:
                st.caption(f"{T['tax_allowance_settings_site']}: {tax_allowance}")
        gain = st.number_input(T["estimated_gain_loss"], value=gain, disabled=True, key="partial_sell_gain")

        txn_date = st.date_input(T["transaction_date"], value=date.today(), key="partial_sell_date", format=date_format)


        if st.button(T["save_partial_sale"]):
            new_transaction(trade_id=trade_id, date=txn_date, product_id=product_id, price=price, qty=qty, fee=fee,
                    tax=tax, total_price=total_price, price_correct=price_correct, action_id=4, open_qty=None, gain=round(gain,2))

            conn = get_db()
            for txn_id, used_qty in temp[1]:
                res = conn.execute("SELECT open_qty FROM transactions WHERE id = ?", (txn_id,)).fetchone()
                if res is not None:
                    current_qty = res[0]
                    new_qty = max(current_qty - used_qty, 0)
                    conn.execute("UPDATE transactions SET open_qty = ? WHERE id = ?", (new_qty, txn_id))
            update_loss_carryforward(loss_carryforward)
            update_tax_allowance(tax_allowance)
            conn.commit()
            st.rerun()


# redemption action
with tabs[4]:
    st.subheader(T["redemption_site"])
    choices = get_product_choices()

    if not choices:
        st.info(T["no_open_pos"])
    else:
        selected_id = st.selectbox(T["select_position"], choices, format_func=lambda x: x[1],
                                   key="redemption_select_position")
        trade_id = selected_id[0]
        product_id = selected_id[3]
        open_qty = selected_id[2]
        price_paid = selected_id[4]
        st.caption(f"Trade ID: {trade_id}")

        total_price = st.number_input(T["total_price"],key="redemption_price", step=1.0)
        st.caption(f"{T['total_price']}: {price_paid}")

        gain = st.number_input(T["estimated_gain_loss"], value=total_price - price_paid, disabled=True, key="redemption_gain")

        txn_date = st.date_input(T["transaction_date"], value=date.today(), key="redemption_date", format=date_format)

        if st.button(T["save_redemption"]):
            new_transaction(trade_id=trade_id, date=txn_date, product_id=product_id, price=0, qty=0, fee=0,
                            tax=0, total_price=total_price, price_correct=1, action_id=5, open_qty=None,
                            gain=round(gain, 2))
            update_open_qty(trade_id=trade_id, open_qty=0)
            update_loss_carryforward(gain)
            st.rerun()


# knock-out action
with tabs[5]:
    st.subheader(T["ko_site"])
    choices = get_product_choices()

    if not choices:
        st.info(T["no_open_pos"])
    else:
        selected_id = st.selectbox(T["select_position"], choices, format_func=lambda x: x[1],
                                   key="ko_select_position")
        trade_id = selected_id[0]
        product_id = selected_id[3]
        open_qty = selected_id[2]
        price_paid = selected_id[4]
        st.caption(f"{T['total_price']}: {price_paid}")

        gain = st.number_input(T["estimated_gain_loss"], value=-price_paid, disabled=True, key="ko_gain")

        txn_date = st.date_input(T["transaction_date"], value=date.today(), key="ko_date", format=date_format)

        if st.button(T["save_ko"]):
            new_transaction(trade_id=trade_id, date=txn_date, product_id=product_id, price=0, qty=0, fee=0,
                            tax=0, total_price=0, price_correct=1, action_id=6, open_qty=None,
                            gain=round(gain, 2))
            update_open_qty(trade_id=trade_id, open_qty=0)
            update_loss_carryforward(gain)
            st.rerun()


st.divider()

# Show last transactions
st.subheader(T["recent_transactions"])
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
column_names = [T["name_col"], T["price_per_unit"], T["quantity"], T["tax"], T["total_price"],
                T["action_col"], T["open_qty_col"], T["transaction_date"]]

try:
    rows = conn.execute(query).fetchall()
    df = pd.DataFrame(rows, columns=column_names)
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
except Exception as e:
    st.error(f"Error loading data: {e}")
    df = pd.DataFrame()

st.dataframe(df, use_container_width=True)
