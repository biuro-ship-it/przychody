import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import re

# --- KONFIGURACJA BAZY DANYCH ---
def init_db():
    conn = sqlite3.connect('finanse.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS przychody 
                 (id INTEGER PRIMARY KEY, data TEXT, kwota REAL, opis TEXT, miesiac TEXT)''')
    conn.commit()
    conn.close()

def add_to_db(kwota, opis):
    now = datetime.now()
    miesiac_rok = now.strftime("%Y-%m") # Format: 2024-04
    data_full = now.strftime("%Y-%m-%d %H:%M")
    
    conn = sqlite3.connect('finanse.db')
    c = conn.cursor()
    c.execute("INSERT INTO przychody (data, kwota, opis, miesiac) VALUES (?, ?, ?, ?)",
              (data_full, kwota, opis, miesiac_rok))
    conn.commit()
    conn.close()

# --- LOGIKA APLIKACJI ---
st.set_page_config(page_title="Mój Portfel", page_icon="💰")
init_db()

st.title("💰 Asystent Przychodów")

# Instrukcja dla użytkownika
st.markdown("""
<small>Kliknij w pole poniżej, użyj **mikrofonu na klawiaturze** i powiedz np.: 
"623 zł sprzedaż rano"</small>
""", unsafe_allow_html=True)

# Pole wejściowe
user_input = st.text_input("Co dopisać?", key="input", placeholder="Powiedz lub wpisz...")

if st.button("➕ Zapisz przychód", use_container_width=True):
    if user_input:
        # Wyciąganie liczby z tekstu
        match = re.search(r'(\d+[\d\s,.]*)', user_input)
        if match:
            kwota_str = match.group(1).replace(" ", "").replace(",", ".")
            try:
                kwota = float(kwota_str)
                opis = user_input.replace(match.group(1), "").strip()
                add_to_db(kwota, opis)
                st.success(f"✅ Dodano: {kwota} zł ({opis})")
            except ValueError:
                st.error("Nie udało się rozpoznać kwoty.")
        else:
            st.error("Nie znalazłem żadnej liczby w Twojej wypowiedzi.")

# --- WYŚWIETLANIE DANYCH ---
st.divider()
conn = sqlite3.connect('finanse.db')
df = pd.read_sql_query("SELECT * FROM przychody ORDER BY data DESC", conn)
conn.close()

if not df.empty:
    st.subheader("📊 Podsumowanie Miesięczne")
    # Grupowanie i ładne formatowanie
    summary = df.groupby('miesiac')['kwota'].sum().reset_index()
    summary.columns = ['Miesiąc', 'Suma (zł)']
    st.table(summary)

    with st.expander("📝 Ostatnie wpisy"):
        st.dataframe(df[['data', 'kwota', 'opis']], use_container_width=True)
else:
    st.info("Baza jest pusta. Dodaj pierwszy przychód!")
