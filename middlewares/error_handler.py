# middlewares/error_handler.py
import logging
from aiogram import Router, Bot
from aiogram.types import ErrorEvent
from config import ADMIN_IDS

error_router = Router()
logger = logging.getLogger(__name__)

@error_router.errors()
async def global_error_handler(event: ErrorEvent, bot: Bot):
    exception = event.exception
    logger.error(f"Xatolik: {exception}")

    user = None
    if event.update.message:
        user = event.update.message.from_user
    elif event.update.callback_query:
        user = event.update.callback_query.from_user

    user_msg = (
        "Kechirasiz, provayderlarimiz bilan bog'lanishda vaqtinchalik uzilish yuz berdi. 🛠\n"
        "Iltimos, hozircha amaliyotni matn ko'rinishida yozib ko'ring yoki birozdan so'ng urinib ko'ring."
    )
    
    try:
        if event.update.message:
            await event.update.message.answer(user_msg)
        elif event.update.callback_query:
            await event.update.callback_query.message.answer(user_msg)
    except Exception:
        pass # Agar foydalanuvchiga yozish imkonsiz bo'lsa, o'tkazib yuboramiz

    admin_log = (
        f"⚠️ <b>TIZIMDA XATOLIK!</b>\n\n"
        f"👤 <b>Foydalanuvchi:</b> @{user.username if user else 'N/A'}\n"
        f"🔴 <b>Xato turi:</b> {type(exception).__name__}\n"
        f"📄 <b>Tafsilot:</b> {str(exception)[:300]}"
    )

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(chat_id=admin_id, text=admin_log, parse_mode="HTML")
        except:
            pass
