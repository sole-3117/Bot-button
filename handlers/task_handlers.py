from telegram import Update
from telegram.ext import ContextTypes
import database as db

async def complete_task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    # Callback format: "complete_123"
    task_id = int(query.data.split("_")[1])

    # Bazadan tekshirib yakunlaymiz
    success = db.complete_task(task_id, user_id)

    if not success:
        # Agar vazifa boshqa odamniki bo'lsa yoki topilmasa
        await query.answer("⚠️ Bu vazifa sizga tegishli emas yoki topilmadi!", show_alert=True)
        return

    await query.edit_message_text("✅ Vazifa muvaffaqiyatli yakunlandi!")


async def delete_task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    # Callback format: "delete_123"
    task_id = int(query.data.split("_")[1])

    # Bazadan tekshirib o'chiramiz
    success = db.delete_task(task_id, user_id)

    if not success:
        # Agar vazifa boshqa odamniki bo'lsa yoki topilmasa
        await query.answer("⚠️ Bu vazifa sizga tegishli emas yoki topilmadi!", show_alert=True)
        return

    await query.edit_message_text("🗑 Vazifa muvaffaqiyatli o'chirildi.")
