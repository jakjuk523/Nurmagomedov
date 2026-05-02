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
        with open(file, "r", encoding="utf-8") as f: return json.load(f)
    except: return [] if file != DB_FILE else {}

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
    except: return None

# --- 3. СЕССИЯ ---
if 'auth_step' not in st.session_state: st.session_state.auth_step = 'main_gate'
if 'user_info' not in st.session_state: st.session_state.user_info = None
if 'formats' not in st.session_state: st.session_state.formats = None

st.set_page_config(page_title="Video Downloader", page_icon="📲")

# --- 4. АВТОРИЗАЦИЯ ---
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
            if email in banned: st.error("Доступ заблокирован.")
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
                st.session_state.auth_step = 'login_or_reg'
                st.rerun()
            else: st.error("Проверьте данные")

elif st.session_state.auth_step == 'reset_pass_verify':
    st.title("🔑 Смена пароля")
    with st.form("reset_form"):
        input_code = st.text_input("Код подтверждения:")
        p1 = st.text_input("Новый пароль:", type="password")
        p2 = st.text_input("Повторите:", type="password")
        if st.form_submit_button("Сменить"):
            if input_code == st.session_state.get('secret_storage') and p1 == p2:
                users = load_data(DB_FILE)
                users[st.session_state.temp_email]['pass'] = p1
                save_data(DB_FILE, users)
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
            st.subheader("🛠 Админка")
            users = load_data(DB_FILE); banned = load_data(BAN_FILE)
            st.write(f"Юзеров: {len(users)}")
            target = st.text_input("Email для бана:").lower().strip()
            if st.button("БАН/РАЗБАН"):
                if target in banned: banned.remove(target)
                else: banned.append(target)
                save_data(BAN_FILE, banned); st.rerun()
            if st.button("🗑 Очистить кэш видео"):
                for f in os.listdir(DOWNLOAD_DIR):
                    if f.endswith((".mp4",".mp3",".part")): os.remove(os.path.join(DOWNLOAD_DIR, f))
                st.success("Очищено")

    # Вкладки приложения
    tab_dl, tab_msg = st.tabs(["📥 Загрузка", "💬 Сообщения"])

    # --- ВКЛАДКА ЗАГРУЗКИ ---
    with tab_dl:
        st.title("📲 Video Downloader")
        url = st.text_input("Вставьте ссылку:")
        if url and not st.session_state.formats:
            if st.button("🔍 Анализ"):
                with st.spinner("Анализирую..."):
                    try:
                        with YoutubeDL({'noplaylist':True}) as ydl:
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
            choice = st.selectbox("Качество:", list(st.session_state.formats.keys()))
            if st.button("🚀 СКАЧАТЬ", type="primary"):
                f_info = st.session_state.formats[choice]
                ydl_opts = {'format': f_info['id']+'+bestaudio/best' if f_info['type']=='v' else 'bestaudio/best', 'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s'}
                if f_info['type']=='a': ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3'}]
                try:
                    with YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=True)
                        path = ydl.prepare_filename(info)
                        if f_info['type']=='a': path = os.path.splitext(path)[0] + ".mp3"
                        with open(path, "rb") as f:
                            st.download_button("💾 Сохранить", f, file_name=os.path.basename(path))
                        os.remove(path)
                except Exception as e: st.error(f"Ошибка: {e}")
            if st.button("🔄 Сброс"): st.session_state.formats = None; st.rerun()

    # --- ВКЛАДКА СООБЩЕНИЙ ---
    with tab_msg:
        st.header("💬 Объявления от Организатора")
        msgs = load_data(MESSAGES_FILE)

        if is_admin:
            with st.expander("📝 Написать новое сообщение"):
                new_msg = st.text_area("Текст сообщения:")
                if st.button("Отправить"):
                    if new_msg:
                        msgs.append({
                            "id": len(msgs),
                            "text": new_msg,
                            "date": datetime.now().strftime("%d.%m %H:%M"),
                            "likes": 0,
                            "dislikes": 0,
                            "users_voted": [] # Чтобы нельзя было голосовать много раз
                        })
                        save_data(MESSAGES_FILE, msgs); st.rerun()

        if not msgs:
            st.info("Сообщений пока нет.")
        else:
            for i, m in enumerate(reversed(msgs)):
                with st.container():
                    st.markdown(f"""
                    <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #ff4b4b;">
                        <small style="color: #666;">{m['date']}</small><br>
                        <p style="margin: 5px 0; font-size: 16px;">{m['text']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Кнопки лайков (используем реальный индекс из исходного списка)
                    idx = len(msgs) - 1 - i
                    col1, col2, _ = st.columns([1, 1, 4])
                    
                    # Проверка голосовал ли уже текущий пользователь
                    u_id = st.session_state.user_info.get('email', 'admin')
                    if col1.button(f"👍 {m['likes']}", key=f"l_{idx}"):
                        if u_id not in msgs[idx]['users_voted']:
                            msgs[idx]['likes'] += 1
                            msgs[idx]['users_voted'].append(u_id)
                            save_data(MESSAGES_FILE, msgs); st.rerun()
                    
                    if col2.button(f"👎 {m['dislikes']}", key=f"d_{idx}"):
                        if u_id not in msgs[idx]['users_voted']:
                            msgs[idx]['dislikes'] += 1
                            msgs[idx]['users_voted'].append(u_id)
                            save_data(MESSAGES_FILE, msgs); st.rerun()
                    st.divider()
