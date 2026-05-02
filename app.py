import streamlit as st
import os
import json
import smtplib
import random
from email.mime.text import MIMEText
from yt_dlp import YoutubeDL

# --- 1. НАСТРОЙКИ ---
SMTP_SERVER = "://gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "isa.murad.ibaanah@gmail.com"
SENDER_PASSWORD = st.secrets.get('google_password', "") 

DOWNLOAD_DIR = "/tmp"
DB_FILE = "users_db.json"
BAN_FILE = "banned_users.json"
HISTORY_FILE = "download_history.json"
SECRET_CODE = "27032012"
ADMIN_PASSWORD = "2dsfjqHFugfHUgh219-Hfhwgj@"

# Инициализация файлов
for f in [DB_FILE, BAN_FILE, HISTORY_FILE]:
    if not os.path.exists(f):
        with open(f, "w", encoding="utf-8") as file:
            json.dump([] if "history" in f else {}, file)

# --- 2. ФУНКЦИИ ДАННЫХ ---
def load_data(file):
    try:
        with open(file, "r", encoding="utf-8") as f: return json.load(f)
    except: return [] if "history" in file else {}

def save_data(file, data):
    with open(file, "w", encoding="utf-8") as f: json.dump(data, f, indent=4, ensure_ascii=False)

def send_otp(recipient_email):
    otp = str(random.randint(100000, 999999))
    msg = MIMEText(f"Ваш код подтверждения: {otp}")
    msg['Subject'] = 'Код доступа Video Downloader'
    msg['From'] = SENDER_EMAIL
    msg['To'] = recipient_email
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
        server.quit()
        return otp
    except Exception as e:
        st.error(f"Ошибка почты: {e}")
        return None

# --- 3. ИНИЦИАЛИЗАЦИЯ СЕССИИ ---
if 'auth_step' not in st.session_state: st.session_state.auth_step = 'main_gate'
if 'user_info' not in st.session_state: st.session_state.user_info = None

st.set_page_config(page_title="Video Downloader", page_icon="📲")

# --- 4. ЛОГИКА АВТОРИЗАЦИИ ---
if st.session_state.auth_step == 'main_gate':
    st.title("🔒 Доступ к серверу")
    tab1, tab2 = st.tabs(["🔑 Пользователь", "🛠 Организатор"])
    with tab1:
        with st.form("gate"):
            code = st.text_input("Введите секретный код:", type="password")
            if st.form_submit_button("Войти"):
                if code == SECRET_CODE:
                    st.session_state.auth_step = 'login_or_reg'
                    st.rerun()
                else: st.error("Неверный код")
    with tab2:
        with st.form("admin"):
            adm = st.text_input("Пароль организатора:", type="password")
            if st.form_submit_button("Админ-вход"):
                if adm == ADMIN_PASSWORD:
                    st.session_state.user_info = {"name": "Админ", "role": "admin"}
                    st.session_state.auth_step = 'app'
                    st.rerun()

elif st.session_state.auth_step == 'login_or_reg':
    st.title("👤 Аккаунт")
    users = load_data(DB_FILE)
    banned = load_data(BAN_FILE)
    choice = st.radio("Действие:", ["Вход", "Регистрация", "Забыл пароль"])
    with st.form("auth_form"):
        email = st.text_input("Email:").lower().strip()
        password = st.text_input("Пароль:", type="password") if choice == "Вход" else ""
        if st.form_submit_button("Далее"):
            if email in banned:
                st.error("Ваш аккаунт заблокирован.")
            elif choice == "Вход":
                if email in users and users[email]['pass'] == password:
                    st.session_state.user_info = {"name": users[email]['name'], "email": email, "role": "user"}
                    st.session_state.auth_step = 'app'
                    st.rerun()
                else: st.error("Ошибка входа")
            elif choice == "Регистрация":
                st.session_state.temp_email = email
                st.session_state.secret_storage = send_otp(email)
                if st.session_state.secret_storage:
                    st.session_state.auth_step = 'verify_otp'
                    st.rerun()
            elif choice == "Забыл пароль":
                if email in users:
                    st.session_state.temp_email = email
                    st.session_state.secret_storage = send_otp(email)
                    if st.session_state.secret_storage:
                        st.session_state.auth_step = 'reset_pass_verify'
                        st.rerun()
                else: st.error("Пользователь не найден")

