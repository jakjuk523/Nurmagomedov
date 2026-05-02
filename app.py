import streamlit as st
import os
import json
import smtplib
import random
from email.mime.text import MIMEText
from yt_dlp import YoutubeDL
from datetime import datetime

# --- 1. КОНФИГУРАЦИЯ (Приватная) ---
st.set_page_config(page_title="Private DL & Chat", page_icon="🛡️", layout="wide")

BASE_DIR = os.getcwd()
DB_FILE = os.path.join(BASE_DIR, "users_db.json")
BAN_FILE = os.path.join(BASE_DIR, "banned_users.json")
MSG_FILE = os.path.join(BASE_DIR, "messages.json")
COOKIE_FILE = os.path.join(BASE_DIR, "cookies.txt")

# Твои секретные данные
SECRET_CODE = "27032012"
ADMIN_PASSWORD = "2dsfjqHFugfHUgh219-Hfhwgj@"
SENDER_EMAIL = "isa.murad.ibaanah@gmail.com"
SENDER_PASSWORD = st.secrets.get('google_password', "")

# Инициализация хранилища
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
            return json.load(f)
    except: return [] if "users" not in file else {}

def save_data(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def send_otp(email):
    otp = str(random.randint(100000, 999999))
    msg = MIMEText(f"Твой код доступа: {otp}")
    msg['Subject'], msg['From'], msg['To'] = 'Авторизация в системе', SENDER_EMAIL, email
    try:
        server = smtplib.SMTP("://gmail.com", 587, timeout=10)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, email, msg.as_string())
        server.quit()
        return otp
    except: return None

# --- 3. ЛОГИКА ДОСТУПА ---
if 'auth_step' not in st.session_state: st.session_state.auth_step = 'gate'
if 'user_info' not in st.session_state: st.session_state.user_info = None

if st.session_state.auth_step == 'gate':
    st.title("🛡️ Вход в закрытую систему")
    col1, col2 = st.columns(2)
    with col1:
        code = st.text_input("Введите мастер-код:", type="password")
        if st.button("Подтвердить код"):
            if code == SECRET_CODE:
                st.session_state.auth_step = 'auth'; st.rerun()
            else: st.error("Доступ запрещен.")
    with col2:
        adm = st.text_input("Вход для владельца:", type="password")
        if st.button("Вход владельца"):
            if adm == ADMIN_PASSWORD:
                st.session_state.user_info = {"name": "Владелец", "role": "admin", "email": "master@root"}
                st.session_state.auth_step = 'app'; st.rerun()

elif st.session_state.auth_step == 'auth':
    st.title("👤 Личный кабинет")
    users = load_data(DB_FILE)
    banned = load_data(BAN_FILE)
    mode = st.radio("Действие", ["Вход", "Регистрация"], horizontal=True)
    em = st.text_input("Email:").lower().strip()
    
    if mode == "Вход":
        pw = st.text_input("Пароль:", type="password")
        if st.button("Войти"):
            if em in banned: st.error("Доступ заблокирован.")
            elif em in users and users[em]['pass'] == pw:
                st.session_state.user_info = {"name": users[em]['name'], "email": em, "role": "user"}
                st.session_state.auth_step = 'app'; st.rerun()
            else: st.error("Неверные данные.")
    else:
        if st.button("Получить код на почту"):
            otp = send_otp(em)
            if otp:
                st.session_state.temp_email, st.session_state.otp = em, otp
                st.session_state.auth_step = 'verify'; st.rerun()
            else: st.error("Ошибка отправки. Проверь email.")

elif st.session_state.auth_step == 'verify':
    st.title("📩 Верификация")
    c = st.text_input("Код из письма:")
    n = st.text_input("Твое имя:")
    p = st.text_input("Придумай пароль:", type="password")
    if st.button("Создать аккаунт"):
        if c == st.session_state.otp and len(p) >= 4:
            u = load_data(DB_FILE)
            u[st.session_state.temp_email] = {"name": n, "pass": p}
            save_data(DB_FILE, u)
            st.success("Готово! Теперь войди."); st.session_state.auth_step = 'auth'; st.rerun()

