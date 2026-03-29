import streamlit as st
import random
import time
import pandas as pd
import os

# --- KONFIGURACJA PLIKU WYNIKÓW ---
SCORES_FILE = "wyniki_mastermind.csv"

# --- FUNKCJE POMOCNICZE ---
def format_time_pl(seconds):
    minutes = int(seconds // 60)
    rem_seconds = int(seconds % 60)
    return f"{minutes}m {rem_seconds}s" if minutes > 0 else f"{rem_seconds}s"

def get_feedback(secret, guess):
    s_list, g_list = list(secret), list(guess)
    ones, zeros = 0, 0
    # Jedynki (dobre miejsce)
    for i in range(len(g_list)):
        if g_list[i] == s_list[i]:
            ones += 1
            s_list[i] = None
            g_list[i] = "used"
    # Zera (złe miejsce)
    for i in range(len(g_list)):
        if g_list[i] != "used" and g_list[i] in s_list:
            zeros += 1
            s_list[s_list.index(g_list[i])] = None
    return ones, zeros

# --- INICJALIZACJA SESJI ---
if 'secret' not in st.session_state:
    st.session_state.secret = None
    st.session_state.history = []
    st.session_state.game_over = False
    st.session_state.start_time = 0
    st.session_state.duration = 0
    st.session_state.nick = "RobSol"

# --- INTERFEJS UŻYTKOWNIKA ---
st.set_page_config(page_title="Master Mind - Skierniewice Ops", layout="centered", page_icon="🔐")

# Boczny panel (Instrukcja i Admin)
with st.sidebar:
    st.title("📖 Instrukcja misji")
    st.write("Twoim celem jest odgadnięcie tajnego kodu.")
    st.markdown("""
    * **1** = Cyfra na **dobrym** miejscu.
    * **0** = Cyfra w kodzie, ale na **złym** miejscu.
    """)
    st.markdown("---")
    st.write("🔧 **Panel Serwisowy**")
    adm = st.text_input("Kod resetu (Admin):", type="password")
    if adm == "8611":
        if st.button("🚨 WYCZYŚĆ RANKING"):
            if os.path.exists(SCORES_FILE):
                os.remove(SCORES_FILE)
                st.success("Baza wyczyszczona.")
                time.sleep(1)
                st.rerun()

st.title("🔐 Master Mind: Baza Skierniewice")

# --- EKRAN STARTOWY ---
if st.session_state.secret is None:
    with st.container():
        st.session_state.nick = st.text_input("Podaj Nick Hakera:", st.session_state.nick, max_chars=15)
        length = st.slider("Poziom zabezpieczeń (ilość cyfr):", 4, 10, 4)
        
        if st.button("INICJUJ ŁAMANIE HASŁA", use_container_width=True):
            if not st.session_state.nick.strip():
                st.error("Nick nie może być pusty!")
            else:
                st.session_state.secret = "".join([str(random.randint(0, 9)) for _ in range(length)])
                st.session_state.start_time = time.time()
                st.session_state.history = []
                st.session_state.game_over = False
                st.rerun()

# --- EKRAN ROZGRYWKI ---
else:
    st.info(f"Haker: **{st.session_state.nick}** | Cel: **{len(st.session_state.secret)} cyfr**")
    
    if not st.session_state.game_over:
        # Formularz do łapania klawisza Enter
        with st.form(key='guess_form', clear_on_submit=True):
            user_guess = st.text_input("Wprowadź kod i wciśnij Enter:", max_chars=len(st.session_state.secret))
            submit = st.form_submit_button("DEKODUJ")
        
        if submit:
            if len(user_guess) == len(st.session_state.secret) and user_guess.isdigit():
                ones, zeros = get_feedback(st.session_state.secret, user_guess)
                
                # Dodawanie na KONIEC listy (wypełnianie w dół)
                st.session_state.history.append({
                    "Lp.": len(st.session_state.history) + 1, 
                    "Kombinacja": user_guess, 
                    "Wynik": f"1: {ones} | 0: {zeros}"
                })
                
                if ones == len(st.session_state.secret):
                    st.session_state.game_over = True
                    st.session_state.duration = time.time() - st.session_state.start_time
                    
                    # Zapisywanie wyniku w tle od razu po wygranej
                    t_str = format_time_pl(st.session_state.duration)
                    new_data = pd.DataFrame([{
                        "Nick": st.session_state.nick, 
                        "Kod": len(st.session_state.secret), 
                        "Próby": len(st.session_state.history), 
                        "Czas_sek": st.session_state.duration,
                        "Czas": t_str
                    }])
                    if os.path.exists(SCORES_FILE):
                        df = pd.concat([pd.read_csv(SCORES_FILE), new_data], ignore_index=True)
                    else:
                        df = new_data
                    df.to_csv(SCORES_FILE, index=False)
                st.rerun()
            else:
                st.error(f"Odrzucono! Wymagane dokładnie {len(st.session_state.secret)} cyfr.")

    # Wyświetlanie tabeli ruchów (wypełnia się z góry na dół)
    if st.session_state.history:
        st.table(pd.DataFrame(st.session_state.history).set_index("Lp."))

    # Ekran Sukcesu
    if st.session_state.game_over:
        st.success("HASŁO ZŁAMANE!")
        t_str = format_time_pl(st.session_state.duration)
        st.write(f"⏱ Czas: **{t_str}** | 📊 Liczba kroków: **{len(st.session_state.history)}**")
        st.warning("Michał Boryta vel Stanisław Boryta: Wszystkie dane przejęte. Zapisano do crypto.log")
        
        if st.button("NOWA MISJA", use_container_width=True):
            st.session_state.secret = None
            st.rerun()

# --- GLOBALNY RANKING (Wyświetlany zawsze na dole) ---
st.markdown("---")
st.subheader("🏆 Top 10 Hakerów (Globalnie)")
if os.path.exists(SCORES_FILE):
    df_rank = pd.read_csv(SCORES_FILE)
    # Sortowanie premiuje trudność, potem małą ilość kroków, potem szybki czas
    df_rank = df_rank.sort_values(by=["Kod", "Próby", "Czas_sek"], ascending=[False, True, True]).head(10)
    
    # Przeformatowanie tabeli do wyświetlenia
    df_display = df_rank[["Nick", "Kod", "Próby", "Czas"]].reset_index(drop=True)
    df_display.index += 1 # Numeracja od 1
    st.dataframe(df_display, use_container_width=True)
else:
    st.info("Brak wpisów w bazie. Bądź pierwszym, który złamie system!")

st.caption("© 2026 Robert S. | Skierniewice Ops | Wszelkie prawa zastrzeżone.")
