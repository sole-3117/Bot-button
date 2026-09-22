import sqlite3
from datetime import datetime
from contextlib import contextmanager
from config import DB_PATH


def init_db():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                due_datetime TEXT NOT NULL,
                reminder_minutes_before INTEGER DEFAULT 0,
                repeat_type TEXT DEFAULT 'none',
                repeat_interval_days INTEGER,
                status TEXT DEFAULT 'active',
                notified_reminder INTEGER DEFAULT 0,
                notified_due INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        conn.commit()


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def add_user(user_id: int, username: str, first_name: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
            (user_id, username, first_name),
        )
        conn.commit()


def add_task(user_id: int, title: str, due_datetime: str, reminder_minutes_before: int = 0,
             repeat_type: str = "none", repeat_interval_days: int = None, description: str = None):
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO tasks (user_id, title, description, due_datetime,
               reminder_minutes_before, repeat_type, repeat_interval_days)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user_id, title, description, due_datetime, reminder_minutes_before,
             repeat_type, repeat_interval_days),
        )
        conn.commit()
        return cur.lastrowid


def get_task(task_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
        return dict(row) if row else None


def get_user_tasks(user_id: int, status: str = "active"):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM tasks WHERE user_id = ? AND status = ? ORDER BY due_datetime ASC",
            (user_id, status),
        ).fetchall()
        return [dict(r) for r in rows]


def update_task(task_id: int, **fields):
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [task_id]
    with get_conn() as conn:
        conn.execute(f"UPDATE tasks SET {set_clause} WHERE task_id = ?", values)
        conn.commit()


def delete_task(task_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM tasks WHERE task_id = ?", (task_id,))
        conn.commit()


def complete_task(task_id: int):
    with get_conn() as conn:
        conn.execute(
            "UPDATE tasks SET status = 'done', completed_at = ? WHERE task_id = ?",
            (datetime.now().isoformat(), task_id),
        )
        conn.commit()


def get_all_active_tasks():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM tasks WHERE status = 'active'").fetchall()
        return [dict(r) for r in rows]
