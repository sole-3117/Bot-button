import os

ADMIN_IDS = [int(i.strip()) for i in os.getenv("ADMIN_IDS", "SIZNING_TELEGRAM_ID").split(",") if i.strip()]

# Tariflar bo'yicha cheklovlar
PLAN_LIMITS = {
    "free": 5,      # Maksimal 5 ta faol vazifa
    "pro": 30,      # Maksimal 30 ta vazifa
    "vip": 999999   # Cheksiz
}
