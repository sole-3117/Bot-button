import os
from dotenv import load_dotenv
import pytz

load_dotenv()

# Bot sozlamalari
BOT_TOKEN = os.getenv("BOT_TOKEN")
MAIN_ADMIN = int(os.getenv("MAIN_ADMIN", 0)) if os.getenv("MAIN_ADMIN") else None
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/bot_db")
LOCAL_TZ = pytz.timezone(os.getenv("LOCAL_TZ", "Asia/Tashkent"))

# Reminder va Repeat variantlari
REMINDER_OPTIONS = {
    "5": 5,
    "15": 15,
    "30": 30,
    "1 soat": 60,
}

REPEAT_TYPES = {
    "none": "Takrorlanmaydi",
    "daily": "Har kuni",
    "weekly": "Har hafta",
    "custom": "Custom interval",
}
