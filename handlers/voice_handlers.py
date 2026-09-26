# handlers/voice_handlers.py
import logging
from telegram import Update
from telegram.ext import ContextTypes

# Servislarimizni chaqiramiz
from services.speech_to_text import transcribe_voice 
from services.ai_extractor import extract_task_json

# Ma'lumotlar bazasini chaqiramiz (Sizning arxitekturangizga moslab)
import database as db

logger = logging.getLogger(__name__)

async def process_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Ovozli xabarlarni qabul qilib, tahlil qiladi va ro'yxatga (DB) saqlaydi.
    """
    message = update.message
    user_id = update.effective_user.id

    # -------------------------------------------------------------
    # 1. LIMITLARNI TEKSHIRISH (Buni 3-qadamda bazaga to'liq ulaymiz)
    # -------------------------------------------------------------
    # user_plan = db.get_user_plan(user_id)
    # voice_count = db.get_voice_usage(user_id)
    # if user_plan == 'free' and voice_count >= 0:
    #     await message.reply_text("🎙 Ovozli yordamchi faqat PRO va VIP tariflarida mavjud. \n/account orqali tarifni yangilang.")
    #     return

    # Jarayon boshlanganini bildiramiz
    processing_msg = await message.reply_text("⏳ Ovozli xabaringiz AI tomonidan tahlil qilinmoqda...")

    try:
        # -------------------------------------------------------------
        # 2. OVOZ -> MATN (Whisper)
        # -------------------------------------------------------------
        voice_file = await context.bot.get_file(message.voice.file_id)
        text_from_voice = await transcribe_voice(voice_file)
        
        # Agar ovozda hech narsa tushunarsiz bo'lsa
        if not text_from_voice or len(text_from_voice.strip()) < 2:
            await message.reply_text("Kechirasiz, ovozingizni tushuna olmadim. Iltimos, qaytadan aniqroq gapiring.")
            return

        # -------------------------------------------------------------
        # 3. MATN -> JSON (GPT-4o-mini)
        # -------------------------------------------------------------
        task_data = await extract_task_json(text_from_voice)

        title = task_data.get("title", "Nomsiz vazifa")
        date_str = task_data.get("date")
        time_str = task_data.get("time")
        description = task_data.get("description", "")

        # -------------------------------------------------------------
        # 4. BAZAGA SAQLASH
        # -------------------------------------------------------------
        # Bu qator sizning database.py faylingizdagi funksiya nomiga mos bo'lishi kerak.
        # Agar sizda boshqacha nomlangan bo'lsa (masalan: insert_task), shunga o'zgartirasiz.
        db.add_task(
            user_id=user_id,
            title=title,
            description=description,
            date_val=date_str,
            time_val=time_str,
            status="pending" # Vazifa holati
        )

        # Ovozli limitni bittaga kamaytirish (Buni ham 3-qadamda ochamiz)
        # db.increment_voice_usage(user_id)

        # -------------------------------------------------------------
        # 5. FOYDALANUVCHIGA NATIJA
        # -------------------------------------------------------------
        time_display = time_str if time_str else "Vaqt belgilanmagan"
        desc_display = f"\n📝 <b>Izoh:</b> {description}" if description else ""

        await message.reply_text(
            f"✅ <b>Vazifa muvaffaqiyatli saqlandi!</b>\n\n"
            f"📌 <b>Sarlavha:</b> {title}\n"
            f"📅 <b>Sana:</b> {date_str}\n"
            f"⏰ <b>Vaqt:</b> {time_display}"
            f"{desc_display}",
            parse_mode="HTML"
        )
        
    finally:
        # Xato bo'lsa ham, muvaffaqiyatli bo'lsa ham "Yuklanmoqda..." xabarini o'chirib tashlaymiz
        try:
            await context.bot.delete_message(
                chat_id=message.chat_id, 
                message_id=processing_msg.message_id
            )
        except Exception:
            pass
