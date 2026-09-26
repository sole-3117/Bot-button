# middlewares/error_handler.py
import logging
from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_IDS

logger = logging.getLogger(__name__)

async def global_error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Barcha xatoliklarni ushlab qoluvchi va adminga yuboruvchi global yadro.
    """
    exception = context.error
    logger.error(f"Xatolik yuz berdi: {exception}")

    # 1. Foydalanuvchini aniqlash
    user = None
    if update and update.effective_user:
        user = update.effective_user

    # 2. Foydalanuvchiga silliq va xushmuomala javob qaytarish
    user_msg = (
        "Kechirasiz, provayderlarimiz bilan bog'lanishda vaqtinchalik uzilish yuz berdi. 🛠\n"
        "Iltimos, hozircha amaliyotni matn ko'rinishida yozib ko'ring yoki birozdan so'ng urinib ko'ring."
    )
    
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(user_msg)
    except Exception as e:
        logger.error(f"Foydalanuvchiga xabar yuborishda xatolik: {e}")

    # 3. Adminga to'liq texnik hisobot yuborish
    admin_log = (
        f"⚠️ <b>TIZIMDA XATOLIK!</b>\n\n"
        f"👤 <b>Foydalanuvchi:</b> @{user.username if user and user.username else 'N/A'}\n"
        f"🔴 <b>Xato turi:</b> <code>{type(exception).__name__}</code>\n"
        f"📄 <b>Tafsilot:</b> <i>{str(exception)[:300]}</i>"
    )

    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(chat_id=admin_id, text=admin_log, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Adminga log yuborib bo'lmadi: {e}")
