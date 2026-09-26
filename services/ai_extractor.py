import json
import logging
from datetime import datetime
from openai import AsyncOpenAI
from config import AI_API_KEY, LOCAL_TZ

logger = logging.getLogger(__name__)
client = AsyncOpenAI(api_key=AI_API_KEY)

async def extract_task_json(raw_text: str) -> dict:
    now = datetime.now(LOCAL_TZ)
    current_context = (
        f"Bugungi sana: {now.strftime('%Y-%m-%d')}. "
        f"Hozirgi vaqt: {now.strftime('%H:%M')}. "
        f"Hafta kuni: {now.strftime('%A')}."
    )

    system_prompt = f"""
    Siz vazifalarni tahlil qiluvchi yordamchisiz.
    Foydalanuvchining o'zbek tilidagi matnidan quyidagi ma'lumotlarni ajratib, faqat toza JSON formatida qaytaring:
    - "title": Vazifa sarlavhasi.
    - "date": YYYY-MM-DD formati.
    - "time": HH:MM formati (agar aytilmagan bo'lsa null).
    - "description": Qo'shimcha izohlar.

    {current_context}
    Hech qanday tushuntirishsiz faqat JSON qaytaring.
    """

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": raw_text}
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"AI Extraction xatosi: {e}")
        return {
            "title": raw_text[:50],
            "date": now.strftime("%Y-%m-%d"),
            "time": None,
            "description": raw_text
        }
