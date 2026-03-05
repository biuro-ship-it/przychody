import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import re

# --- KONFIGURACJA BAZY ---
DB_NAME = 'finanse_pro.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
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
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO transakcje (data, typ_transakcji, kwota, opis, dokument, miesiac, rok) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (now.strftime("%Y-%m-%d %H:%M"), typ, kwota, opis, dokument, now.strftime("%m"), now.strftime("%Y")))
    conn.commit()
    conn.close()

def run_query(query, params=()):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    conn.close()

# --- LOGIKA PARSOWANIA GŁOSU ---
def parse_input(text):
    kwota = 0
    dokument = "Paragon"
    text_lower = text.lower()
    if "faktura" in text_lower: dokument = "Faktura"
    
    match = re.search(r'(\d+[.,]?\d*)', text)
    if match:
        kwota_str = match.group(1).replace(",", ".")
        kwota = float(kwota_str)
        opis = text.replace(match.group(1), "").replace("faktura", "").replace("paragon", "").strip()
        return kwota, opis, dokument
    return None, None, None

# --- UI ---
st.set_page_config(page_title="Finanse Pro", layout="wide")
init_db()

st.title("📊 Moja Księgowość Głosowa")

# --- PANEL DODAWANIA ---
st.subheader("➕ Nowy wpis")
col1, col2, col3 = st.columns([3, 1, 1])

with col1:
    raw_text = st.text_input("Powiedz/Wpisz:", placeholder="np. 200 paliwo faktura", key="voice_input")
with col2:
    typ_input = st.selectbox("Typ", ["Przychód", "Koszt"])
with col3:
    st.write(" ")
    if st.button("Zapisz wpis", use_container_width=True):
        if raw_text:
            k, o, d = parse_input(raw_text)
            if k is not None:
                add_transakcja(typ_input, k, o, d)
                st.success(f"Dodano: {k} zł")
                st.rerun()
            else:
                st.error("Brak kwoty!")

# --- POBIERANIE DANYCH ---
conn = sqlite3.connect(DB_NAME)
df = pd.read_sql_query("SELECT * FROM transakcje", conn)
conn.close()

if not df.empty:
    # --- STATYSTYKI ---
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

    # --- EDYCJA ---
    st.subheader("📝 Edycja i Zarządzanie")
    
    # Wyświetlamy tabelę (id jako pierwsza kolumna - LP)
    edited_df = st.data_editor(
        df[['id', 'data', 'typ_transakcji', 'kwota', 'opis', 'dokument']], 
        key="data_editor", 
        num_rows="dynamic", 
        use_container_width=True,
        column_config={"id": st.column_config.Column("ID / Lp", disabled=True)}
    )

    # --- PRZYCISKI AKCJI ---
    st.write("### Akcje na bazie danych:")
    col_del, col_save = st.columns(2)

    with col_del:
        st.write("🗑️ Usuwanie")
        id_to_delete = st.number_input("Wpisz ID do usunięcia:", step=1, value=0)
        if st.button("USUŃ REKORD", type="secondary", use_container_width=True):
            if id_to_delete in df['id'].values:
                run_query("DELETE FROM transakcje WHERE id = ?", (int(id_to_delete),))
                st.success(f"Usunięto rekord o ID {id_to_delete}")
                st.rerun()
            else:
                st.error("Nie znaleziono takiego ID!")

    with col_save:
        st.write("💾 Zmiany w treści")
        st.write("Zmieniłeś kwotę lub opis w tabeli wyżej?")
        if st.button("ZAPISZ ZMIANY W TABELI", type="primary", use_container_width=True):
            for index, row in edited_df.iterrows():
                run_query('''UPDATE transakcje SET 
                             typ_transakcji = ?, kwota = ?, opis = ?, dokument = ? 
                             WHERE id = ?''', 
                          (row['typ_transakcji'], row['kwota'], row['opis'], row['dokument'], row['id']))
            st.success("Zmiany zapisane!")
            st.rerun()

    # --- EKSPORT ---
    st.divider()
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 Pobierz kopię do Excel (CSV)", data=csv, file_name=f"raport_{datetime.now().strftime('%Y%m')}.csv", use_container_width=True)
else:
    st.info("Baza danych jest pusta.")
