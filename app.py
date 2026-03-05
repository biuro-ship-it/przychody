import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import re

# --- KONFIGURACJA BAZY ---
def init_db():
    conn = sqlite3.connect('finanse_pro.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS transakcje 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  data TEXT, 
                  typ_transakcji TEXT, 
                  kwota REAL, 
                  opis TEXT, 
                  dokument TEXT, 
                  miesiac TEXT, 
                  rok TEXT)''')
    conn.commit()
    conn.close()

def add_transakcja(typ, kwota, opis, dokument):
    now = datetime.now()
    conn = sqlite3.connect('finanse_pro.db')
    c = conn.cursor()
    c.execute("INSERT INTO transakcje (data, typ_transakcji, kwota, opis, dokument, miesiac, rok) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (now.strftime("%Y-%m-%d %H:%M"), typ, kwota, opis, dokument, now.strftime("%m"), now.strftime("%Y")))
    conn.commit()
    conn.close()

def delete_transakcja(id_trans):
    conn = sqlite3.connect('finanse_pro.db')
    c = conn.cursor()
    c.execute("DELETE FROM transakcje WHERE id=?", (id_trans,))
    conn.commit()
    conn.close()

# --- LOGIKA PARSOWANIA GŁOSU ---
def parse_input(text):
    kwota = 0
    dokument = "Paragon"
    if "faktura" in text.lower(): dokument = "Faktura"
    
    match = re.search(r'(\d+[\d\s,.]*)', text)
    if match:
        kwota = float(match.group(1).replace(" ", "").replace(",", "."))
        opis = text.replace(match.group(1), "").replace("faktura", "").replace("paragon", "").strip()
        return kwota, opis, dokument
    return None, None, None

# --- UI ---
st.set_page_config(page_title="Finanse Pro", layout="wide")
init_db()

st.title("📊 Zarządzanie Przychodami i Kosztami")

# --- PANEL DODAWANIA ---
with st.expander("➕ Dodaj nowy wpis (Głosowo lub Tekstowo)", expanded=True):
    col1, col2 = st.columns([3, 1])
    with col1:
        raw_text = st.text_input("Powiedz np. '623 sprzedaż rano faktura' lub '50 paliwo paragon'")
    with col2:
        typ = st.selectbox("Typ", ["Przychód", "Koszt"])
    
    if st.button("Zapisz", use_container_width=True):
        k, o, d = parse_input(raw_text)
        if k:
            add_transakcja(typ, k, o, d)
            st.success(f"Dodano {typ}: {k} zł")
            st.rerun()

# --- POBIERANIE DANYCH ---
conn = sqlite3.connect('finanse_pro.db')
df = pd.read_sql_query("SELECT * FROM transakcje", conn)
conn.close()

# --- STATYSTYKI ---
if not df.empty:
    st.divider()
    m_now = datetime.now().strftime("%m")
    r_now = datetime.now().strftime("%Y")
    
    col_a, col_b, col_c = st.columns(3)
    
    przychody_m = df[(df['typ_transakcji'] == 'Przychód') & (df['miesiac'] == m_now)]['kwota'].sum()
    koszty_m = df[(df['typ_transakcji'] == 'Koszt') & (df['miesiac'] == m_now)]['kwota'].sum()
    przychody_r = df[(df['typ_transakcji'] == 'Przychód') & (df['rok'] == r_now)]['kwota'].sum()
    
    col_a.metric("Przychody (Miesiąc)", f"{przychody_m:,.2f} zł")
    col_b.metric("Koszty (Miesiąc)", f"{koszty_m:,.2f} zł")
    col_c.metric("Przychody (Rok)", f"{przychody_r:,.2f} zł")

    # --- LISTA I EDYCJA ---
    st.subheader("📝 Lista operacji")
    
    # Wyświetlamy tabelę z możliwością edycji
    edited_df = st.data_editor(df[['id', 'data', 'typ_transakcji', 'kwota', 'opis', 'dokument']], 
                               num_rows="dynamic", key="editor", use_container_width=True)
    
    if st.button("🗑️ Usuń wybrane (wpisz ID)"):
        id_to_del = st.number_input("Podaj ID do usunięcia", step=1)
        if st.button("Potwierdź usunięcie"):
            delete_transakcja(id_to_del)
            st.rerun()

    # --- EKSPORT ---
    st.divider()
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 Pobierz kopię do Excel (CSV)", data=csv, file_name=f"finanse_{datetime.now().strftime('%Y%m%d')}.csv")

else:
    st.info("Brak danych. Zacznij od dodania pierwszej transakcji!")
