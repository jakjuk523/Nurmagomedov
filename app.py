import streamlit as st
import os
import json
import smtplib
import random
from email.mime.text import MIMEText
from yt_dlp import YoutubeDL
from datetime import datetime

# --- 1. КОНФИГУРАЦИЯ ---
st.set_page_config(page_title="Video Downloader & Chat", page_icon="📲", layout="wide")

BASE_DIR = os.getcwd()
DB_FILE = os.path.join(BASE_DIR, "users_db.json")
BAN_FILE = os.path.join(BASE_DIR, "banned_users.json")
MSG_FILE = os.path.join(BASE_DIR, "messages.json")
COOKIE_FILE = os.path.join(BASE_DIR, "cookies.txt")

SECRET_CODE = "27032012"
ADMIN_PASSWORD = "2dsfjqHFugfHUgh219-Hfhwgj@"
SENDER_EMAIL = "isa.murad.ibaanah@gmail.com"
SENDER_PASSWORD = st.secrets.get('google_password', "")

# Инициализация файлов
for f in [DB_FILE, BAN_FILE, MSG_FILE]:
    if not os.path.exists(f):
        with open(f, "w", encoding="utf-8") as file:
            json.dump([] if "users" not in f else {}, file)

if "youtube_cookies" in st.secrets:
    with open(COOKIE_FILE, "w", encoding="utf-8") as f:
        f.write(st.secrets["youtube_cookies"])

# --- 2. ФУНКЦИИ ---
def load_data(file):
    try:
        with open(file, "r", encoding="utf-8") as f:
            content = f.read().strip()
            return json.loads(content) if content else ([] if "users" not in file else {})
    except: return [] if "users" not in file else {}

def save_data(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def send_otp(email):
    otp = str(random.randint(100000, 999999))
    msg = MIMEText(f"Ваш код доступа: {otp}")
    msg['Subject'], msg['From'], msg['To'] = 'Код подтверждения', SENDER_EMAIL, email
    try:
        server = smtplib.SMTP("://gmail.com", 587, timeout=10)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, email, msg.as_string())
        server.quit()
        return otp
    except: return None

# --- 3. СЕССИЯ ---
if 'auth_step' not in st.session_state: st.session_state.auth_step = 'main_gate'
if 'user_info' not in st.session_state: st.session_state.user_info = None
if 'formats' not in st.session_state: st.session_state.formats = None
if 'url_buffer' not in st.session_state: st.session_state.url_buffer = ""

# --- 4. АВТОРИЗАЦИЯ ---
if st.session_state.auth_step == 'main_gate':
    st.title("🔒 Вход")
    t1, t2 = st.tabs(["🔑 Пользователь", "🛠 Админ"])
    with t1:
        code = st.text_input("Код доступа:", type="password", key="gate_code")
        if st.button("Войти"):
            if code == SECRET_CODE: st.session_state.auth_step = 'login_or_reg'; st.rerun()
            else: st.error("Неверно")
    with t2:
        ap = st.text_input("Пароль администратора:", type="password")
        if st.button("Админ-вход"):
            if ap == ADMIN_PASSWORD:
                st.session_state.user_info = {"name": "Админ", "role": "admin", "email": "admin@system"}
                st.session_state.auth_step = 'app'; st.rerun()

elif st.session_state.auth_step == 'login_or_reg':
    st.title("👤 Аккаунт")
    users, banned = load_data(DB_FILE), load_data(BAN_FILE)
    choice = st.radio("Действие:", ["Вход", "Регистрация"], horizontal=True)
    em = st.text_input("Email:").lower().strip()
    pw = st.text_input("Пароль:", type="password") if choice == "Вход" else ""
    if st.button("Далее"):
        if not em: st.error("Введите Email")
        elif em in banned: st.error("Бан")
        elif choice == "Вход":
            if em in users and users[em].get('pass') == pw:
                st.session_state.user_info = {"name": users[em]['name'], "email": em, "role": "user"}
                st.session_state.auth_step = 'app'; st.rerun()
            else: st.error("Ошибка входа")
        else:
            otp = send_otp(em)
            if otp:
                st.session_state.temp_email, st.session_state.otp = em, otp
                st.session_state.auth_step = 'verify'; st.rerun()

elif st.session_state.auth_step == 'verify':
    st.title("📩 Подтверждение")
    c = st.text_input("Код:")
    n = st.text_input("Имя:")
    p1 = st.text_input("Пароль:", type="password")
    if st.button("Завершить"):
        if c == st.session_state.get('otp') and len(p1) >= 4:
            users = load_data(DB_FILE)
            users[st.session_state.temp_email] = {"name": n, "pass": p1}
            save_data(DB_FILE, users); st.success("Готово!"); st.session_state.auth_step = 'login_or_reg'; st.rerun()

