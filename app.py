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

# --- FUNKCJA POBIERANIA DANYCH ---
@st.cache_data(ttl=10) # Odświeżaj co 10 sekund
def get_data():
    try:
        response = requests.get(st.secrets["script_url"])
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data)
            if not df.empty:
                # CZYSZCZENIE DANYCH:
                # 1. Kwota na liczbę
                df['kwota'] = pd.to_numeric(df['kwota'], errors='coerce').fillna(0)
                # 2. Miesiąc i Rok na tekst bez ".0" (np. "3.0" -> "3")
                df['miesiac'] = df['miesiac'].astype(str).str.split('.').str[0].str.strip()
                df['rok'] = df['rok'].astype(str).str.split('.').str[0].str.strip()
            return df
    except Exception as e:
        st.error(f"Błąd pobierania: {e}")
    return pd.DataFrame()

# --- APLIKACJA ---
st.title("💰 Księgowość Głosowa PRO")

# 1. FORMULARZ DODAWANIA
with st.form("add_form", clear_on_submit=True):
    col1, col2 = st.columns([3, 1])
    with col1:
        raw_text = st.text_input("Dyktuj (np. 623 sprzedaż ranek faktura):")
    with col2:
        typ = st.selectbox("Typ", ["Przychód", "Koszt"])
    
    if st.form_submit_button("ZAPISZ DO ARKUSZA"):
        match = re.search(r'(\d+[.,]?\d*)', raw_text)
        if match:
            kwota = float(match.group(1).replace(",", "."))
            now = datetime.now()
            payload = {
                "token": st.secrets["api_token"],
                "data": now.strftime("%Y-%m-%d %H:%M"),
                "typ": typ,
                "kwota": kwota,
                "opis": raw_text.replace(match.group(1), "").strip(),
                "dokument": "Faktura" if "faktura" in raw_text.lower() else "Paragon",
                "miesiac": str(now.month), # Zapisuje "3" zamiast "03"
                "rok": str(now.year)
            }
            res = requests.post(st.secrets["script_url"], json=payload)
            if res.text == "Zapisano pomyślnie":
                st.toast("Zapisano!", icon="✅")
                st.cache_data.clear()
                st.rerun()

# 2. STATYSTYKI
df = get_data()

if not df.empty:
    st.divider()
    
    # Pobieramy aktualny miesiąc i rok jako tekst (np. "3", "2026")
    m_now = str(datetime.now().month)
    r_now = str(datetime.now().year)

    # Filtrowanie
    przychody_m = df[(df['typ'] == 'Przychód') & (df['miesiac'] == m_now)]['kwota'].sum()
    koszty_m = df[(df['typ'] == 'Koszt') & (df['miesiac'] == m_now)]['kwota'].sum()
    przychody_r = df[(df['typ'] == 'Przychód') & (df['rok'] == r_now)]['kwota'].sum()

    # Wyświetlanie metryk
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Przychód (Miesiąc)", f"{przychody_m:,.2f} zł")
    col_b.metric("Koszty (Miesiąc)", f"{koszty_m:,.2f} zł")
    col_c.metric("Przychód (Rok)", f"{przychody_r:,.2f} zł")

    st.subheader("📝 Ostatnie wpisy")
    st.dataframe(df.tail(10), use_container_width=True)
    
    if st.button("🔄 Odśwież dane"):
        st.cache_data.clear()
        st.rerun()
else:
    st.info("Baza jest pusta lub ładuje dane...")
