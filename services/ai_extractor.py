# services/ai_extractor.py
import json
import logging
from datetime import datetime
from openai import AsyncOpenAI
from config import AI_API_KEY

logger = logging.getLogger(__name__)

# OpenAI asinxron mijozi (Agar Whisper kaliti bilan bir xil bo'lsa, o'shani berasiz)
client = AsyncOpenAI(api_key=AI_API_KEY)

async def extract_task_json(raw_text: str) -> dict:
    """
    Foydalanuvchining xom matnini tahlil qilib, JSON formatda
    sana, vaqt va sarlavhani ajratib oladi.
    """
    # 1. Hozirgi vaqt va sanani aniqlash (Nisbiy so'zlar: "ertaga", "indin" ni to'g'ri tushunishi uchun juda muhim)
    now = datetime.now()
    current_context = (
        f"Bugungi sana: {now.strftime('%Y-%m-%d')}. "
        f"Hozirgi vaqt: {now.strftime('%H:%M')}. "
        f"Hafta kuni: {now.strftime('%A')}."
    )

    # 2. AI uchun qat'iy tizim prompti (System Prompt)
    system_prompt = f"""
    Siz vazifalarni tahlil qiluvchi aqlli yordamchisiz.
    Foydalanuvchining o'zbek tilidagi erkin matnidan quyidagi ma'lumotlarni ajratib, faqat toza JSON formatida qaytaring:
    - "title": Vazifa sarlavhasi (qisqa va aniq ma'noli).
    - "date": Sana (YYYY-MM-DD formatida).
    - "time": Vaqt (HH:MM formatida).
    - "description": Qo'shimcha izohlar (agar bo'lsa, yo'qsa bo'sh qoldiring).

    {current_context}

    Qoidalar:
    - Agar matnda "ertaga", "indin" kabi so'zlar bo'lsa, hozirgi sanadan kelib chiqib aniq sanani hisoblang.
    - Agar sanani umuman aytmagan bo'lsa, bugungi sanani qo'ying.
    - Agar matnda aniq vaqt aytilmagan bo'lsa, "time" qiymatini null (bo'sh) qoldiring.
    - Hech qanday izoh yoki markdown yozmang, faqat JSON obyekt qaytaring.
    """

    try:
        # 3. Modelga so'rov yuborish
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": raw_text}
            ],
            temperature=0, # 0 bo'lsa, model ijodkorlik qilmaydi, aniq va mashinaday ishlaydi
            response_format={"type": "json_object"} # Qat'iy JSON formatida qaytarishni majburlaymiz
        )

        # 4. Javobni parse qilish
        result_text = response.choices[0].message.content
        task_data = json.loads(result_text)
        
        return task_data

    except Exception as e:
        logger.error(f"AI Extraction xatosi: {e}")
        # Xatolik bo'lsa, bot qotib qolmasligi uchun himoya qatlami (Fallback)
        return {
            "title": raw_text[:50] + "...", 
            "date": now.strftime('%Y-%m-%d'),
            "time": None,
            "description": raw_text
        }
