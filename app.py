import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import re

# --- LOGOWANIE ---
def check_password():
    if "password_correct" not in st.session_state:
        st.title("🔒 Dostęp chroniony")
        pwd = st.text_input("Podaj hasło:", type="password")
        if st.button("Zaloguj"):
            if pwd == st.secrets["password"]:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("Błędne hasło!")
        return False
    return True

if check_password():
    # --- START APLIKACJI ---
    DB_NAME = 'finanse_pro.db'
    
    def init_db():
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS transakcje 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, typ_transakcji TEXT, 
                      kwota REAL, opis TEXT, dokument TEXT, miesiac TEXT, rok TEXT)''')
        conn.commit()
        conn.close()

    def run_query(query, params=()):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute(query, params)
        conn.commit()
        conn.close()

    def parse_input(text):
        kwota = 0
        dokument = "Paragon"
        if "faktura" in text.lower(): dokument = "Faktura"
        match = re.search(r'(\d+[.,]?\d*)', text)
        if match:
            kwota = float(match.group(1).replace(",", "."))
            opis = text.replace(match.group(1), "").replace("faktura", "").replace("paragon", "").strip()
            return kwota, opis, dokument
        return None, None, None

    init_db()
    st.title("📊 Moja Księgowość Głosowa")
    
    if st.sidebar.button("Wyloguj"):
        del st.session_state["password_correct"]
        st.rerun()

    # --- PANEL DODAWANIA (Z POPRAWKĄ CZYSZCZENIA) ---
    st.subheader("➕ Nowy wpis")
    
    # Tworzymy formularz, który ułatwia czyszczenie pól
    with st.form("my_form", clear_on_submit=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            raw_text = st.text_input("Powiedz/Wpisz (np. 100 obiady):", key="voice_input")
        with col2:
            typ_input = st.selectbox("Typ", ["Przychód", "Koszt"])
        
        submitted = st.form_submit_button("ZAPISZ WPIS", use_container_width=True)
        
        if submitted and raw_text:
            k, o, d = parse_input(raw_text)
            if k:
                now = datetime.now()
                run_query("INSERT INTO transakcje (data, typ_transakcji, kwota, opis, dokument, miesiac, rok) VALUES (?,?,?,?,?,?,?)",
                          (now.strftime("%Y-%m-%d %H:%M"), typ_input, k, o, d, now.strftime("%m"), now.strftime("%Y")))
                st.toast(f"Dodano: {k} zł", icon='✅')
                # Formularz sam wyczyści pole dzięki 'clear_on_submit=True'
            else:
                st.error("Nie znalazłem kwoty!")

    # --- DANE I STATYSTYKI ---
    # (Pobieranie danych do tabeli)
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM transakcje", conn)
    conn.close()

    if not df.empty:
        st.divider()
        m_now, r_now = datetime.now().strftime("%m"), datetime.now().strftime("%Y")
        
        # Szybkie filtry dla statystyk
        p_m = df[(df['typ_transakcji'] == 'Przychód') & (df['miesiac'] == m_now)]['kwota'].sum()
        k_m = df[(df['typ_transakcji'] == 'Koszt') & (df['miesiac'] == m_now)]['kwota'].sum()
        
        col_a, col_b = st.columns(2)
        col_a.metric("Przychody (Miesiąc)", f"{p_m:,.2f} zł")
        col_b.metric("Koszty (Miesiąc)", f"{k_m:,.2f} zł")

        # TABELA I EDYCJA
        st.subheader("📝 Zarządzanie")
        edited_df = st.data_editor(df, key="editor", use_container_width=True, 
                                   column_config={"id": st.column_config.Column(disabled=True)})
        
        c1, c2 = st.columns(2)
        with c1:
            id_del = st.number_input("ID do usunięcia:", step=1, value=0)
            if st.button("USUŃ REKORD"):
                run_query("DELETE FROM transakcje WHERE id = ?", (int(id_del),))
                st.rerun()
        with c2:
            st.write(" ")
            if st.button("ZAPISZ ZMIANY W TABELI"):
                for _, row in edited_df.iterrows():
                    run_query("UPDATE transakcje SET typ_transakcji=?, kwota=?, opis=?, dokument=? WHERE id=?", 
                              (row['typ_transakcji'], row['kwota'], row['opis'], row['dokument'], row['id']))
                st.success("Zapisano zmiany!")
                st.rerun()
        
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Eksportuj CSV", csv, f"raport.csv", use_container_width=True)
    else:
        st.info("Baza jest pusta.")
