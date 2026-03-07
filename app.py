import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import re

# --- LOGOWANIE ---
if "password_correct" not in st.session_state:
    st.title("🔒 Logowanie")
    pwd = st.text_input("Hasło:", type="password")
    if st.button("Zaloguj"):
        if pwd == st.secrets["password"]:
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("Błąd!")
    st.stop()

# --- APLIKACJA ---
st.title("💰 Księgowość Głosowa (Apps Script)")

with st.form("add_form", clear_on_submit=True):
    col1, col2 = st.columns([3, 1])
    with col1:
        raw_text = st.text_input("Dyktuj/Wpisz:")
    with col2:
        typ = st.selectbox("Typ", ["Przychód", "Koszt"])
    
    if st.form_submit_button("ZAPISZ DO ARKUSZA"):
        match = re.search(r'(\d+[.,]?\d*)', raw_text)
        if match:
            kwota = float(match.group(1).replace(",", "."))
            now = datetime.now()
            
            # Dane do wysłania
            payload = {
                "token": st.secrets["api_token"],
                "data": now.strftime("%Y-%m-%d %H:%M"),
                "typ": typ,
                "kwota": kwota,
                "opis": raw_text.replace(match.group(1), "").strip(),
                "dokument": "Faktura" if "faktura" in raw_text.lower() else "Paragon",
                "miesiac": now.strftime("%m"),
                "rok": now.strftime("%Y")
            }
            
            # Wysyłka do Google Apps Script
            response = requests.post(st.secrets["script_url"], json=payload)
            
            if response.text == "Zapisano pomyślnie":
                st.success("✅ Dane bezpiecznie wysłane do Arkusza Google!")
            else:
                st.error(f"Błąd: {response.text}")
