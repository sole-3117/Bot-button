from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
from config import DATABASE_URL, LOCAL_TZ

def get_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            plan TEXT DEFAULT 'free',
            subscription_until TEXT,
            created_at TEXT
        );
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            task_id SERIAL PRIMARY KEY,
            user_id BIGINT,
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
        );
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS payment_requests (
            req_id SERIAL PRIMARY KEY,
            user_id BIGINT,
            plan TEXT,
            receipt_file_id TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT
        );
    """)
    conn.commit()
    conn.close()

def register_user(user_id: int, username: str, full_name: str):
    conn = get_connection()
    c = conn.cursor()
    now_str = datetime.now(LOCAL_TZ).strftime("%Y-%m-%d %H:%M:%S")
    c.execute("""
        INSERT INTO users (user_id, username, full_name, plan, created_at)
        VALUES (%s, %s, %s, 'free', %s)
        ON CONFLICT(user_id) DO UPDATE SET
            username = EXCLUDED.username,
            full_name = EXCLUDED.full_name;
    """, (user_id, username, full_name, now_str))
    conn.commit()
    conn.close()

def get_user(user_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = %s;", (user_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def count_active_tasks(user_id: int) -> int:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as total FROM tasks WHERE user_id = %s AND status = 'active';", (user_id,))
    res = c.fetchone()
    conn.close()
    return res["total"] if res else 0

def add_payment_request(user_id: int, plan: str, receipt_file_id: str) -> int:
    conn = get_connection()
    c = conn.cursor()
    now_str = datetime.now(LOCAL_TZ).strftime("%Y-%m-%d %H:%M:%S")
    c.execute("""
        INSERT INTO payment_requests (user_id, plan, receipt_file_id, status, created_at)
        VALUES (%s, %s, %s, 'pending', %s) RETURNING req_id;
    """, (user_id, plan, receipt_file_id, now_str))
    req_id = c.fetchone()["req_id"]
    conn.commit()
    conn.close()
    return req_id

def get_payment_request(req_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM payment_requests WHERE req_id = %s;", (req_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def approve_payment(req_id: int, days: int = 30):
    conn = get_connection()
    c = conn.cursor()
    req = get_payment_request(req_id)
    if not req or req["status"] != "pending":
        conn.close()
        return None
    
    until = (datetime.now(LOCAL_TZ) + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    c.execute("UPDATE users SET plan = %s, subscription_until = %s WHERE user_id = %s;", (req["plan"], until, req["user_id"]))
    c.execute("UPDATE payment_requests SET status = 'approved' WHERE req_id = %s;", (req_id,))
    conn.commit()
    conn.close()
    return req

def reject_payment(req_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE payment_requests SET status = 'rejected' WHERE req_id = %s;", (req_id,))
    conn.commit()
    conn.close()

def add_task(user_id, title, description, due_datetime, reminder_minutes_before, repeat_type, repeat_interval_days):
    conn = get_connection()
    c = conn.cursor()
    now_str = datetime.now(LOCAL_TZ).strftime("%Y-%m-%d %H:%M:%S")
    c.execute("""
        INSERT INTO tasks (user_id, title, description, due_datetime, reminder_minutes_before, repeat_type, repeat_interval_days, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING task_id;
    """, (user_id, title, description, due_datetime, reminder_minutes_before, repeat_type, repeat_interval_days, now_str))
    task_id = c.fetchone()["task_id"]
    conn.commit()
    conn.close()
    return task_id

def get_user_tasks(user_id: int, status: str = "active"):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM tasks WHERE user_id = %s AND status = %s ORDER BY due_datetime ASC;", (user_id, status))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def complete_task(task_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE tasks SET status = 'done' WHERE task_id = %s;", (task_id,))
    conn.commit()
    conn.close()

def delete_task(task_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE task_id = %s;", (task_id,))
    conn.commit()
    conn.close()

def get_all_active_tasks():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM tasks WHERE status = 'active';")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def update_task(task_id: int, **kwargs):
    conn = get_connection()
    c = conn.cursor()
    cols = ", ".join([f"{k} = %s" for k in kwargs.keys()])
    vals = list(kwargs.values()) + [task_id]
    c.execute(f"UPDATE tasks SET {cols} WHERE task_id = %s;", vals)
    conn.commit()
    conn.close()

def get_admin_stats():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as total_users FROM users;")
    total_users = c.fetchone()["total_users"]
    
    c.execute("SELECT plan, COUNT(*) as count FROM users GROUP BY plan;")
    plans = {row["plan"]: row["count"] for row in c.fetchall()}
    
    c.execute("SELECT COUNT(*) as total_tasks FROM tasks;")
    total_tasks = c.fetchone()["total_tasks"]
    conn.close()
    return {
        "total_users": total_users,
        "plans": plans,
        "total_tasks": total_tasks
    }
