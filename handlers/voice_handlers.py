# handlers/voice_handlers.py
from aiogram import Router, F, Bot
from aiogram.types import Message
# Xizmatlarni chaqiramiz (Bu fayllar API lar bilan gaplashadi)
from services.speech_to_text import transcribe_voice 
from services.ai_extractor import extract_task_json

voice_router = Router()

@voice_router.message(F.voice)
async def process_voice_message(message: Message, bot: Bot):
    # 1. Bepul tarifdagilarni tekshirish (Logika kelajakda DB ga bog'lanadi)
    # if user_plan == 'free': await message.answer("Ovozli funksiya faqat PRO/VIP da!") return

    processing_msg = await message.answer("⏳ Ovozli xabaringiz tahlil qilinmoqda...")

    try:
        file_id = message.voice.file_id
        
        # 2. Whisper orqali matnga o'giramiz
        text_from_voice = await transcribe_voice(bot, file_id) 
        
        # 3. AI orqali JSON olamiz
        task_data = await extract_task_json(text_from_voice) 

        # 4. Foydalanuvchiga natijani beramiz
        await message.answer(
            f"✅ <b>Vazifa qo'shildi!</b>\n\n"
            f"📌 <b>Sarlavha:</b> {task_data['title']}\n"
            f"📅 <b>Sana:</b> {task_data['date']}\n"
            f"⏰ <b>Vaqt:</b> {task_data['time']}",
            parse_mode="HTML"
        )
    finally:
        await processing_msg.delete()
