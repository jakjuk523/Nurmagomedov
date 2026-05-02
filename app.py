import streamlit as st
import os
import json
import smtplib
import random
from email.mime.text import MIMEText
from yt_dlp import YoutubeDL
from datetime import datetime

# --- 1. НАСТРОЙКИ ---
SMTP_SERVER = "://gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "isa.murad.ibaanah@gmail.com"
SENDER_PASSWORD = st.secrets.get('google_password', "") 

DOWNLOAD_DIR = "/tmp"
DB_FILE = "users_db.json"
BAN_FILE = "banned_users.json"
MESSAGES_FILE = "messages.json"
SECRET_CODE = "27032012"
ADMIN_PASSWORD = "2dsfjqHFugfHUgh219-Hfhwgj@"

# Инициализация файлов
for f in [DB_FILE, BAN_FILE, MESSAGES_FILE]:
    if not os.path.exists(f):
        with open(f, "w", encoding="utf-8") as file:
            json.dump([] if f != DB_FILE else {}, file)

# --- 2. ФУНКЦИИ ДАННЫХ ---
def load_data(file):
    try:
        with open(file, "r", encoding="utf-8") as f: 
            content = f.read().strip()
            if not content: return [] if file != DB_FILE else {}
            return json.loads(content)
    except: return [] if file != DB_FILE else {}

def save_data(file, data):
    with open(file, "w", encoding="utf-8") as f: 
        json.dump(data, f, indent=4, ensure_ascii=False)

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
    except: return None

# --- 3. ИНИЦИАЛИЗАЦИЯ СЕССИИ ---
if 'auth_step' not in st.session_state: st.session_state.auth_step = 'main_gate'
if 'user_info' not in st.session_state: st.session_state.user_info = None
if 'formats' not in st.session_state: st.session_state.formats = None
if 'url_buffer' not in st.session_state: st.session_state.url_buffer = ""

st.set_page_config(page_title="Video Downloader", page_icon="📲")

# --- 4. ЛОГИКА АВТОРИЗАЦИИ ---
if st.session_state.auth_step == 'main_gate':
    st.title("🔒 Доступ к серверу: Приложение Исы")
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
            if email in banned: st.error("Ваш доступ заблокирован.")
            elif choice == "Вход":
                if email in users and isinstance(users[email], dict) and users[email].get('pass') == password:
                    st.session_state.user_info = {"name": users[email]['name'], "email": email, "role": "user"}
                    st.session_state.auth_step = 'app'
                    st.rerun()
                else: st.error("Ошибка входа или старый формат аккаунта")
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

elif st.session_state.auth_step == 'verify_otp':
    st.title("📩 Регистрация")
    with st.form("otp_form"):
        input_code = st.text_input("Код из письма:")
        name = st.text_input("Ваше имя:")
        p1 = st.text_input("Пароль:", type="password")
        p2 = st.text_input("Повторите пароль:", type="password")
        if st.form_submit_button("Ок"):
            if input_code == st.session_state.get('secret_storage') and p1 == p2 and len(p1) > 3:
                users = load_data(DB_FILE)
                users[st.session_state.temp_email] = {"name": name, "pass": p1}
                save_data(DB_FILE, users)
                st.success("Успех! Теперь войдите.")
                st.session_state.auth_step = 'login_or_reg'
                st.rerun()
            else: st.error("Ошибка в данных или коде")

elif st.session_state.auth_step == 'reset_pass_verify':
    st.title("🔑 Смена пароля")
    with st.form("reset_form"):
        input_code = st.text_input("Код подтверждения:")
        p1 = st.text_input("Новый пароль:", type="password")
        p2 = st.text_input("Повторите:", type="password")
        if st.form_submit_button("Сменить"):
            if input_code == st.session_state.get('secret_storage') and p1 == p2:
                users = load_data(DB_FILE)
                if st.session_state.temp_email in users:
                    if not isinstance(users[st.session_state.temp_email], dict):
                        users[st.session_state.temp_email] = {"name": "User", "pass": p1}
                    else:
                        users[st.session_state.temp_email]['pass'] = p1
                    save_data(DB_FILE, users)
                    st.success("Пароль изменен")
                    st.session_state.auth_step = 'login_or_reg'
                    st.rerun()

