import logging
from datetime import datetime
import pytz
import os
from telegram.ext import ContextTypes
import database as db

logger = logging.getLogger(__name__)
LOCAL_TZ = pytz.timezone(os.getenv("LOCAL_TZ", "Asia/Tashkent"))

async def check_tasks(context: ContextTypes.DEFAULT_TYPE):
    """Har daqiqada faol vazifalarni tekshiradi va eslatmalarni yuboradi"""
    try:
        now = datetime.now(LOCAL_TZ)
        tasks = db.get_all_active_tasks()

        for task in tasks:
            # due_datetime ISO formatidan parse qilish
            try:
                due_dt = datetime.fromisoformat(task["due_datetime"])
                # Local timezone qo'shish
                if due_dt.tzinfo is None:
                    due_dt = LOCAL_TZ.localize(due_dt)
            except Exception as e:
                logger.error(f"Task {task['task_id']} uchun due_datetime parse qilib bo'lmadi: {e}")
                continue

            # Eslatma vaqti
            if task["reminder_minutes_before"] > 0:
                reminder_time = due_dt.replace(
                    hour=due_dt.hour,
                    minute=due_dt.minute - task["reminder_minutes_before"]
                )
                
                # Vaqt qo'shish kerak bo'lsa (minut < 0)
                if reminder_time.minute < 0:
                    reminder_time = reminder_time.replace(minute=reminder_time.minute + 60, hour=reminder_time.hour - 1)
                
                # Eslatma vaqti keldi va hali yuborilmagan bo'lsa
                if now >= reminder_time and task["notified_reminder"] == 0:
                    await context.bot.send_message(
                        chat_id=task["user_id"],
                        text=f"🔔 Eslatma: '{task['title']}' vazifasi {task['reminder_minutes_before']} daqiqadan so'ng boshlangan bo'ladi."
                    )
                    db.update_task(task["task_id"], notified_reminder=1)
                    logger.info(f"Eslatma yuborildi: task_id={task['task_id']}")

            # Muddat vaqti
            if now >= due_dt and task["notified_due"] == 0:
                await context.bot.send_message(
                    chat_id=task["user_id"],
                    text=f"📌 Vazifa muddati tugadi: '{task['title']}'"
                )
                db.update_task(task["task_id"], notified_due=1)
                logger.info(f"Muddat bildirishnomasi yuborildi: task_id={task['task_id']}")
                
                # Agar takrorlanuvchi bo'lsa, yangi vazifa yaratish
                if task["repeat_type"] == "daily" and task["repeat_interval_days"]:
                    from datetime import timedelta
                    new_due = (due_dt + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S")
                    db.add_task(
                        user_id=task["user_id"],
                        title=task["title"],
                        due_datetime=new_due,
                        description=task["description"],
                        reminder_minutes_before=task["reminder_minutes_before"],
                        repeat_type=task["repeat_type"],
                        repeat_interval_days=task["repeat_interval_days"]
                    )
                    logger.info(f"Takrorlanuvchi vazifa yaratildi: {task['title']}")

    except Exception as e:
        logger.error(f"check_tasks xatosi: {e}", exc_info=True)
