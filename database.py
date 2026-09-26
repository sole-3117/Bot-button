def complete_task(task_id: int, user_id: int) -> bool:
    """Faqat o'z egasi bo'lgan vazifani 'done' holatiga o'tkazish."""
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "UPDATE tasks SET status = 'done' WHERE task_id = %s AND user_id = %s;",
        (task_id, user_id)
    )
    rows_affected = c.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0


def delete_task(task_id: int, user_id: int) -> bool:
    """Faqat o'z egasi bo'lgan vazifani bazadan o'chirish."""
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "DELETE FROM tasks WHERE task_id = %s AND user_id = %s;",
        (task_id, user_id)
    )
    rows_affected = c.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0
