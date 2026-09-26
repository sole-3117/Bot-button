# handlers/voice_handlers.py
from telegram import Update
from telegram.ext import ContextTypes

# Bu fayllar hali yozilmagan bo'lsa, pastroqda qanday yozishni aytaman
# from services.speech_to_text import transcribe_voice 
# from services.ai_extractor import extract_task_json

async def process_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Ovozli xabarlarni qabul qilib, vazifaga aylantiruvchi handler.
    Xatolar global_error_handler tomonidan ushlanadi.
    """
    message = update.message

    # 1. Bepul tarifdagilarni tekshirish (Logika kelajakda DB ga bog'lanadi)
    # if user_plan == 'free': await message.reply_text("Ovozli funksiya faqat PRO/VIP da!") return

    processing_msg = await message.reply_text("⏳ Ovozli xabaringiz tahlil qilinmoqda...")

    try:
        # 2. Ovozli faylni olish (PTB usuli)
        voice_file = await context.bot.get_file(message.voice.file_id)
        
        # 3. Whisper orqali matnga o'giramiz (Hali yozamiz)
        # text_from_voice = await transcribe_voice(voice_file) 
        
        # 4. AI orqali JSON olamiz (Hali yozamiz)
        # task_data = await extract_task_json(text_from_voice) 

        # Hozircha test ma'lumot (API ulanmaganda kod xato bermasligi uchun)
        task_data = {
            'title': 'Test vazifa',
            'date': '2026-09-26',
            'time': '12:00'
        }

        # 5. Foydalanuvchiga natijani beramiz
        await message.reply_text(
            f"✅ <b>Vazifa qo'shildi!</b>\n\n"
            f"📌 <b>Sarlavha:</b> {task_data['title']}\n"
            f"📅 <b>Sana:</b> {task_data['date']}\n"
            f"⏰ <b>Vaqt:</b> {task_data['time']}",
            parse_mode="HTML"
        )
    finally:
        # Jarayon tugagach, "Yuklanmoqda..." xabarini o'chirib tashlaymiz
        try:
            await context.bot.delete_message(
                chat_id=message.chat_id, 
                message_id=processing_msg.message_id
            )
        except Exception:
            pass # Xabar allaqachon o'chirilgan bo'lsa xato bermaydi
