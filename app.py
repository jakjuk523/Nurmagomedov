import streamlit as st
import os
import json
import smtplib
import random
from email.mime.text import MIMEText
from yt_dlp import YoutubeDL
from datetime import datetime

# --- 1. КОНФИГУРАЦИЯ ---
SMTP_SERVER = "://gmail.com"
SMTP_IP = "74.125.131.108" # Резервный IP для стабильности
SMTP_PORT = 587
SENDER_EMAIL = "isa.murad.ibaanah@gmail.com"
SENDER_PASSWORD = st.secrets.get('google_password', "")

DOWNLOAD_DIR = "/tmp"
DB_FILE, BAN_FILE, MSG_FILE = "users_db.json", "banned_users.json", "messages.json"
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
            if not c: return [] if file != DB_FILE else {}
            return json.loads(c)
    except: return [] if file != DB_FILE else {}

def save_data(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def send_otp(email):
    otp = str(random.randint(100000, 999999))
    msg = MIMEText(f"Ваш код подтверждения: {otp}")
    msg['Subject'], msg['From'], msg['To'] = 'Код подтверждения', SENDER_EMAIL, email
    for target in [SMTP_SERVER, SMTP_IP]:
        try:
            server = smtplib.SMTP(target, SMTP_PORT, timeout=15)
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

# --- 4. АВТОРИЗАЦИЯ ---
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
            ap = st.text_input("Пароль организатора:", type="password")
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
        c = st.text_input("Код из письма:")
        n = st.text_input("Имя:") if is_reg else ""
        p1 = st.text_input("Новый пароль:", type="password")
        p2 = st.text_input("Повторите:", type="password")
        if st.form_submit_button("Завершить"):
            if c == st.session_state.get('otp') and p1 == p2 and len(p1) > 3:
                users = load_data(DB_FILE)
                name_val = n if is_reg else users.get(st.session_state.temp_email, {}).get('name', 'User')
                users[st.session_state.temp_email] = {"name": name_val, "pass": p1}
                save_data(DB_FILE, users)
                st.success("Готово!"); st.session_state.auth_step = 'login_or_reg'; st.rerun()
            else: st.error("Ошибка в данных")

# --- 5. ПРИЛОЖЕНИЕ ---
elif st.session_state.auth_step == 'app':
    is_admin = st.session_state.user_info.get('role') == 'admin'
    with st.sidebar:
        st.write(f"👤 **{st.session_state.user_info['name']}**")
        
        # Кнопка смены пароля для юзеров
        if not is_admin:
            if st.button("⚙️ Сменить пароль"):
                otp = send_otp(st.session_state.user_info['email'])
                if otp:
                    st.session_state.temp_email, st.session_state.otp = st.session_state.user_info['email'], otp
                    st.session_state.auth_step = 'reset'; st.rerun()
        
        if st.button("🚪 Выйти"): st.session_state.clear(); st.rerun()
        
        if is_admin:
            st.divider()
            u_db, b_db = load_data(DB_FILE), load_data(BAN_FILE)
            for email, data in u_db.items():
                name = data.get('name', 'User') if isinstance(data, dict) else "Old"
                c1, c2 = st.columns()
                c1.write(f"**{name}**\n{email}")
                if c2.button("🚫" if email not in b_db else "✅", key=email):
                    if email in b_db: b_db.remove(email)
                    else: b_db.append(email)
                    save_data(BAN_FILE, b_db); st.rerun()

    t_dl, t_chat = st.tabs(["📥 Загрузка", "💬 Сообщения"])
    
    with t_dl:
        st.title("📲 Video Downloader")
        url = st.text_input("Ссылка:")
        if url != st.session_state.url_buffer:
            st.session_state.url_buffer, st.session_state.formats = url, None

        if url and not st.session_state.formats:
            if st.button("🔍 Анализ"):
                with st.spinner("Анализирую..."):
                    try:
                        with YoutubeDL({'quiet':True, 'nocheckcertificate': True}) as ydl:
                            info = ydl.extract_info(url, download=False)
                            opts = {}
                            for f in info.get('formats', []):
                                if f.get('height'):
                                    label = f"{f['height']}p ({f['ext']})"
                                    opts[label] = {'id': f['format_id'], 'type': 'v'}
                                elif f.get('acodec')!='none' and f.get('vcodec')=='none':
                                    opts["🎵 MP3 Аудио"] = {'id': f['format_id'], 'type': 'a'}
                            st.session_state.formats = opts; st.rerun()
                    except Exception as e: st.error(f"Ошибка: {e}")

        if st.session_state.formats:
            choice = st.selectbox("Выберите качество:", list(st.session_state.formats.keys()))
            if st.button("🚀 СКАЧАТЬ", type="primary"):
                try:
                    f_info = st.session_state.formats[choice]
                    with st.spinner("Загрузка..."):
                        ydl_opts = {
                            'format': f_info['id']+'+bestaudio/best' if f_info['type']=='v' else 'bestaudio/best',
                            'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
                            'nocheckcertificate': True
                        }
                        if f_info['type']=='a':
                            ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3'}]
                        
                        with YoutubeDL(ydl_opts) as ydl:
                            info = ydl.extract_info(url, download=True)
                            path = ydl.prepare_filename(info)
                            if f_info['type']=='a': path = os.path.splitext(path)[0] + ".mp3"
                            with open(path, "rb") as f:
                                st.download_button("💾 Сохранить файл", f, file_name=os.path.basename(path))
                            os.remove(path)
                except Exception as e: st.error(f"Ошибка: {e}")
            if st.button("🔄 Сброс"): st.session_state.formats = None; st.rerun()

    with t_chat:
        st.header("💬 Сообщения и Обсуждения")
        msgs = load_data(MSG_FILE)
        
        if is_admin:
            with st.expander("📝 Написать сообщение"):
                txt = st.text_area("Текст:")
                if st.button("Отправить"):
                    msgs.append({
                        "text": txt, 
                        "date": datetime.now().strftime("%d.%m %H:%M"), 
                        "likes": 0, "dislikes": 0, "voted": [],
                        "comments": []
                    })
                    save_data(MSG_FILE, msgs); st.rerun()
        
        for i, m in enumerate(reversed(msgs)):
            idx = len(msgs) - 1 - i
            st.markdown(f"<div style='background:#f0f2f6;padding:15px;border-radius:10px;border-left:5px solid red;'><b>{m['text']}</b><br><small>{m['date']}</small></div>", unsafe_allow_html=True)
            
            c1, c2, c3 = st.columns([1, 1, 2])
            uid = st.session_state.user_info.get('email', 'admin')
            
            if c1.button(f"👍 {m['likes']}", key=f"l{idx}"):
                if uid not in m['voted']:
                    msgs[idx]['likes'] += 1; msgs[idx]['voted'].append(uid); save_data(MSG_FILE, msgs); st.rerun()
            
            if c2.button(f"👎 {m['dislikes']}", key=f"d{idx}"):
                if uid not in m['voted']:
                    msgs[idx]['dislikes'] += 1; msgs[idx]['voted'].append(uid); save_data(MSG_FILE, msgs); st.rerun()
            
            # --- СИСТЕМА КОММЕНТАРИЕВ ---
            with c3.expander(f"💬 Комменты ({len(m.get('comments', []))})"):
                for comm in m.get('comments', []):
                    st.markdown(f"**{comm['user']}**: {comm['text']} <small style='color:gray'>{comm['time']}</small>", unsafe_allow_html=True)
                
                new_comm = st.text_input("Напишите ответ...", key=f"in{idx}")
                if st.button("Ответить", key=f"btn_c{idx}"):
                    if new_comm:
                        if "comments" not in msgs[idx]: msgs[idx]["comments"] = []
                        msgs[idx]["comments"].append({
                            "user": st.session_state.user_info['name'],
                            "text": new_comm,
                            "time": datetime.now().strftime("%H:%M")
                        })
                        save_data(MSG_FILE, msgs); st.rerun()
            st.divider()
