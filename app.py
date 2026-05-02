import streamlit as st
import os
import json
import smtplib
import random
from email.mime.text import MIMEText
from yt_dlp import YoutubeDL
from datetime import datetime

# --- 1. КОНФИГУРАЦИЯ И НАСТРОЙКИ ---
SMTP_SERVER, SMTP_PORT = "://gmail.com", 587
SENDER_EMAIL = "isa.murad.ibaanah@gmail.com"
# Пароль берется из Secrets (google_password)
SENDER_PASSWORD = st.secrets.get('google_password', "")

DOWNLOAD_DIR = "/tmp"
DB_FILE, BAN_FILE, MSG_FILE = "users_db.json", "banned_users.json", "messages.json"
SECRET_CODE, ADMIN_PASSWORD = "27032012", "2dsfjqHFugfHUgh219-Hfhwgj@"

# Инициализация системных файлов
for f in [DB_FILE, BAN_FILE, MSG_FILE]:
    if not os.path.exists(f):
        with open(f, "w", encoding="utf-8") as file:
            json.dump([] if f != DB_FILE else {}, file)

# --- 2. СИСТЕМНЫЕ ФУНКЦИИ ---
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

def send_otp(email):
    otp = str(random.randint(100000, 999999))
    msg = MIMEText(f"Ваш код подтверждения для Video Downloader: {otp}")
    msg['Subject'], msg['From'], msg['To'] = 'Код подтверждения', SENDER_EMAIL, email
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, email, msg.as_string())
        server.quit()
        return otp
    except Exception as e:
        st.error(f"Ошибка почтового сервера: {e}")
        return None

# --- 3. УПРАВЛЕНИЕ СОСТОЯНИЕМ СЕССИИ ---
if 'auth_step' not in st.session_state: st.session_state.auth_step = 'main_gate'
if 'user_info' not in st.session_state: st.session_state.user_info = None
if 'formats' not in st.session_state: st.session_state.formats = None
if 'url_buffer' not in st.session_state: st.session_state.url_buffer = ""

st.set_page_config(page_title="Video Downloader", page_icon="📲", layout="centered")

# --- 4. ЭКРАНЫ АВТОРИЗАЦИИ ---

# Шаг 1: Проверка секретного кода сервера
if st.session_state.auth_step == 'main_gate':
    st.title("🔒 Вход на сервер")
    t1, t2 = st.tabs(["🔑 Пользователь", "🛠 Организатор"])
    with t1:
        with st.form("gate"):
            c = st.text_input("Введите секретный код доступа:", type="password")
            if st.form_submit_button("Подтвердить"):
                if c == SECRET_CODE: 
                    st.session_state.auth_step = 'login_or_reg'
                    st.rerun()
                else: st.error("Код неверный")
    with t2:
        with st.form("admin_gate"):
            ap = st.text_input("Пароль организатора:", type="password")
            if st.form_submit_button("Админ-вход"):
                if ap == ADMIN_PASSWORD:
                    st.session_state.user_info = {"name": "Админ", "role": "admin"}
                    st.session_state.auth_step = 'app'
                    st.rerun()

# Шаг 2: Вход / Регистрация / Восстановление
elif st.session_state.auth_step == 'login_or_reg':
    st.title("👤 Аккаунт")
    users, banned = load_data(DB_FILE), load_data(BAN_FILE)
    choice = st.radio("Выберите действие:", ["Вход", "Регистрация", "Забыл пароль"], horizontal=True)
    
    with st.form("auth_main"):
        em = st.text_input("Email:").lower().strip()
        pw = st.text_input("Пароль:", type="password") if choice == "Вход" else ""
        if st.form_submit_button("Далее"):
            if not em: st.error("Заполните поле Email")
            elif em in banned: st.error("Ваш доступ заблокирован администратором")
            elif choice == "Вход":
                if em in users and isinstance(users[em], dict) and users[em].get('pass') == pw:
                    st.session_state.user_info = {"name": users[em]['name'], "email": em, "role": "user"}
                    st.session_state.auth_step = 'app'
                    st.rerun()
                else: st.error("Неверный email или пароль")
            else:
                with st.spinner("Отправка кода на почту..."):
                    otp = send_otp(em)
                    if otp:
                        st.session_state.temp_email, st.session_state.otp = em, otp
                        st.session_state.auth_step = 'verify' if choice == "Регистрация" else 'reset'
                        st.rerun()

