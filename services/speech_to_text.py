# services/speech_to_text.py
import os
import tempfile
from openai import AsyncOpenAI
from config import WHISPER_API_KEY

# OpenAI asinxron mijozi (API kaliti bilan)
client = AsyncOpenAI(api_key=WHISPER_API_KEY)

async def transcribe_voice(voice_file) -> str:
    """
    Telegramdan olingan ovozli faylni Whisper API orqali matnga o'giradi.
    """
    # Vaqtinchalik fayl yaratamiz (xotirani to'ldirib yubormaslik uchun)
    # Telegram ovozli xabarlari odatda .ogg formatida bo'ladi
    with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as temp_audio:
        temp_file_path = temp_audio.name

    try:
        # 1. Telegram serveridan audioni vaqtinchalik faylga yuklab olamiz
        await voice_file.download_to_drive(custom_path=temp_file_path)
        
        # 2. Faylni ochib, Whisper API ga yuboramiz
        with open(temp_file_path, "rb") as audio_data:
            transcription = await client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_data,
                language="uz" # O'zbek tilini majburiy ko'rsatamiz, bu aniqlikni oshiradi
            )
            
        # 3. Matnni qaytaramiz
        return transcription.text

    finally:
        # 4. Jarayon tugagach yoki xato bo'lganda ham, vaqtinchalik faylni albatta o'chiramiz
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
