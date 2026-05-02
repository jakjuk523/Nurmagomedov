import streamlit as st
import os
import json
import smtplib
import random
from email.mime.text import MIMEText
from yt_dlp import YoutubeDL
from datetime import datetime

# --- 1. КОНФИГУРАЦИЯ ---
SMTP_SERVER, SMTP_IP = "://gmail.com", "74.125.131.108"
SMTP_PORT = 587
SENDER_EMAIL = "isa.murad.ibaanah@gmail.com"
SENDER_PASSWORD = st.secrets.get('google_password', "")

DOWNLOAD_DIR = "/tmp"
DB_FILE, BAN_FILE, MSG_FILE = "users_db.json", "banned_users.json", "messages.json"
COOKIE_FILE = "cookies.txt" 
SECRET_CODE, ADMIN_PASSWORD = "27032012", "2dsfjqHFugfHUgh219-Hfhwgj@"

# Инициализация файлов
for f in [DB_FILE, BAN_FILE, MSG_FILE]:
    if not os.path.exists(f):
        with open(f, "w", encoding="utf-8") as file:
            json.dump([] if f != DB_FILE else {}, file)

# --- 2. ФУНКЦИИ ДАННЫХ ---
def load_data(file):
    try:
        with open(file, "r", encoding="utf-8") as f:
            c = f.read().strip()
            return json.loads(c) if c else ([] if file != DB_FILE else {})
    except: return [] if file != DB_FILE else {}

def save_data(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def send_otp(email):
    otp = str(random.randint(100000, 999999))
    msg = MIMEText(f"Ваш код доступа: {otp}")
    msg['Subject'], msg['From'], msg['To'] = 'Код подтверждения', SENDER_EMAIL, email
    for target in [SMTP_SERVER, SMTP_IP]:
        try:
            server = smtplib.SMTP(target, SMTP_PORT, timeout=10)
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, email, msg.as_string())
            server.quit()
            return otp
        except: continue
    return None

# --- 3. СЕССИЯ ---
if 'auth_step' not in st.session_state: st.session_state.auth_step = 'main_gate'
if 'user_info' not in st.session_state: st.session_state.user_info = None
if 'formats' not in st.session_state: st.session_state.formats = None
if 'url_buffer' not in st.session_state: st.session_state.url_buffer = ""

st.set_page_config(page_title="Video Downloader", page_icon="📲")

# --- 4. АВТОРИЗАЦИЯ --- (без изменений)
if st.session_state.auth_step == 'main_gate':
    st.title("🔒 Вход")
    t1, t2 = st.tabs(["🔑 Пользователь", "🛠 Организатор"])
    with t1:
        with st.form("gate"):
            c = st.text_input("Код доступа:", type="password")
            if st.form_submit_button("Войти"):
                if c == SECRET_CODE: st.session_state.auth_step = 'login_or_reg'; st.rerun()
                else: st.error("Неверно")
    with t2:
        with st.form("admin_gate"):
            ap = st.text_input("Пароль:", type="password")
            if st.form_submit_button("Админ-вход"):
                if ap == ADMIN_PASSWORD:
                    st.session_state.user_info = {"name": "Админ", "role": "admin"}
                    st.session_state.auth_step = 'app'; st.rerun()

elif st.session_state.auth_step == 'login_or_reg':
    st.title("👤 Аккаунт")
    users, banned = load_data(DB_FILE), load_data(BAN_FILE)
    choice = st.radio("Действие:", ["Вход", "Регистрация", "Забыл пароль"], horizontal=True)
    with st.form("auth"):
        em = st.text_input("Email:").lower().strip()
        pw = st.text_input("Пароль:", type="password") if choice == "Вход" else ""
        if st.form_submit_button("Далее"):
            if not em: st.error("Введите Email")
            elif em in banned: st.error("Доступ закрыт")
            elif choice == "Вход":
                if em in users and isinstance(users[em], dict) and users[em].get('pass') == pw:
                    st.session_state.user_info = {"name": users[em]['name'], "email": em, "role": "user"}
                    st.session_state.auth_step = 'app'; st.rerun()
                else: st.error("Ошибка входа")
            else:
                otp = send_otp(em)
                if otp:
                    st.session_state.temp_email, st.session_state.otp = em, otp
                    st.session_state.auth_step = 'verify' if choice == "Регистрация" else 'reset'
                    st.rerun()

elif st.session_state.auth_step in ['verify', 'reset']:
    st.title("📩 Подтверждение")
    is_reg = st.session_state.auth_step == 'verify'
    with st.form("otp_finish"):
        c, n, p1, p2 = st.text_input("Код:"), st.text_input("Имя:") if is_reg else "", st.text_input("Пароль:", type="password"), st.text_input("Повторите:", type="password")
        if st.form_submit_button("Завершить"):
            if c == st.session_state.get('otp') and p1 == p2 and len(p1) > 3:
                users = load_data(DB_FILE)
                name_val = n if is_reg else users.get(st.session_state.temp_email, {}).get('name', 'User')
                users[st.session_state.temp_email] = {"name": name_val, "pass": p1}
                save_data(DB_FILE, users); st.success("Готово!"); st.session_state.auth_step = 'login_or_reg'; st.rerun()