elif st.session_state.auth_step == 'verify_otp':
    st.title("📩 Регистрация")
    with st.form("otp_form"):
        input_code = st.text_input("Код из письма:")
        name = st.text_input("Ваше имя:")
        new_pass = st.text_input("Придумайте пароль:", type="password")
        confirm_pass = st.text_input("Подтвердите пароль:", type="password")
        if st.form_submit_button("Зарегистрироваться"):
            if input_code != st.session_state.secret_storage:
                st.error("Неверный код!")
            elif new_pass != confirm_pass:
                st.error("Пароли не совпадают!")
            elif len(new_pass) < 4:
                st.error("Пароль слишком короткий!")
            else:
                users = load_data(DB_FILE)
                users[st.session_state.temp_email] = {"name": name, "pass": new_pass}
                save_data(DB_FILE, users)
                st.success("Регистрация успешна! Войдите.")
                st.session_state.auth_step = 'login_or_reg'
                st.rerun()

elif st.session_state.auth_step == 'reset_pass_verify':
    st.title("🔑 Восстановление доступа")
    with st.form("reset_otp_form"):
        input_code = st.text_input("Код подтверждения:")
        new_pass = st.text_input("Новый пароль:", type="password")
        confirm_pass = st.text_input("Подтвердите новый пароль:", type="password")
        if st.form_submit_button("Сменить пароль"):
            if input_code == st.session_state.secret_storage:
                if new_pass == confirm_pass:
                    users = load_data(DB_FILE)
                    users[st.session_state.temp_email]['pass'] = new_pass
                    save_data(DB_FILE, users)
                    st.success("Пароль изменен!")
                    st.session_state.auth_step = 'login_or_reg'
                    st.rerun()
                else: st.error("Пароли не совпадают")
            else: st.error("Неверный код")

# --- 5. ОСНОВНОЕ ПРИЛОЖЕНИЕ ---
elif st.session_state.auth_step == 'app':
    with st.sidebar:
        st.write(f"👤 **{st.session_state.user_info['name']}**")
        
        # Кнопка смены пароля для обычного пользователя
        if st.session_state.user_info.get('role') != 'admin':
            if st.button("⚙️ Сменить пароль"):
                st.session_state.temp_email = st.session_state.user_info['email']
                st.session_state.secret_storage = send_otp(st.session_state.temp_email)
                if st.session_state.secret_storage:
                    st.session_state.auth_step = 'reset_pass_verify'
                    st.rerun()

        if st.button("🚪 Выйти"):
            st.session_state.clear()
            st.rerun()
        
        # --- АДМИН ПАНЕЛЬ ---
        if st.session_state.user_info.get('role') == 'admin':
            st.divider()
            st.subheader("🛠 Панель Организатора")
            users = load_data(DB_FILE)
            banned = load_data(BAN_FILE)
            st.write(f"Юзеров: {len(users)}")
            if st.checkbox("Список пользователей"):
                for u_email, u_data in users.items():
                    status = "🛑" if u_email in banned else "✅"
                    st.text(f"{status} {u_data['name']} ({u_email})")
            
            target = st.text_input("Email юзера:").lower().strip()
            c1, c2 = st.columns(2)
            if c1.button("БАН"):
                if target and target not in banned:
                    banned.append(target); save_data(BAN_FILE, banned)
                    st.rerun()
            if c2.button("РАЗБАН"):
                if target in banned:
                    banned.remove(target); save_data(BAN_FILE, banned)
                    st.rerun()

    st.title("📲 Video Downloader")
    url = st.text_input("Вставьте ссылку:")
    quality = st.selectbox("Качество:", ["1080", "720", "Audio MP3"])

    if st.button("🚀 ЗАПУСТИТЬ", type="primary", use_container_width=True):
        if url:
            status_text = st.empty()
            ydl_format = 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            if quality == "720": ydl_format = 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            if quality == "Audio MP3": ydl_format = 'bestaudio/best'

            ydl_opts = {
                'format': ydl_format,
                'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
                'noplaylist': True,
                'http_headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'},
            }

            if quality == "Audio MP3":
                ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}]

            try:
                with YoutubeDL(ydl_opts) as ydl:
                    status_text.text("Загрузка...")
                    info = ydl.extract_info(url, download=True)
                    path = ydl.prepare_filename(info)
                    if quality == "Audio MP3": path = os.path.splitext(path)[0] + ".mp3"

                    with open(path, "rb") as f:
                        st.success("✅ Готово!")
                        st.download_button(label="💾 СКАЧАТЬ", data=f, file_name=os.path.basename(path))
                    os.remove(path)
            except Exception as e:
                st.error(f"Ошибка: {e}")
