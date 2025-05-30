import streamlit as st
import pandas as pd

from utils.db_helper import get_db
from utils.settings_handler import get_lang

st.set_page_config(page_title="OptionsTracker – Tables", layout="wide", page_icon="📋")

T = get_lang()

st.title(T["title_table_site"])

conn = get_db()

st.subheader(T["select_table"])
col1, col2 = st.columns([3, 1])
with col1:
    tab = st.selectbox(T["choose_table"], [T["transactions_table"], T["products_table"]])
with col2:
    limit = st.selectbox(T["rows"], [10, 25, 50, 100], index=1)

column_names = []
if tab == T["products_table"]:
    st.subheader(T["products_table"])
    query = """
        SELECT bp.name,
               pt.name,
               d.name,
               CAST(p.strike AS TEXT) || sc.symbol,
               p.wkn,
               p.expiry_date
        FROM products p
        JOIN basis_products bp ON p.basis_product_id = bp.id
        JOIN product_types pt ON p.product_type_id = pt.id
        JOIN directions d ON p.direction_id = d.id
        JOIN strike_currencies sc ON p.strike_currency_id = sc.id
        LIMIT ?
    """
    column_names = T["table_columns_products"]
else:
    st.subheader(T["transactions_table"])
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
        LIMIT ?
    """
    column_names = T["table_columns_transactions"]

try:
    rows = conn.execute(query, (limit,)).fetchall()
    df = pd.DataFrame(rows, columns=column_names)
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
except Exception as e:
    st.error(f"{T['error_loading']} {e}")
    df = pd.DataFrame()

st.dataframe(df, use_container_width=True)
