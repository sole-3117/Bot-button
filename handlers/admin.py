import os
import shutil
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from config import ADMIN_IDS, DB_PATH

RESTORE_FILE = 1

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

# ---------- /backup ----------
async def backup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("⛔️ Siz admin emassiz.")
        return

    if not os.path.exists(DB_PATH):
        await update.message.reply_text("❌ Baza fayli topilmadi.")
        return

    await update.message.reply_text("📦 Baza zaxira nusxasi tayyorlanmoqda...")
    with open(DB_PATH, "rb") as db_file:
        await context.bot.send_document(
            chat_id=user_id,
            document=db_file,
            filename=os.path.basename(DB_PATH),
            caption="✅ Baza muvaffaqiyatli saqlandi (/backup)."
        )

# ---------- /restore ----------
async def restore_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("⛔️ Siz admin emassiz.")
        return ConversationHandler.END

    await update.message.reply_text(
        "📥 Yangi `.db` faylini ushbu chatga hujjat (document) koʻrinishida yuboring.\n"
        "Bekor qilish uchun /cancel deb yozing."
    )
    return RESTORE_FILE

async def restore_file_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    if not document.file_name.endswith(".db"):
        await update.message.reply_text("❌ Iltimos, faqat `.db` formatidagi baza faylini yuboring:")
        return RESTORE_FILE

    # Eski faylni ehtiyotkorlik uchun .bak qilib saqlaymiz
    if os.path.exists(DB_PATH):
        shutil.copyfile(DB_PATH, f"{DB_PATH}.bak")

    # Yangi faylni yuklab olamiz
    new_file = await context.bot.get_file(document.file_id)
    await new_file.download_to_drive(custom_path=DB_PATH)

    await update.message.reply_text("✅ Maʼlumotlar bazasi muvaffaqiyatli tiklandi (/restore)!")
    return ConversationHandler.END