# Шаг 3: Верификация кода и установка пароля
elif st.session_state.auth_step in ['verify', 'reset']:
    is_reg = st.session_state.auth_step == 'verify'
    st.title("📩 " + ("Регистрация" if is_reg else "Сброс пароля"))
    with st.form("otp_finalize"):
        st.write(f"Код отправлен на {st.session_state.temp_email}")
        c = st.text_input("Код из письма:")
        n = st.text_input("Ваше имя (Ник):") if is_reg else ""
        p1 = st.text_input("Придумайте пароль:", type="password")
        p2 = st.text_input("Повторите пароль:", type="password")
        if st.form_submit_button("Завершить"):
            if c == st.session_state.otp and p1 == p2 and len(p1) > 3:
                users = load_data(DB_FILE)
                name_val = n if is_reg else users.get(st.session_state.temp_email, {}).get('name', 'User')
                users[st.session_state.temp_email] = {"name": name_val, "pass": p1}
                save_data(DB_FILE, users)
                st.success("Успешно! Теперь войдите в аккаунт.")
                st.session_state.auth_step = 'login_or_reg'
                st.rerun()
            else: st.error("Ошибка: проверьте код или совпадение паролей (мин. 4 символа)")

# --- 5. ОСНОВНОЙ ИНТЕРФЕЙС ПРИЛОЖЕНИЯ ---
elif st.session_state.auth_step == 'app':
    is_admin = st.session_state.user_info.get('role') == 'admin'
    
    # БОКОВАЯ ПАНЕЛЬ (САЙДБАР)
    with st.sidebar:
        st.header("📲 Меню")
        st.write(f"Привет, **{st.session_state.user_info['name']}**!")
        
        if not is_admin:
            if st.button("⚙️ Сменить пароль", use_container_width=True):
                otp = send_otp(st.session_state.user_info['email'])
                if otp:
                    st.session_state.temp_email, st.session_state.otp = st.session_state.user_info['email'], otp
                    st.session_state.auth_step = 'reset'
                    st.rerun()
                    
        if st.button("🚪 Выйти из системы", use_container_width=True):
            st.session_state.clear()
            st.rerun()
        
        if is_admin:
            st.divider()
            st.subheader("🛠 Админ-панель")
            u_db, b_db = load_data(DB_FILE), load_data(BAN_FILE)
            
            if not u_db: st.info("Пользователей пока нет")
            for email, data in u_db.items():
                name = data.get('name', 'User') if isinstance(data, dict) else "Старый формат"
                c1, c2 = st.columns([3, 1])
                c1.markdown(f"**{name}**\n<small>{email}</small>", unsafe_allow_html=True)
                
                # Кнопка быстрой блокировки
                is_banned = email in b_db
                if c2.button("🚫" if not is_banned else "✅", key=f"btn_{email}"):
                    if is_banned: b_db.remove(email)
                    else: b_db.append(email)
                    save_data(BAN_FILE, b_db)
                    st.rerun()
            
            if st.button("🗑 Очистить кэш видео", use_container_width=True):
                for f in os.listdir(DOWNLOAD_DIR):
                    if f.endswith((".mp4", ".mp3", ".part", ".webm")):
                        os.remove(os.path.join(DOWNLOAD_DIR, f))
                st.success("Кэш очищен")

    # ОСНОВНОЙ КОНТЕНТ (ВКЛАДКИ)
    t_dl, t_chat = st.tabs(["📥 Загрузчик", "💬 Чат и новости"])
    
    with t_dl:
        st.title("📲 Video Downloader")
        url = st.text_input("Вставьте ссылку на видео (YouTube/VK):", placeholder="https://...")
        
        # Сброс форматов при новой ссылке
        if url != st.session_state.url_buffer:
            st.session_state.url_buffer = url
            st.session_state.formats = None

        if url and not st.session_state.formats:
            if st.button("🔍 Анализировать качество", use_container_width=True):
                with st.spinner("Анализ доступных форматов..."):
                    try:
                        ydl_params = {
                            'quiet': True, 
                            'no_warnings': True,
                            'http_headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'}
                        }
                        with YoutubeDL(ydl_params) as ydl:
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
                            st.session_state.formats = opts
                            st.rerun()
                    except Exception as e: st.error(f"Не удалось распознать видео: {e}")

        if st.session_state.formats:
            choice = st.selectbox("Выберите доступное качество:", list(st.session_state.formats.keys()))
            if st.button("🚀 НАЧАТЬ СКАЧИВАНИЕ", type="primary", use_container_width=True):
                f_data = st.session_state.formats[choice]
                try:
                    with st.spinner("Загрузка на сервер..."):
                        ydl_opts = {
                            'format': f"{f_data['id']}+bestaudio/best" if f_data['type'] == 'v' else 'bestaudio/best',
                            'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
                            'nocheckcertificate': True,
                        }
                        if f_data['type'] == 'a':
                            ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3'}]
                        
                        with YoutubeDL(ydl_opts) as ydl:
                            info = ydl.extract_info(url, download=True)
                            path = ydl.prepare_filename(info)
                            if f_data['type'] == 'a': path = os.path.splitext(path)[0] + ".mp3"
                            
                            with open(path, "rb") as file_bytes:
                                st.success("✅ Файл готов!")
                                st.download_button("💾 СОХРАНИТЬ НА УСТРОЙСТВО", file_bytes, file_name=os.path.basename(path), use_container_width=True)
                            os.remove(path)
                except Exception as e: st.error(f"Ошибка загрузки: {e}")
            
            if st.button("🔄 Сбросить ссылку"):
                st.session_state.formats = None
                st.session_state.url_buffer = ""
                st.rerun()

    with t_chat:
        st.header("💬 Чат и объявления")
        msgs = load_data(MSG_FILE)
        
        if is_admin:
            with st.expander("📝 Написать сообщение всем пользователям"):
                txt = st.text_area("Ваш текст:")
                if st.button("Опубликовать", use_container_width=True):
                    if txt:
                        msgs.append({"text": txt, "date": datetime.now().strftime("%d.%m %H:%M"), "likes": 0, "dislikes": 0, "voted": []})
                        save_data(MSG_FILE, msgs)
                        st.rerun()
        
        if not msgs: st.info("Здесь пока пусто. Ожидайте новостей от администратора!")
        for i, m in enumerate(reversed(msgs)):
            idx = len(msgs) - 1 - i
            st.markdown(f"""
                <div style="background: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b; margin-bottom: 5px;">
                    <small style="color: gray;">{m['date']}</small><br><b>{m['text']}</b>
                </div>
            """, unsafe_allow_html=True)
            
            c1, c2, _ = st.columns([1, 1, 4])
            uid = st.session_state.user_info.get('email', 'admin')
            if c1.button(f"👍 {m['likes']}", key=f"l{idx}"):
                if uid not in m['voted']:
                    msgs[idx]['likes'] += 1; msgs[idx]['voted'].append(uid)
                    save_data(MSG_FILE, msgs); st.rerun()
            if c2.button(f"👎 {m['dislikes']}", key=f"d{idx}"):
                if uid not in m['voted']:
                    msgs[idx]['dislikes'] += 1; msgs[idx]['voted'].append(uid)
                    save_data(MSG_FILE, msgs); st.rerun()
            st.divider()
