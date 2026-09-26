# main.py
import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN

# Routerlarni chaqiramiz
from middlewares.error_handler import error_router
from handlers.voice_handlers import voice_router
# from handlers.user_handlers import user_router
# from handlers.admin_handlers import admin_router

logging.basicConfig(level=logging.INFO)

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Xatoliklarni ushlovchi routerni birinchi ulaymiz (Juda muhim!)
    dp.include_router(error_router)
    
    # Qolgan barcha funksiyalar routeri
    # dp.include_router(user_router)
    dp.include_router(voice_router)
    # dp.include_router(admin_router)
    
    print("🤖 Bot ishga tushdi va API lar ulandi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