# --- 5. ПРИЛОЖЕНИЕ ---
elif st.session_state.auth_step == 'app':
    is_admin = st.session_state.user_info.get('role') == 'admin'
    current_user_email = st.session_state.user_info.get('email')

    with st.sidebar:
        st.header(f"👤 {st.session_state.user_info['name']}")
        if st.button("🚪 Выйти"): st.session_state.clear(); st.rerun()
        if is_admin:
            st.divider()
            st.subheader("Управление")
            u_db, b_db = load_data(DB_FILE), load_data(BAN_FILE)
            for email in u_db:
                if st.button(f"{'✅' if email not in b_db else '🚫'} {email}"):
                    if email in b_db: b_db.remove(email)
                    else: b_db.append(email)
                    save_data(BAN_FILE, b_db); st.rerun()

    t_dl, t_chat = st.tabs(["📥 Загрузка", "💬 История сообщений"])
    
    with t_dl:
        url = st.text_input("Ссылка:")
        if url != st.session_state.url_buffer:
            st.session_state.url_buffer, st.session_state.formats = url, None

        if url and not st.session_state.formats:
            if st.button("🔍 Найти форматы"):
                with st.spinner("Анализ..."):
                    try:
                        ydl_opts = {
                            'quiet': True, 'extractor_args': {'youtube': {'player_client': ['ios', 'web']}},
                            'http_headers': {'User-Agent': 'Mozilla/5.0'}
                        }
                        if os.path.exists(COOKIE_FILE): ydl_opts['cookiefile'] = COOKIE_FILE
                        if "vk" in url: ydl_opts.setdefault('http_headers', {})['Referer'] = 'https://vk.com'
                        
                        with YoutubeDL(ydl_opts) as ydl:
                            info = ydl.extract_info(url, download=False)
                            opts = {}
                            for f in info.get('formats', []):
                                h = f.get('height')
                                if h and f.get('vcodec') != 'none':
                                    opts[f"{h}p ({f.get('ext')})"] = {'id': f['format_id'], 'type': 'v'}
                                elif f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                                    opts["🎵 MP3"] = {'id': f['format_id'], 'type': 'a'}
                            st.session_state.formats = opts; st.rerun()
                    except Exception as e: st.error(f"Ошибка: {e}")

        if st.session_state.formats:
            choice = st.selectbox("Качество:", list(st.session_state.formats.keys()))
            if st.button("🚀 СКАЧАТЬ"):
                try:
                    f_info = st.session_state.formats[choice]
                    with st.spinner("Загрузка..."):
                        ydl_opts = {
                            'format': f"{f_info['id']}+bestaudio/best" if f_info['type'] == 'v' else 'bestaudio/best',
                            'outtmpl': os.path.join(BASE_DIR, '%(title)s.%(ext)s'),
                            'cookiefile': COOKIE_FILE if os.path.exists(COOKIE_FILE) else None
                        }
                        if f_info['type'] == 'a':
                            ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3'}]
                        
                        with YoutubeDL(ydl_opts) as ydl:
                            info = ydl.extract_info(url, download=True)
                            path = ydl.prepare_filename(info)
                            if f_info['type'] == 'a': path = os.path.splitext(path)[0] + ".mp3"
                            
                            with open(path, "rb") as f:
                                st.download_button("💾 СОХРАНИТЬ", f, file_name=os.path.basename(path))
                            os.remove(path)
                except Exception as e: st.error(f"Ошибка: {e}")

    with t_chat:
        st.subheader("💬 Общий чат")
        messages = load_data(MSG_FILE)
        
        # Область сообщений
        chat_container = st.container(height=400)
        with chat_container:
            for m in messages:
                is_me = m.get('author_email') == current_user_email
                align = "right" if is_me else "left"
                bg = "#DCF8C6" if is_me else "#F0F0F0"
                st.markdown(f"""
                <div style="display: flex; justify-content: {align}; margin-bottom: 10px;">
                    <div style="background: {bg}; padding: 10px; border-radius: 15px; max-width: 70%; color: black;">
                        <b style="font-size: 0.8rem; color: #555;">{m.get('author_name', 'User')}</b><br>
                        {m.get('text')}<br>
                        <small style="font-size: 0.6rem; color: gray;">{m.get('date')}</small>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # Форма отправки
        with st.form("send_msg", clear_on_submit=True):
            user_text = st.text_input("Введите сообщение...")
            if st.form_submit_button("Отправить"):
                if user_text:
                    new_msg = {
                        "author_name": st.session_state.user_info['name'],
                        "author_email": current_user_email,
                        "text": user_text,
                        "date": datetime.now().strftime("%H:%M")
                    }
                    messages.append(new_msg)
                    save_data(MSG_FILE, messages)
                    st.rerun()

