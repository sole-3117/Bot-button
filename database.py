import sqlite3
from datetime import datetime
from config import DB_PATH

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Foydalanuvchilar jadvali (Tariflar va vaqt mintaqasi bilan)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            plan TEXT DEFAULT 'free', -- 'free', 'pro', 'vip'
            subscription_until TEXT,
            timezone TEXT DEFAULT 'Asia/Tashkent',
            created_at TEXT
        )
    """)
    
    # Vazifalar jadvali (description mavjudligini ta'minlash)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT NOT NULL,
            description TEXT,
            due_datetime TEXT NOT NULL,
            reminder_minutes_before INTEGER DEFAULT 0,
            repeat_type TEXT DEFAULT 'none',
            repeat_interval_days INTEGER,
            status TEXT DEFAULT 'active',
            notified_reminder INTEGER DEFAULT 0,
            notified_due INTEGER DEFAULT 0,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

# Foydalanuvchini ro'yxatga olish yoki yangilash
def register_user(user_id: int, username: str, full_name: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (user_id, username, full_name, plan, created_at)
        VALUES (?, ?, ?, 'free', ?)
        ON CONFLICT(user_id) DO UPDATE SET
            username=excluded.username,
            full_name=excluded.full_name
    """, (user_id, username, full_name, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_user(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

# Foydalanuvchi tarifini o'zgartirish (Admin uchun)
def update_user_plan(user_id: int, plan: str, days: int = 30):
    conn = get_connection()
    cursor = conn.cursor()
    from datetime import timedelta
    until = (datetime.now() + timedelta(days=days)).isoformat()
    cursor.execute("""
        UPDATE users 
        SET plan = ?, subscription_until = ?
        WHERE user_id = ?
    """, (plan, until, user_id))
    conn.commit()
    conn.close()

# Foydalanuvchining faol vazifalari soni (Limitni tekshirish uchun)
def count_active_tasks(user_id: int) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total FROM tasks WHERE user_id = ? AND status = 'active'", (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res["total"] if res else 0

# Admin uchun umumiy statistika
def get_admin_stats():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total_users FROM users")
    total_users = cursor.fetchone()["total_users"]
    
    cursor.execute("SELECT plan, COUNT(*) as count FROM users GROUP BY plan")
    plans = {row["plan"]: row["count"] for row in cursor.fetchall()}
    
    cursor.execute("SELECT COUNT(*) as total_tasks FROM tasks")
    total_tasks = cursor.fetchone()["total_tasks"]
    conn.close()
    return {
        "total_users": total_users,
        "plans": plans,
        "total_tasks": total_tasks
    }
