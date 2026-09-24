import sys
import os
from datetime import datetime, timedelta
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import LOCAL_TZ

# Ichki papkadan asosiy papka modullarini to'g'ri ko'rish uchun
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database as db

logger = logging.getLogger(__name__)

def build_repeat_next(task: dict) -> str | None:
    due = datetime.fromisoformat(task["due_datetime"])
    rtype = task["repeat_type"]

    if rtype == "daily":
        return (due + timedelta(days=1)).isoformat()
    elif rtype == "weekly":
        return (due + timedelta(weeks=1)).isoformat()
    elif rtype == "monthly":
        return (due + timedelta(days=30)).isoformat()
    elif rtype == "custom" and task.get("repeat_interval_days"):
        return (due + timedelta(days=task["repeat_interval_days"])).isoformat()
    return None

async def check_tasks(app):
    now = datetime.now(LOCAL_TZ).replace(tzinfo=None)
    tasks = db.get_all_active_tasks()

    for task in tasks:
        due = datetime.fromisoformat(task["due_datetime"])
        task_id = task["task_id"]
        chat_id = task["user_id"]

        # Oldindan eslatma yuborish
        if task.get("reminder_minutes_before") and not task.get("notified_reminder"):
            reminder_time = due - timedelta(minutes=task["reminder_minutes_before"])
            if reminder_time <= now < due:
                try:
                    await app.bot.send_message(
                        chat_id=chat_id,
                        text=f"⏰ Eslatma: \"{task['title']}\"\n"
                             f"Muddat: {due.strftime('%d.%m.%Y %H:%M')} "
                             f"({task['reminder_minutes_before']} daqiqadan keyin)",
                    )
                    db.update_task(task_id, notified_reminder=1)
                except Exception as e:
                    logger.error(f"Eslatma yuborishda xato: {e}")

        # Muddat yetganda eslatish
        if now >= due and not task.get("notified_due"):
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Bajarildi", callback_data=f"complete_{task_id}")]
            ])
            try:
                await app.bot.send_message(
                    chat_id=chat_id,
                    text=f"🔔 Vazifa vaqti keldi: \"{task['title']}\"",
                    reply_markup=keyboard,
                )
                db.update_task(task_id, notified_due=1)
            except Exception as e:
                logger.error(f"Muddat xabarida xato: {e}")

            # Takrorlanish bo'lsa yangi vazifa yaratish
            next_due = build_repeat_next(task)
            if next_due:
                db.add_task(
                    user_id=task["user_id"],
                    title=task["title"],
                    description=task.get("description", ""),
                    due_datetime=next_due,
                    reminder_minutes_before=task.get("reminder_minutes_before", 0),
                    repeat_type=task.get("repeat_type", "none"),
                    repeat_interval_days=task.get("repeat_interval_days"),
                )