# --- 5. ПРИЛОЖЕНИЕ ---
elif st.session_state.auth_step == 'app':
    is_admin = st.session_state.user_info.get('role') == 'admin'

    with st.sidebar:
        st.write(f"👤 **{st.session_state.user_info['name']}**")
        if not is_admin:
            if st.button("⚙️ Сменить пароль"):
                st.session_state.temp_email = st.session_state.user_info['email']
                st.session_state.secret_storage = send_otp(st.session_state.temp_email)
                st.session_state.auth_step = 'reset_pass_verify'
                st.rerun()
        if st.button("🚪 Выйти"):
            st.session_state.clear()
            st.rerun()
        
        if is_admin:
            st.divider()
            st.subheader("🛠 Управление пользователями")
            users = load_data(DB_FILE)
            banned = load_data(BAN_FILE)
            
            if not users:
                st.info("База пуста")
            else:
                for email, data in users.items():
                    # ЗАЩИТА: Проверка формата данных
                    if isinstance(data, dict):
                        u_name = data.get('name', 'Без имени')
                    else:
                        u_name = "Старый аккаунт"
                    
                    col_u, col_b = st.columns([2, 1])
                    col_u.markdown(f"**{u_name}**\n<small>{email}</small>", unsafe_allow_html=True)
                    
                    if email in banned:
                        if col_b.button("Разбан", key=f"unban_{email}"):
                            banned.remove(email); save_data(BAN_FILE, banned); st.rerun()
                    else:
                        if col_b.button("БАН", key=f"ban_{email}"):
                            banned.append(email); save_data(BAN_FILE, banned); st.rerun()
                    st.divider()

            if st.button("🗑 Очистить кэш видео"):
                for f in os.listdir(DOWNLOAD_DIR):
                    if f.endswith((".mp4",".mp3",".part")): os.remove(os.path.join(DOWNLOAD_DIR, f))
                st.success("Очищено")

    # Вкладки
    tab_dl, tab_msg = st.tabs(["📥 Загрузка", "💬 Сообщения"])

    with tab_dl:
        st.title("📲 Video Downloader")
        url = st.text_input("Вставьте ссылку:", value=st.session_state.url_buffer)
        if url != st.session_state.url_buffer:
            st.session_state.url_buffer = url
            st.session_state.formats = None; st.rerun()

        if url and not st.session_state.formats:
            if st.button("🔍 Анализ"):
                with st.spinner("Анализирую форматы..."):
                    try:
                        with YoutubeDL({'noplaylist':True, 'quiet':True}) as ydl:
                            info = ydl.extract_info(url, download=False)
                            opts = {}
                            for f in info.get('formats', []):
                                if f.get('height'):
                                    label = f"{f['height']}p ({f['ext']})"
                                    opts[label] = {'id': f['format_id'], 'type': 'v'}
                                elif f.get('acodec')!='none' and f.get('vcodec')=='none':
                                    opts["MP3 Аудио"] = {'id': f['format_id'], 'type': 'a'}
                            st.session_state.formats = opts; st.rerun()
                    except Exception as e: st.error(f"Ошибка: {e}")

        if st.session_state.formats:
            choice = st.selectbox("Выберите качество:", list(st.session_state.formats.keys()))
            if st.button("🚀 СКАЧАТЬ", type="primary", use_container_width=True):
                f_info = st.session_state.formats[choice]
                ydl_opts = {
                    'format': f_info['id']+'+bestaudio/best' if f_info['type']=='v' else 'bestaudio/best',
                    'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
                    'nocheckcertificate': True,
                    'http_headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'}
                }
                if f_info['type']=='a': ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3'}]
                try:
                    with YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=True)
                        path = ydl.prepare_filename(info)
                        if f_info['type']=='a': path = os.path.splitext(path)[0] + ".mp3"
                        with open(path, "rb") as f:
                            st.download_button("💾 Сохранить файл", f, file_name=os.path.basename(path))
                        os.remove(path)
                except Exception as e: st.error(f"Ошибка загрузки: {e}")
            if st.button("🔄 Сброс"): st.session_state.formats = None; st.session_state.url_buffer = ""; st.rerun()

    with tab_msg:
        st.header("💬 Сообщения")
        msgs = load_data(MESSAGES_FILE)
        if is_admin:
            with st.expander("📝 Написать объявление"):
                new_msg = st.text_area("Текст:")
                if st.button("Отправить"):
                    if new_msg:
                        msgs.append({"id": len(msgs), "text": new_msg, "date": datetime.now().strftime("%d.%m %H:%M"), "likes": 0, "dislikes": 0, "users_voted": []})
                        save_data(MESSAGES_FILE, msgs); st.rerun()

        for i, m in enumerate(reversed(msgs)):
            idx = len(msgs) - 1 - i
            st.markdown(f"<div style='background: #f0f2f6; padding: 10px; border-radius: 10px; border-left: 5px solid red;'><small>{m['date']}</small><br>{m['text']}</div>", unsafe_allow_html=True)
            c1, c2, _ = st.columns([1,1,4])
            u_id = st.session_state.user_info.get('email', 'admin')
            if c1.button(f"👍 {m['likes']}", key=f"l_{idx}"):
                if u_id not in msgs[idx]['users_voted']:
                    msgs[idx]['likes'] += 1; msgs[idx]['users_voted'].append(u_id); save_data(MESSAGES_FILE, msgs); st.rerun()
            if c2.button(f"👎 {m['dislikes']}", key=f"d_{idx}"):
                if u_id not in msgs[idx]['users_voted']:
                    msgs[idx]['dislikes'] += 1; msgs[idx]['users_voted'].append(u_id); save_data(MESSAGES_FILE, msgs); st.rerun()
            st.divider()