# --- 5. ПРИЛОЖЕНИЕ ---
elif st.session_state.auth_step == 'app':
    is_admin = st.session_state.user_info.get('role') == 'admin'
    
    # ПАРАМЕТРЫ ДЛЯ ОБХОДА БЛОКИРОВКИ 403
    ydl_base_opts = {
        'quiet': True,
        'nocheckcertificate': True,
        'no_warnings': True,
        'youtube_include_dash_manifest': False,
        # Имитируем разные устройства
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
    }
    
    with st.sidebar:
        st.write(f"👤 **{st.session_state.user_info['name']}**")
        if os.path.exists(COOKIE_FILE):
            st.success("✅ Cookies.txt подключен")
            ydl_base_opts['cookiefile'] = COOKIE_FILE
        
        if st.button("🚪 Выйти"): st.session_state.clear(); st.rerun()
        
        if is_admin:
            st.divider()
            u_db, b_db = load_data(DB_FILE), load_data(BAN_FILE)
            for email, data in u_db.items():
                name = data.get('name', 'User') if isinstance(data, dict) else "Old"
                c1, c2 = st.columns(2)
                c1.write(f"**{name}**\n{email}")
                if c2.button("🚫" if email not in b_db else "✅", key=email):
                    if email in b_db: b_db.remove(email)
                    else: b_db.append(email)
                    save_data(BAN_FILE, b_db); st.rerun()

    t_dl, t_chat = st.tabs(["📥 Загрузка", "💬 Сообщения"])
    
    with t_dl:
        st.title("📲 Video Downloader")
        url = st.text_input("Ссылка на видео:")
        if url != st.session_state.url_buffer:
            st.session_state.url_buffer, st.session_state.formats = url, None

        if url and not st.session_state.formats:
            if st.button("🔍 Получить доступные форматы", use_container_width=True):
                with st.spinner("Пробиваем защиту YouTube..."):
                    try:
                        with YoutubeDL(ydl_base_opts) as ydl:
                            info = ydl.extract_info(url, download=False)
                            opts = {}
                            for f in info.get('formats', []):
                                h = f.get('height')
                                if h and f.get('vcodec') != 'none':
                                    label = f"{h}p ({f.get('ext', 'mp4')})"
                                    if label not in opts or f.get('tbr', 0) > opts[label]['tbr']:
                                        opts[label] = {'id': f['format_id'], 'tbr': f.get('tbr', 0), 'type': 'v'}
                                elif f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                                    opts["🎵 MP3 Аудио"] = {'id': f['format_id'], 'type': 'a'}
                            st.session_state.formats = opts; st.rerun()
                    except Exception as e: st.error(f"Ошибка анализа: {e}")

        if st.session_state.formats:
            choice = st.selectbox("Качество:", list(st.session_state.formats.keys()))
            if st.button("🚀 СКАЧАТЬ ФАЙЛ", type="primary", use_container_width=True):
                try:
                    f_info = st.session_state.formats[choice]
                    with st.spinner("Загрузка и обработка..."):
                        ydl_opts = ydl_base_opts.copy()
                        ydl_opts['format'] = f"{f_info['id']}+bestaudio/best" if f_info['type'] == 'v' else 'bestaudio/best'
                        ydl_opts['outtmpl'] = f'{DOWNLOAD_DIR}/%(title)s.%(ext)s'
                        if f_info['type'] == 'a':
                            ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3'}]
                        
                        with YoutubeDL(ydl_opts) as ydl:
                            info = ydl.extract_info(url, download=True)
                            path = ydl.prepare_filename(info)
                            
                            # ИСПРАВЛЕНИЕ ОШИБКИ С TUPLE ПРИ ПЕРЕИМЕНОВАНИИ
                            if f_info['type'] == 'a': 
                                base, ext = os.path.splitext(path)
                                path = base + ".mp3"
                            
                            with open(path, "rb") as f:
                                st.success("✅ Готово к сохранению!")
                                st.download_button("💾 СОХРАНИТЬ НА УСТРОЙСТВО", f, file_name=os.path.basename(path), use_container_width=True)
                            os.remove(path)
                except Exception as e: st.error(f"Ошибка загрузки: {e}")
            if st.button("🔄 Сбросить ссылку"): st.session_state.formats = None; st.rerun()

    with t_chat:
        st.header("💬 Сообщения")
        msgs = load_data(MSG_FILE)
        if is_admin:
            with st.expander("📝 Написать"):
                txt = st.text_area("Текст:")
                if st.button("Отправить"):
                    msgs.append({"text": txt, "date": datetime.now().strftime("%H:%M"), "likes": 0, "dislikes": 0, "voted": [], "comments": []})
                    save_data(MSG_FILE, msgs); st.rerun()
        for i, m in enumerate(reversed(msgs)):
            idx = len(msgs) - 1 - i
            st.markdown(f"<div style='background:#f0f2f6;padding:15px;border-radius:10px;border-left:5px solid red;'><b>{m['text']}</b><br><small>{m['date']}</small></div>", unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            uid = st.session_state.user_info.get('email', 'admin')
            if c1.button(f"👍 {m.get('likes', 0)}", key=f"l{idx}"):
                if uid not in m.get('voted', []): m['likes'] = m.get('likes', 0) + 1; m.setdefault('voted', []).append(uid); save_data(MSG_FILE, msgs); st.rerun()
            if c2.button(f"👎 {m.get('dislikes', 0)}", key=f"d{idx}"):
                if uid not in m.get('voted', []): m['dislikes'] = m.get('dislikes', 0) + 1; m.setdefault('voted', []).append(uid); save_data(MSG_FILE, msgs); st.rerun()
            with c3.expander(f"💬 ({len(m.get('comments', []))})"):
                for comm in m.get('comments', []): st.markdown(f"**{comm['user']}**: {comm['text']}")
                nc = st.text_input("Ответ...", key=f"in{idx}")
                if st.button("Ок", key=f"btn_c{idx}"):
                    if nc: m.setdefault("comments", []).append({"user": st.session_state.user_info['name'], "text": nc, "time": datetime.now().strftime("%H:%M")}); save_data(MSG_FILE, msgs); st.rerun()
            st.divider()