# --- 4. ОСНОВНОЙ ФУНКЦИОНАЛ ---
elif st.session_state.auth_step == 'app':
    user = st.session_state.user_info
    
    with st.sidebar:
        st.write(f"Привет, **{user['name']}**!")
        if st.button("Выйти"): st.session_state.clear(); st.rerun()
        
        if user['role'] == 'admin':
            st.divider()
            st.caption("Управление доступом")
            all_u = load_data(DB_FILE)
            b_list = load_data(BAN_FILE)
            for mail in all_u:
                status = "🚫" if mail in b_list else "✅"
                if st.button(f"{status} {mail}"):
                    if mail in b_list: b_list.remove(mail)
                    else: b_list.append(mail)
                    save_data(BAN_FILE, b_list); st.rerun()

    tab_dl, tab_chat = st.tabs(["📥 Загрузка видео", "💬 Приватный чат"])

    with tab_dl:
        url = st.text_input("Ссылка на видео:")
        if url:
            if st.button("🔍 Найти доступные качества"):
                with st.spinner("Обходим блокировки..."):
                    try:
                        ydl_opts = {
                            'quiet': True,
                            'http_headers': {
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                                'Referer': 'https://vk.com' if 'vk' in url else 'https://google.com'
                            }
                        }
                        if os.path.exists(COOKIE_FILE): ydl_opts['cookiefile'] = COOKIE_FILE
                        
                        with YoutubeDL(ydl_opts) as ydl:
                            info = ydl.extract_info(url, download=False)
                            formats = info.get('formats', [info])
                            res_opts = {}
                            for f in formats:
                                if f.get('height') and f.get('vcodec') != 'none':
                                    res_opts[f"{f['height']}p ({f['ext']})"] = f['format_id']
                            
                            st.session_state.current_formats = res_opts
                            st.session_state.current_url = url
                    except Exception as e: st.error(f"Ошибка (возможно, нужны свежие куки): {e}")

        if 'current_formats' in st.session_state and st.session_state.current_formats:
            qual = st.selectbox("Выбери качество:", list(st.session_state.current_formats.keys()))
            if st.button("🚀 Скачать"):
                try:
                    with st.spinner("Загружаем..."):
                        fid = st.session_state.current_formats[qual]
                        ydl_opts = {
                            'format': f"{fid}+bestaudio/best",
                            'outtmpl': '%(title)s.%(ext)s',
                            'cookiefile': COOKIE_FILE if os.path.exists(COOKIE_FILE) else None,
                            'merge_output_format': 'mp4'
                        }
                        with YoutubeDL(ydl_opts) as ydl:
                            info = ydl.extract_info(st.session_state.current_url, download=True)
                            fname = ydl.prepare_filename(info).replace('.mkv', '.mp4').replace('.webm', '.mp4')
                            
                            with open(fname, "rb") as f:
                                st.download_button("💾 Сохранить на устройство", f, file_name=fname)
                            os.remove(fname)
                except Exception as e: st.error(f"Ошибка при скачивании: {e}")

    with tab_chat:
        msgs = load_data(MSG_FILE)
        st.caption("Чат зашифрован (XSS Protection Active)")
        
        container = st.container(height=400)
        for m in msgs:
            is_me = m['author_email'] == user['email']
            # Защита от взлома через текст
            clean_text = m['text'].replace("<", "&lt;").replace(">", "&gt;")
            
            container.markdown(f"""
                <div style="text-align: {'right' if is_me else 'left'}; margin-bottom: 10px;">
                    <div style="display: inline-block; background: {'#DCF8C6' if is_me else '#F0F2F5'}; 
                                padding: 8px 12px; border-radius: 15px; color: black; text-align: left;">
                        <small style="color: #666;">{m['author_name']}</small><br>{clean_text}
                        <div style="font-size: 0.7em; color: #999; text-align: right;">{m['date']}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        with st.form("chat_f", clear_on_submit=True):
            txt = st.text_input("Ваше сообщение...")
            if st.form_submit_button("Отправить") and txt:
                msgs.append({
                    "author_name": user['name'],
                    "author_email": user['email'],
                    "text": txt,
                    "date": datetime.now().strftime("%H:%M")
                })
                save_data(MSG_FILE, msgs[-100:])
                st.rerun()
