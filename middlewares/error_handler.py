import logging
from telegram import Update
from telegram.error import BadRequest, Conflict
from telegram.ext import ContextTypes
from config import MAIN_ADMIN

logger = logging.getLogger(__name__)

async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xatolarni global ravishda boshqaradi"""
    error = context.error
    
    # Message is not modified xatosini yutsin
    if isinstance(error, BadRequest) and "Message is not modified" in str(error):
        logger.debug("Message is not modified xatosi - e'tiborga olinmadi")
        return
    
    # Conflict xatosi (409) - bot boshqa joyda ham ishlamoqda
    if isinstance(error, Conflict):
        logger.error("409 Conflict: Bot token boshqa joyda ham ishlayapti!")
        if MAIN_ADMIN and update:
            try:
                await context.bot.send_message(
                    chat_id=MAIN_ADMIN,
                    text="⚠️ KRITIK XATOLIK: Bot token boshqa joyda ham ishlayapti (409 Conflict)"
                )
            except Exception as e:
                logger.error(f"Adminga xabar yubora olmadi: {e}")
        return
    
    # Boshqa kritik xatolar
    logger.error(f"Xatolik yuz berdi: {error}", exc_info=context.error)
    
    if MAIN_ADMIN and update:
        try:
            await context.bot.send_message(
                chat_id=MAIN_ADMIN,
                text=f"🔴 Xatolik:\n{str(error)[:200]}"
            )
        except Exception as e:
            logger.error(f"Adminga xabar yubora olmadi: {e}")
