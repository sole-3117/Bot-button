import psycopg2
from psycopg2.extras import DictCursor
from datetime import datetime, timedelta
import logging
from config import PLANS # config.py dagi tariflar ro'yxatini chaqiramiz

logger = logging.getLogger(__name__)

# Baza ulanish parametrlari (Buni .env dan olishingiz mumkin)
DB_CONFIG = {
    "dbname": "kino_planner",
    "user": "postgres",
    "password": "yourpassword",
    "host": "localhost",
    "port": "5432"
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def init_db():
    """Baza va jadvallarni initsializatsiya qilish"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # users jadvaliga yangi ustunlar (plan, limitlar, vaqt) qo'shildi
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username VARCHAR(255),
            plan VARCHAR(50) DEFAULT 'free',
            plan_expire_date TIMESTAMP,
            tasks_limit INT DEFAULT 5,
            voice_limit INT DEFAULT 0,
            sms_limit INT DEFAULT 3,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # tasks jadvali (avvalgi kodingizdagi kabi)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            user_id BIGINT REFERENCES users(user_id),
            title VARCHAR(255),
            description TEXT,
            date_val DATE,
            time_val TIME,
            status VARCHAR(50) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()
    logger.info("📦 Ma'lumotlar bazasi muvaffaqiyatli initsializatsiya qilindi.")

def register_user(user_id: int, username: str):
    """Yangi foydalanuvchini ro'yxatdan o'tkazish (Welcome Bonus bilan)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Agar foydalanuvchi yo'q bo'lsa, 'free' tarif bilan qo'shadi (3 ta SMS bonus)
    cursor.execute("""
        INSERT INTO users (user_id, username, plan, tasks_limit, voice_limit, sms_limit)
        VALUES (%s, %s, 'free', %s, %s, %s)
        ON CONFLICT (user_id) DO NOTHING
    """, (user_id, username, PLANS['free']['max_tasks'], PLANS['free']['max_voice'], PLANS['free']['max_sms']))
    
    conn.commit()
    cursor.close()
    conn.close()

def upgrade_user_plan(user_id: int, plan_name: str):
    """Foydalanuvchi obuna sotib olganda limitlarini yangilash"""
    if plan_name not in PLANS:
        return False
        
    plan_data = PLANS[plan_name]
    expire_date = datetime.now() + timedelta(days=plan_data['duration_days'])
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE users 
        SET plan = %s, 
            plan_expire_date = %s, 
            tasks_limit = %s, 
            voice_limit = %s, 
            sms_limit = %s
        WHERE user_id = %s
    """, (
        plan_name, 
        expire_date, 
        plan_data['max_tasks'], 
        plan_data['max_voice'], 
        plan_data['max_sms'], 
        user_id
    ))
    
    conn.commit()
    cursor.close()
    conn.close()
    return True

def get_user_limits(user_id: int) -> dict:
    """Foydalanuvchining hozirgi tarifi va limitlarini olish"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)
    
    cursor.execute("""
        SELECT plan, plan_expire_date, tasks_limit, voice_limit, sms_limit 
        FROM users 
        WHERE user_id = %s
    """, (user_id,))
    
    user_data = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if user_data:
        # Agar vaqt tugagan bo'lsa, avtomatik Free tarifiga tushirish logikasi shu yerda ham ishlashi mumkin
        if user_data['plan'] != 'free' and user_data['plan_expire_date'] and datetime.now() > user_data['plan_expire_date']:
            upgrade_user_plan(user_id, 'free')
            return get_user_limits(user_id) # Qaytadan yuklash
            
        return dict(user_data)
    return None

def decrement_voice_limit(user_id: int) -> bool:
    """Ovozli xabar ishlatilganda limitdan 1 ta ayirish"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE users 
        SET voice_limit = voice_limit - 1 
        WHERE user_id = %s AND voice_limit > 0
        RETURNING voice_limit
    """, (user_id,))
    
    result = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()
    
    return result is not None # Agar limit > 0 bo'lsa True qaytadi

def decrement_sms_limit(user_id: int) -> bool:
    """SMS ishlatilganda limitdan 1 ta ayirish"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE users 
        SET sms_limit = sms_limit - 1 
        WHERE user_id = %s AND sms_limit > 0
        RETURNING sms_limit
    """, (user_id,))
    
    result = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()
    
    return result is not None

def add_task(user_id, title, description, date_val, time_val, status="pending"):
    """Vazifani bazaga saqlash"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO tasks (user_id, title, description, date_val, time_val, status)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (user_id, title, description, date_val, time_val, status))
    conn.commit()
    cursor.close()
    conn.close()
