from utils.db_helper import get_db
import importlib
import streamlit as st

LANGUAGES = {
        "English": "en",
        "Deutsch": "de"
    }

THEME = {
    "Dark": "Dark",
    "Light": "Light"
}


def get_lang():

    if "language_code" not in st.session_state:
        st.session_state.language_code = "en"


    lang_display = st.sidebar.selectbox("🌍 Language / Sprache", list(LANGUAGES.keys()),
                                      index=list(LANGUAGES.values()).index(st.session_state.language_code))
    st.session_state.language_code = LANGUAGES[lang_display]

    lang_module = importlib.import_module(f"lang.{st.session_state.language_code}")
    return lang_module.translations

def get_theme_mode():
    if "theme_mode" not in st.session_state:
        st.session_state.theme_mode = "dark"

    theme_mode_display = st.sidebar.radio("🖼 Theme: ", list(THEME.keys()),
                                          index=list(THEME.values()).index(st.session_state.theme_mode))
    st.session_state.theme_mode = THEME[theme_mode_display]

def init_settings_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            user_id TEXT PRIMARY KEY,
            language_code TEXT DEFAULT 'de',
            tax_rate REAL DEFAULT 0.0,
            date_format TEXT DEFAULT '%d.%m.%Y',
            tax_allowance REAL DEFAULT 0.0,
            loss_carryforward REAL DEFAULT 0.0
        )
    """)
    conn.commit()
    conn.close()


def load_settings(user_id="default"):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT language_code, tax_rate, date_format, tax_allowance, loss_carryforward, theme_mode FROM settings WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "language_code": row[0],
            "tax_rate": row[1],
            "date_format": row[2],
            "tax_allowance": row[3],
            "loss_carryforward": row[4],
            "theme_mode": row[5]
        }
    else:
        save_settings({"language_code": "en", "tax_rate": 0.0, "date_format": "%d.%m.%Y", "tax_allowance": 0.0, "loss_carryforward": 0.0, "theme_mode":"Dark"}, user_id)
        return load_settings(user_id)


def save_settings(settings, user_id="default"):
    conn = get_db()
    conn.execute("""
        INSERT INTO settings (user_id, language_code, tax_rate, date_format, tax_allowance, loss_carryforward, theme_mode)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            language_code=excluded.language_code,
            tax_rate=excluded.tax_rate,
            date_format=excluded.date_format,
            tax_allowance=excluded.tax_allowance,
            loss_carryforward=excluded.loss_carryforward,
            theme_mode=excluded.theme_mode
    """, (user_id, settings["language_code"], settings["tax_rate"], settings["date_format"], settings["tax_allowance"],
          settings["loss_carryforward"], settings["theme_mode"]))
    conn.commit()
    conn.close()

if __name__=="__main__":
    if "theme_mode" not in st.session_state:
        st.session_state.theme_mode = "Dark"