import streamlit as st
from utils.settings_handler import load_settings

if "settings_loaded" not in st.session_state:
    stored = load_settings()
    for key, value in stored.items():
        if key not in st.session_state:
            st.session_state[key] = value
    st.session_state.settings_loaded = True


