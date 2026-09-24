import os
from datetime import timezone, timedelta

BOT_TOKEN = os.getenv("BOT_TOKEN", "SIZNING_BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")  # Agar bo'lsa PostgreSQL, bo'lmasa SQLite
DB_PATH = os.getenv("DB_PATH", "rejachi.db")
ADMIN_IDS = [int(i.strip()) for i in os.getenv("ADMIN_IDS", "123456789").split(",") if i.strip()]

# Toshkent vaqti (UTC+5)
LOCAL_TZ = timezone(timedelta(hours=5))

# To'lov ma'lumotlari
PAYMENT_CARD = "8600 0000 0000 0000"
PAYMENT_OWNER = "ISM FAMILIYA"

# Tarif narxlari va limitlari
PLANS = {
    "free": {"name": "Oddiy (Free)", "price": 0, "limit": 5},
    "pro": {"name": "Pro Rejachi", "price": 15000, "limit": 30},
    "vip": {"name": "VIP Cheksiz", "price": 30000, "limit": 999999},
}

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
    "custom": "Boshqa oraliq",
}
