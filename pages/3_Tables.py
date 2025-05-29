import streamlit as st
import pandas as pd

from utils.db_helper import get_db

st.set_page_config(page_title="OptionsTracker – Tables", layout="wide", page_icon="📋")
st.title("📋 Show Data")

conn = get_db()

st.subheader("📂 Select Table")
col1, col2 = st.columns([3, 1])
with col1:
    tab = st.selectbox("Choose table", ["Transactions", "Products"])
with col2:
    limit = st.selectbox("Rows", [10, 25, 50, 100], index=1)

column_names = []
if tab == "Products":
    st.subheader("💼 Products Table")
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
    column_names = ["Underlying Asset", "Product Type", "Strategy", "Strike", "WKN", "Expiry Date"]
else:
    st.subheader("💳 Transactions Table")
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
    column_names = ["Name", "Price", "Quantity", "Tax", "Total", "Action", "Open Quantity", "Date"]

try:
    rows = conn.execute(query, (limit,)).fetchall()
    df = pd.DataFrame(rows, columns=column_names)
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
except Exception as e:
    st.error(f"Error loading data: {e}")
    df = pd.DataFrame()

st.dataframe(df, use_container_width=True)
