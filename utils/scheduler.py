from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import logging
from telegram.ext import ContextTypes
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import database as db
from config import TIMEZONE

logger = logging.getLogger(__name__)

# Timezone obyektini yaratib olamiz (masalan, Asia/Tashkent)
LOCAL_TZ = ZoneInfo(TIMEZONE if TIMEZONE else "Asia/Tashkent")


def build_repeat_next(task: dict) -> str | None:
    """Keyingi takrorlanish sanasini hisoblaydi, yoki None (takror yo'q bo'lsa)."""
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


async def check_tasks(context: ContextTypes.DEFAULT_TYPE):
    """Har daqiqada ishga tushadi: eslatma va muddat vaqtlarini tekshiradi."""
    # Server vaqti emas, aynan ko'rsatilgan mintaqa (Toshkent) vaqtini olamiz
    # va bazadagi naive datetime bilan to'g'ri solishtirish uchun tzinfo ni olib tashlaymiz
    now = datetime.now(LOCAL_TZ).replace(tzinfo=None)
    tasks = db.get_all_active_tasks()

    for task in tasks:
        due = datetime.fromisoformat(task["due_datetime"])
        task_id = task["task_id"]
        chat_id = task["user_id"]

        # Oldindan eslatma
        if task.get("reminder_minutes_before") and not task.get("notified_reminder"):
            reminder_time = due - timedelta(minutes=task["reminder_minutes_before"])
            if now >= reminder_time and now < due:
                try:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"⏰ Eslatma: \"{task['title']}\"\n"
                             f"Muddat: {due.strftime('%d.%m.%Y %H:%M')} "
                             f"({task['reminder_minutes_before']} daqiqadan keyin)",
                    )
                    db.update_task(task_id, notified_reminder=1)
                except Exception as e:
                    logger.error(f"Eslatma yuborishda xato (task_id: {task_id}): {e}")

        # Muddat yetganda
        if now >= due and not task.get("notified_due"):
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Bajarildi", callback_data=f"complete_{task_id}")]
            ])
            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"🔔 Vazifa vaqti keldi: \"{task['title']}\"",
                    reply_markup=keyboard,
                )
                db.update_task(task_id, notified_due=1)
            except Exception as e:
                logger.error(f"Vazifa bildirishnomasini yuborishda xato (task_id: {task_id}): {e}")

            # Takrorlanuvchi vazifa bo'lsa, keyingisini yaratamiz
            next_due = build_repeat_next(task)
            if next_due:
                db.add_task(
                    user_id=task["user_id"],
                    title=task["title"],
                    due_datetime=next_due,
                    reminder_minutes_before=task.get("reminder_minutes_before", 0),
                    repeat_type=task.get("repeat_type", "none"),
                    repeat_interval_days=task.get("repeat_interval_days"),
                    description=task.get("description", ""),
                )
