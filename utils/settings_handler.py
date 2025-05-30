from utils.db_helper import get_db
import importlib
import streamlit as st

LANGUAGES = {
        "English": "en",
        "Deutsch": "de"
    }


def get_lang():

    if "language_code" not in st.session_state:
        st.session_state.language_code = "en"


    lang_display = st.sidebar.selectbox("🌍 Language / Sprache", list(LANGUAGES.keys()),
                                      index=list(LANGUAGES.values()).index(st.session_state.language_code))
    st.session_state.language_code = LANGUAGES[lang_display]

    lang_module = importlib.import_module(f"lang.{st.session_state.language_code}")
    return lang_module.translations


def init_settings_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            user_id TEXT PRIMARY KEY,
            language_code TEXT DEFAULT 'de',
            tax_rate REAL DEFAULT 0.0,
            date_format TEXT DEFAULT '%d.%m.%Y'
        )
    """)
    conn.commit()
    conn.close()


def load_settings(user_id="default"):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT language_code, tax_rate, date_format FROM settings WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "language_code": row[0],
            "tax_rate": row[1],
            "date_format": row[2]
        }
    else:
        save_settings({"language_code": "en", "tax_rate": 0.0, "date_format": "%d.%m.%Y"}, user_id)
        return load_settings(user_id)


def save_settings(settings, user_id="default"):
    conn = get_db()
    conn.execute("""
        INSERT INTO settings (user_id, language_code, tax_rate, date_format)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            language_code=excluded.language_code,
            tax_rate=excluded.tax_rate,
            date_format=excluded.date_format
    """, (user_id, settings["language_code"], settings["tax_rate"], settings["date_format"]))
    conn.commit()
    conn.close()

if __name__=="__main__":
    init_settings_db()