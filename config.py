import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
DB_PATH = os.getenv("DB_PATH", "rejachi.db")
TIMEZONE = os.getenv("TIMEZONE", "Asia/Tashkent")

# Oldindan eslatish variantlari (daqiqalarda)
REMINDER_OPTIONS = {
    "5": 5,
    "15": 15,
    "30": 30,
    "60": 60,
}

# Takrorlanish turlari
REPEAT_TYPES = {
    "none": "Takrorlanmasin",
    "daily": "Har kuni",
    "weekly": "Har hafta",
    "monthly": "Har oy",
    "custom": "Maxsus interval",
}
