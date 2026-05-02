import pathlib
import platform
import streamlit as st
import os
import re
import json
import smtplib
import random
from email.mime.text import MIMEText
from datetime import datetime
from yt_dlp import YoutubeDL

# --- 1. НАСТРОЙКИ ПОЧТЫ (ЗАПОЛНИ ЭТО) ---
SMTP_SERVER = "64.233.165.108"
SMTP_PORT = 587
SENDER_EMAIL = "isa.murad.ibaanah@gmail.com"  # Твоя почта
SENDER_PASSWORD = st.secrets['google_password']  # Твой 16-значный код приложения


# --- 2. ПУТИ И КОНФИГУРАЦИЯ ---
def get_download_path():
    return str(pathlib.Path.home() / "Downloads")


DOWNLOAD_DIR = get_download_path()
DB_FILE = "users_db.json"
BAN_FILE = "banned_users.json"
HISTORY_FILE = "download_history.json"
SECRET_CODE = "27032012"
ADMIN_PASSWORD = "2dsfjqHFugfHUgh219-Hfhwgj@"

for f in [DB_FILE, BAN_FILE, HISTORY_FILE]:
    if not os.path.exists(f):
        with open(f, "w", encoding="utf-8") as file:
            json.dump([] if "history" in f else {}, file)


# --- 3. ФУНКЦИИ ---
def load_data(file):
    with open(file, "r", encoding="utf-8") as f: return json.load(f)


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


def clean_text(text):
    if not text: return ""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text).strip()


# --- 4. ИНИЦИАЛИЗАЦИЯ СЕССИИ ---
if 'auth_step' not in st.session_state: st.session_state.auth_step = 'main_gate'
if 'user_info' not in st.session_state: st.session_state.user_info = None
if 'url_buffer' not in st.session_state: st.session_state.url_buffer = ""

# --- 5. ЛОГИКА АВТОРИЗАЦИИ (ЭКРАНЫ) ---
st.set_page_config(page_title="Video Downloader", page_icon="📲")

import pathlib
import streamlit as st
import os
import re
import json
import smtplib
import random
from email.mime.text import MIMEText
from yt_dlp import YoutubeDL

# --- 1. НАСТРОЙКИ ПОЧТЫ ---
SMTP_SERVER = "://gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "isa.murad.ibaanah@gmail.com"
# Пароль берется из настроек Streamlit Cloud (Secrets)
SENDER_PASSWORD = st.secrets.get('google_password', "")

# --- 2. ПУТИ И КОНФИГУРАЦИЯ ---
# В облаке используем /tmp для временного хранения файлов
DOWNLOAD_DIR = "/tmp"
DB_FILE = "users_db.json"
BAN_FILE = "banned_users.json"
HISTORY_FILE = "download_history.json"
SECRET_CODE = "27032012"
ADMIN_PASSWORD = "2dsfjqHFugfHUgh219-Hfhwgj@"

# Создание файлов базы данных, если их нет
for f in [DB_FILE, BAN_FILE, HISTORY_FILE]:
    if not os.path.exists(f):
        with open(f, "w", encoding="utf-8") as file:
            json.dump([] if "history" in f else {}, file)


# --- 3. ФУНКЦИИ ---
def load_data(file):
    try:
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


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
        st.error(f"Ошибка почты: {e}. Проверьте google_password в Secrets!")
        return None


# --- 4. ИНИЦИАЛИЗАЦИЯ СЕССИИ ---
if 'auth_step' not in st.session_state: st.session_state.auth_step = 'main_gate'
if 'user_info' not in st.session_state: st.session_state.user_info = None
if 'url_buffer' not in st.session_state: st.session_state.url_buffer = ""

st.set_page_config(page_title="Video Downloader", page_icon="📲")

# --- 5. ЛОГИКА АВТОРИЗАЦИИ ---
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
                else:
                    st.error("Неверный код")
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
    choice = st.radio("Действие:", ["Вход", "Регистрация", "Забыл пароль"])
    with st.form("auth_form"):
        email = st.text_input("Email:").lower().strip()
        password = st.text_input("Пароль:", type="password") if choice == "Вход" else ""
        if st.form_submit_button("Далее"):
            if choice == "Вход":
                if email in users and users[email]['pass'] == password:
                    st.session_state.user_info = {"name": users[email]['name'], "email": email}
                    st.session_state.auth_step = 'app'
                    st.rerun()
                else:
                    st.error("Ошибка входа")
            elif choice == "Регистрация":
                st.session_state.temp_email = email
                st.session_state.secret_storage = send_otp(email)
                if st.session_state.secret_storage:
                    st.session_state.auth_step = 'verify_otp'
                    st.rerun()

elif st.session_state.auth_step == 'verify_otp':
    st.title("📩 Подтверждение")
    with st.form("otp_form"):
        input_code = st.text_input("Код из письма:")
        name = st.text_input("Ваше имя:")
        new_pass = st.text_input("Пароль:", type="password")
        if st.form_submit_button("Зарегистрироваться"):
            if input_code == st.session_state.secret_storage:
                users = load_data(DB_FILE)
                users[st.session_state.temp_email] = {"name": name, "pass": new_pass}
                save_data(DB_FILE, users)
                st.success("Готово! Теперь войдите.")
                st.session_state.auth_step = 'login_or_reg'
                st.rerun()

# --- 6. ОСНОВНОЕ ПРИЛОЖЕНИЕ ---
elif st.session_state.auth_step == 'app':
    status_text = st.empty()
    progress_bar = st.progress(0)


    def progress_hook(d):
        if d['status'] == 'downloading':
            p = d.get('_percent_str', '0%').replace('%', '')
            try:
                progress_bar.progress(float(p) / 100)
                status_text.text(f"Загрузка: {d.get('_percent_str')} | Скорость: {d.get('_speed_str')}")
            except:
                pass


    with st.sidebar:
        st.write(f"👤 {st.session_state.user_info['name']}")
        if st.button("Выйти"):
            st.session_state.clear()
            st.rerun()

    st.title("📲 Video Downloader")
    url = st.text_input("Вставьте ссылку:", value=st.session_state.url_buffer)
    quality = st.selectbox("Качество:", ["1080", "720", "Audio MP3"])

    if st.button("🚀 ЗАПУСТИТЬ", type="primary", use_container_width=True):
        if url:
            # Настройка формата для yt-dlp
            if quality == "Audio MP3":
                ydl_format = 'bestaudio/best'
            elif quality == "1080":
                ydl_format = 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            else:
                ydl_format = 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'

            ydl_opts = {
                'format': ydl_format,
                'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
                'progress_hooks': [progress_hook],
                'noplaylist': True,
            }

            if quality == "Audio MP3":
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]

            try:
                with YoutubeDL(ydl_opts) as ydl:
                    status_text.text("Анализирую ссылку...")
                    info = ydl.extract_info(url, download=True)
                    path = ydl.prepare_filename(info)

                    if quality == "Audio MP3":
                        path = os.path.splitext(path)[0] + ".mp3"

                    with open(path, "rb") as f:
                        st.success("✅ Файл готов!")
                        st.download_button(
                            label="💾 СКАЧАТЬ ФАЙЛ",
                            data=f,
                            file_name=os.path.basename(path),
                            mime="video/mp4" if quality != "Audio MP3" else "audio/mpeg"
                        )
                    # Очистка места на сервере
                    os.remove(path)
            except Exception as e:
                st.error(f"Ошибка загрузки: {e}")
