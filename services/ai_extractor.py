import os
import json
from datetime import datetime, timedelta
import pytz
from openai import OpenAI

AI_API_KEY = os.getenv("AI_API_KEY")
LOCAL_TZ = pytz.timezone(os.getenv("LOCAL_TZ", "Asia/Tashkent"))

def extract_task_json(raw_text: str) -> dict:
    """Matndan vazifa parametrlarini ajratib oladi (GPT-4o-mini orqali)"""
    if not AI_API_KEY:
        return None

    client = OpenAI(api_key=AI_API_KEY)
    now = datetime.now(LOCAL_TZ)
    current_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")
    tomorrow = (now + timedelta(days=1)).strftime("%Y-%m-%d")

    system_prompt = f"""
Sen Telegram eslatuvchi bot uchun yordamchisan. Hozirgi sana: {current_date}, vaqt: {current_time}.
Foydalanuvchi matnini tahlil qilib, faqat JSON formatida qaytar:
{{
    "title": "Vazifa nomi (qisqa)",
    "description": "Batafsil izoh yoki bo'sh string",
    "due_datetime": "YYYY-MM-DDTHH:MM:SS",
    "reminder_minutes_before": 15,
    "repeat_type": "none"
}}
Agar sana/vaqt aytilmagan bo'lsa, {tomorrow}T09:00:00 ni belgilang.
Faqat toza JSON qaytar.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": raw_text}
            ],
            temperature=0.2
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()
        return json.loads(content)
    except Exception:
        return None
