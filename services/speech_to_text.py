import os
from openai import OpenAI

WHISPER_API_KEY = os.getenv("WHISPER_API_KEY") or os.getenv("AI_API_KEY")

async def transcribe_voice(bot, file_id: str) -> str:
    """Ovoz faylini matnga aylantiradi (Whisper orqali)"""
    if not WHISPER_API_KEY:
        raise ValueError("WHISPER_API_KEY sozlanmagan")

    file = await bot.get_file(file_id)
    file_path = f"/tmp/{file_id}.ogg"
    await file.download_to_drive(custom_path=file_path)

    client = OpenAI(api_key=WHISPER_API_KEY)
    try:
        with open(file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="uz"
            )
        return transcript.text
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
