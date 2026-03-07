import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import re

# --- KONFIGURACJA ---
# Lista słów sugerujących automatycznie "Koszt"
SLOWA_KOSZTY = [
    'paliwo', 'obiad', 'jedzenie', 'zakupy', 'zus', 'podatek', 'czynsz', 
    'prąd', 'gaz', 'internet', 'telefon', 'naprawa', 'serwis', 'sklep', 
    'lena', 'lidl', 'castorama', 'orlen', 'części', 'opłata', 'rata',
    'hobby', 'amunicja', 'sport'  # Twoje nowe słowa
]

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
@st.cache_data(ttl=5)
def get_data():
    try:
        response = requests.get(st.secrets["script_url"])
        if response.status_code == 200:
            df = pd.DataFrame(response.json())
            if not df.empty:
                # Konwersja i czyszczenie danych
                df['kwota'] = pd.to_numeric(df['kwota'], errors='coerce').fillna(0)
                df['miesiac'] = df['miesiac'].astype(str).str.split('.').str[0].str.strip()
                df['rok'] = df['rok'].astype(str).str.split('.').str[0].str.strip()
            return df
    except:
        pass
    return pd.DataFrame()

# --- APLIKACJA ---
st.title("💰 Księgowość Głosowa AI")

# Pole tekstowe do wprowadzania danych
raw_text = st.text_input("Dyktuj (np. 150 amunicja trening):", key="raw_text_input")

# Logika zgadywania typu (Przychód = 0, Koszt = 1)
default_index = 0
if any(word in raw_text.lower() for word in SLOWA_KOSZTY):
    default_index = 1

# --- FORMULARZ DODAWANIA ---
with st.form("add_form", clear_on_submit=True):
    typ = st.selectbox("Typ wpisu:", ["Przychód", "Koszt"], index=default_index)
    
    if st.form_submit_button("ZAPISZ DO ARKUSZA", use_container_width=True):
        match = re.search(r'(\d+[.,]?\d*)', raw_text)
        if match:
            kwota = float(match.group(1).replace(",", "."))
            opis = raw_text.replace(match.group(1), "").strip()
            now = datetime.now()
            
            payload = {
                "token": st.secrets["api_token"],
                "data": now.strftime("%Y-%m-%d %H:%M"),
                "typ": typ,
                "kwota": kwota,
                "opis": opis,
                "dokument": "Faktura" if "faktura" in raw_text.lower() else "Paragon",
                "miesiac": str(now.month),
                "rok": str(now.year)
            }
            
            res = requests.post(st.secrets["script_url"], json=payload)
            if res.text == "Zapisano pomyślnie":
                st.toast(f"Dodano {typ}: {kwota} zł", icon="✅")
                st.cache_data.clear()
                st.rerun()
        else:
            st.error("Nie znalazłem kwoty w tekście!")

# --- STATYSTYKI I TABELA ---
df = get_data()

if not df.empty:
    st.divider()
    m_now, r_now = str(datetime.now().month), str(datetime.now().year)

    # Obliczenia sumaryczne
    p_m = df[(df['typ'] == 'Przychód') & (df['miesiac'] == m_now)]['kwota'].sum()
    k_m = df[(df['typ'] == 'Koszt') & (df['miesiac'] == m_now)]['kwota'].sum()
    p_r = df[(df['typ'] == 'Przychód') & (df['rok'] == r_now)]['kwota'].sum()

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Przychód (Miesiąc)", f"{p_m:,.2f} zł")
    col_b.metric("Koszty (Miesiąc)", f"{k_m:,.2f} zł")
    col_c.metric("Przychód (Rok)", f"{p_r:,.2f} zł")

    with st.expander("📝 Historia wpisów (od najnowszych)"):
        # Wyświetlamy historię w odwrotnej kolejności
        st.dataframe(df.iloc[::-1], use_container_width=True)
        if st.button("🔄 Odśwież widok"):
            st.cache_data.clear()
            st.rerun()
else:
    st.info("Dodaj pierwszy wpis, aby zobaczyć statystyki.")
