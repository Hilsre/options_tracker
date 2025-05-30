import streamlit as st

from utils.db_helper import get_db
from utils.settings_handler import get_lang

st.set_page_config(page_title="OptionsTracker – Master Data", layout="wide", page_icon="💾")

T = get_lang()

st.title(T["title_options_site"])

conn = get_db()

tabs = st.tabs(T["tabs_master"])

# === Tab 1: Underlying Assets ===
with tabs[0]:
    st.subheader(T["underlying_assets"])
    new_basis = st.text_input(T["add_underlying"])
    if st.button(T["add_button"], key="add_basis"):
        if new_basis.strip():
            conn.execute("INSERT INTO basis_products (name) VALUES (?)", (new_basis.strip(),))
            conn.commit()
            st.success(f"'{new_basis}'{T['added_successfully']}")
        else:
            st.warning(T["input_warning"])

    rows = conn.execute("SELECT name FROM basis_products ORDER BY id").fetchall()
    st.table(rows)

# === Tab 2: Product Types ===
with tabs[1]:
    st.subheader(T["product_types"])
    rows = conn.execute("SELECT name FROM product_types ORDER BY id").fetchall()
    st.table(rows)

# === Tab 3: Strategies ===
with tabs[2]:
    st.subheader(T["strategies"])
    rows = conn.execute("SELECT name FROM directions ORDER BY id").fetchall()
    st.table(rows)

# === Tab 4: Strike Currencies ===
with tabs[3]:
    st.subheader(T["strike_currencies"])
    new_currency = st.text_input(T["add_currency"])
    if st.button(T["add_button"], key="add_currency"):
        if new_currency.strip():
            conn.execute("INSERT INTO strike_currencies (symbol) VALUES (?)", (new_currency.strip(),))
            conn.commit()
            st.success(f"'{new_currency}'{T['added_successfully']}")
        else:
            st.warning(T["input_warning"])

    rows = conn.execute("SELECT symbol FROM strike_currencies ORDER BY id").fetchall()
    st.table(rows)
