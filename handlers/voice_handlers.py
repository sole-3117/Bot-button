import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

from services.speech_to_text import transcribe_voice
from services.ai_extractor import extract_task_json
from config import LOCAL_TZ
import database as db

logger = logging.getLogger(__name__)

async def process_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    user_id = update.effective_user.id

    # 1. Limitlarni tekshirish
    user = db.get_user(user_id)
    if not user:
        db.register_user(user_id, update.effective_user.username or "", update.effective_user.full_name or "")
        user = db.get_user(user_id)

    if user.get("voice_limit", 0) <= 0:
        await message.reply_text(
            "🎙 Ovozli yordamchi limiti tugagan yoki Free tarifidasiz.\n"
            "/account orqali PRO yoki VIP tarifini sotib oling."
        )
        return

    active_tasks = db.count_active_tasks(user_id)
    if active_tasks >= user.get("tasks_limit", 5):
        await message.reply_text("⚠️ Faol vazifalar limitingiz tugagan. /account orqali limitni kengaytiring.")
        return

    processing_msg = await message.reply_text("⏳ Ovozli xabaringiz AI tomonidan tahlil qilinmoqda...")

    try:
        # 2. Ovoz -> Matn
        voice_file = await context.bot.get_file(message.voice.file_id)
        text_from_voice = await transcribe_voice(voice_file)

        if not text_from_voice or len(text_from_voice.strip()) < 2:
            await message.reply_text("Kechirasiz, ovozni tushunib bo'lmadi. Iltimos, qaytadan yozib yuboring.")
            return

        # 3. Matn -> JSON
        task_data = await extract_task_json(text_from_voice)
        title = task_data.get("title", "Ovozli vazifa")
        date_str = task_data.get("date")
        time_str = task_data.get("time") or "09:00" # Agar vaqt topilmasa, default 09:00
        description = task_data.get("description", "")

        # ISO formatda due_datetime yasash (Toshkent vaqti bilan)
        now = datetime.now(LOCAL_TZ)
        if not date_str:
            date_str = now.strftime("%Y-%m-%d")

        due_datetime_str = f"{date_str} {time_str}:00"

        # 4. Bazaga to'g'ri parametrlar bilan saqlash
        task_id = db.add_task(
            user_id=user_id,
            title=title,
            description=description,
            due_datetime=due_datetime_str,
            reminder_minutes_before=15, # Standart 15 daqiqa oldin eslatish
            repeat_type="none",
            repeat_interval_days=None
        )

        # Limitdan 1 ta ayirish
        db.decrement_voice_limit(user_id)

        await message.reply_text(
            f"✅ <b>Vazifa saqlandi!</b>\n\n"
            f"📌 <b>Nomi:</b> {title}\n"
            f"📅 <b>Vaqti:</b> {due_datetime_str}\n"
            f"{f'📝 <b>Izoh:</b> {description}' if description else ''}",
            parse_mode="HTML"
        )
    finally:
        try:
            await context.bot.delete_message(chat_id=message.chat_id, message_id=processing_msg.message_id)
        except Exception:
            pass
