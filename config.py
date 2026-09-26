# config.py
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [123456789] # O'zingizning va shogirdingizning Telegram ID'lari

# API Kalitlar
WHISPER_API_KEY = os.getenv("WHISPER_API_KEY")
AI_API_KEY = os.getenv("AI_API_KEY")
ESKIZ_EMAIL = os.getenv("ESKIZ_EMAIL")
ESKIZ_PASSWORD = os.getenv("ESKIZ_PASSWORD")

# Tariflar va Limitlar (Siz bilan kelishilgan o'lchamlar)
PLANS = {
    "free": {
        "price": 0,
        "max_tasks": 5,
        "max_voice": 0,
        "max_sms": 3, # Bir martalik Welcome Bonus
        "duration_days": 9999
    },
    "pro": {
        "price": 15000,
        "max_tasks": 50, # Sizga tekin bo'lgani uchun ko'p beramiz
        "max_voice": 50,
        "max_sms": 30,
        "duration_days": 30
    },
    "vip": {
        "price": 35000,
        "max_tasks": 9999, # Cheksiz
        "max_voice": 9999, # Cheksiz
        "max_sms": 60,
        "duration_days": 30
    }
}
