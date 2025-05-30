import streamlit as st

import utils.settings_handler as sh
from utils.settings_handler import get_lang, init_settings_db, load_settings, save_settings

st.set_page_config(page_title="OptionsTracker – Settings", layout="wide", page_icon="📥")

init_settings_db()
stored = load_settings()
for key, value in stored.items():
    if key not in st.session_state:
        st.session_state[key] = value

T = get_lang()

st.title(T["title_settings_site"])

# ----- language -----
st.subheader(T["language_section_settings_site"])
LANGUAGES = sh.LANGUAGES
lang_display = st.selectbox(
    "🌍 Language / Sprache",
    list(LANGUAGES.keys()),
    index=list(LANGUAGES.values()).index(st.session_state.language_code),
    key="language_settings_site"
)
st.session_state.language_code = LANGUAGES[lang_display]

# ----- tax -----
st.subheader(T["tax_section_settings_site"])
default_tax = st.session_state.get("tax_rate", 0.0)
new_tax = st.number_input(T["tax_rate_settings_site"], min_value=0.0000, max_value=1.0000, value=default_tax, step=0.0001, format="%.4f")
st.caption(f"{T['default_tax_caption']}{default_tax}")
st.session_state.tax_rate = new_tax

# ----- date format -----
st.subheader(T["date_section_settings_site"])

date_formats = {
    "DD.MM.YYYY": "DD.MM.YYYY",
    "YYYY-MM-DD": "YYYY-MM-DD",
    "MM/DD/YYYY": "MM/DD/YYYY"
}

# Aktuelles Format aus session_state oder Default
current_format = st.session_state.get("date_format", "DD.MM.YYYY")

# Versuche, das Label (Key) für das aktuelle Format zu finden
matches = [k for k, v in date_formats.items() if v == current_format]
date_label = matches[0] if matches else "DD.MM.YYYY"

# Auswahl anzeigen
new_date_label = st.selectbox(
    T["choose_date_format"],
    list(date_formats.keys()),
    index=list(date_formats.keys()).index(date_label)
)

# Neues Format speichern
st.session_state.date_format = date_formats[new_date_label]


# ----- Speichern -----
if st.button(T["save_settings"]):
    save_settings({
        "language_code": st.session_state.language_code,
        "tax_rate": st.session_state.tax_rate,
        "date_format": st.session_state.date_format
    })
    st.rerun()
