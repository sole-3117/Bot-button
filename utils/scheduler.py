from datetime import datetime, timedelta
from telegram.ext import ContextTypes
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import database as db


def build_repeat_next(task: dict) -> str | None:
    """Keyingi takrorlanish sanasini hisoblaydi, yoki None (takror yo'q bo'lsa)."""
    due = datetime.fromisoformat(task["due_datetime"])
    rtype = task["repeat_type"]

    if rtype == "daily":
        return (due + timedelta(days=1)).isoformat()
    elif rtype == "weekly":
        return (due + timedelta(weeks=1)).isoformat()
    elif rtype == "monthly":
        # oddiy yondashuv: 30 kun qo'shamiz
        return (due + timedelta(days=30)).isoformat()
    elif rtype == "custom" and task.get("repeat_interval_days"):
        return (due + timedelta(days=task["repeat_interval_days"])).isoformat()
    return None


async def check_tasks(context: ContextTypes.DEFAULT_TYPE):
    """Har daqiqada ishga tushadi: eslatma va muddat vaqtlarini tekshiradi."""
    now = datetime.now()
    tasks = db.get_all_active_tasks()

    for task in tasks:
        due = datetime.fromisoformat(task["due_datetime"])
        task_id = task["task_id"]
        chat_id = task["user_id"]

        # Oldindan eslatma
        if task["reminder_minutes_before"] and not task["notified_reminder"]:
            reminder_time = due - timedelta(minutes=task["reminder_minutes_before"])
            if now >= reminder_time and now < due:
                try:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"⏰ Eslatma: \"{task['title']}\"\n"
                             f"Muddat: {due.strftime('%d.%m.%Y %H:%M')} "
                             f"({task['reminder_minutes_before']} daqiqadan keyin)",
                    )
                except Exception:
                    pass
                db.update_task(task_id, notified_reminder=1)

        # Muddat yetganda
        if now >= due and not task["notified_due"]:
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Toʻlash", callback_data=f"complete_{task_id}")]
            ])
            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"🔔 Vazifa vaqti keldi: \"{task['title']}\"",
                    reply_markup=keyboard,
                )
            except Exception:
                pass
            db.update_task(task_id, notified_due=1)

            # Takrorlanuvchi vazifa bo'lsa, keyingisini yaratamiz
            next_due = build_repeat_next(task)
            if next_due:
                db.add_task(
                    user_id=task["user_id"],
                    title=task["title"],
                    due_datetime=next_due,
                    reminder_minutes_before=task["reminder_minutes_before"],
                    repeat_type=task["repeat_type"],
                    repeat_interval_days=task["repeat_interval_days"],
                    description=task["description"],
                )
