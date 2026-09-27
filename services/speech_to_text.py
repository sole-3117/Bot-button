import os
from openai import AsyncOpenAI

async def transcribe_voice(bot, file_id: str) -> str:
    """Ovoz faylini matnga aylantiradi (Whisper orqali)"""
    api_key = os.getenv("WHISPER_API_KEY") or os.getenv("AI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OpenAI API kaliti (.env da WHISPER_API_KEY yoki OPENAI_API_KEY) kiritilmagan!")

    client = AsyncOpenAI(api_key=api_key)

    file = await bot.get_file(file_id)
    file_path = f"/tmp/{file_id}.ogg"
    await file.download_to_drive(custom_path=file_path)

    try:
        with open(file_path, "rb") as audio_file:
            transcript = await client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="uz"
            )
        return transcript.text
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
