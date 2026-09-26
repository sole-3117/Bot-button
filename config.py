import os
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

LOCAL_TZ = ZoneInfo(os.getenv("LOCAL_TZ", "Asia/Tashkent"))

MAIN_ADMIN = int(os.getenv("MAIN_ADMIN", "0"))
ADMIN_IDS = [MAIN_ADMIN] if MAIN_ADMIN else []

PAYMENT_CARD = os.getenv("PAYMENT_CARD", "")
PAYMENT_OWNER = os.getenv("PAYMENT_OWNER", "")

AI_API_KEY = os.getenv("AI_API_KEY")
WHISPER_API_KEY = os.getenv("WHISPER_API_KEY", AI_API_KEY)

REMINDER_OPTIONS = {
    "5": 5,
    "15": 15,
    "30": 30,
    "60": 60,
}

REPEAT_TYPES = {
    "none": "Takrorlanmasin",
    "daily": "Har kuni",
    "weekly": "Har hafta",
    "monthly": "Har oy",
    "custom": "Maxsus interval",
}

# Ham 'limit', ham 'max_tasks' qo'shildi (KeyError oldini olish uchun)
PLANS = {
    "free": {
        "name": "Free",
        "price": 0,
        "limit": 5,
        "max_tasks": 5,
        "max_voice": 0,
        "max_sms": 3,
        "duration_days": 9999,
    },
    "pro": {
        "name": "Pro",
        "price": 15000,
        "limit": 50,
        "max_tasks": 50,
        "max_voice": 50,
        "max_sms": 30,
        "duration_days": 30,
    },
    "vip": {
        "name": "VIP",
        "price": 35000,
        "limit": 9999,
        "max_tasks": 9999,
        "max_voice": 9999,
        "max_sms": 60,
        "duration_days": 30,
    },
}
