import streamlit as st

from utils.db_helper import get_db

st.set_page_config(page_title="OptionsTracker – Master Data", layout="wide", page_icon="📊")
st.title("⚙️ Manage Master Data")

conn = get_db()

tabs = st.tabs([
    "Underlying Assets",
    "Product Types",
    "Strategies",
    "Strike Currencies"
])

# === Tab 1: Underlying Assets ===
with tabs[0]:
    st.subheader("📌 Underlying Assets")
    new_basis = st.text_input("Add a new underlying asset")
    if st.button("Add", key="add_basis"):
        if new_basis.strip():
            conn.execute("INSERT INTO basis_products (name) VALUES (?)", (new_basis.strip(),))
            conn.commit()
            st.success(f"'{new_basis}' has been added.")
        else:
            st.warning("Please enter a valid name.")

    rows = conn.execute("SELECT name FROM basis_products ORDER BY id").fetchall()
    st.table(rows)

# === Tab 2: Product Types ===
with tabs[1]:
    st.subheader("📦 Product Types")
    rows = conn.execute("SELECT name FROM product_types ORDER BY id").fetchall()
    st.table(rows)

# === Tab 3: Strategies ===
with tabs[2]:
    st.subheader("🎯 Strategies")
    rows = conn.execute("SELECT name FROM directions ORDER BY id").fetchall()
    st.table(rows)

# === Tab 4: Strike Currencies ===
with tabs[3]:
    st.subheader("💱 Strike Currencies")
    new_currency = st.text_input("Add a new currency")
    if st.button("Add", key="add_currency"):
        if new_currency.strip():
            conn.execute("INSERT INTO strike_currencies (symbol) VALUES (?)", (new_currency.strip(),))
            conn.commit()
            st.success(f"'{new_currency}' has been added.")
        else:
            st.warning("Please enter a valid currency.")

    rows = conn.execute("SELECT symbol FROM strike_currencies ORDER BY id").fetchall()
    st.table(rows)
