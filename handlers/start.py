from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import database as db

def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Yangi vazifa", callback_data="new_task")],
        [InlineKeyboardButton("📋 Faol vazifalar", callback_data="list_tasks")],
        [InlineKeyboardButton("✅ Bajarilganlar", callback_data="list_done")],
        [InlineKeyboardButton("👤 Shaxsiy kabinet", callback_data="open_account")]
    ])

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.register_user(user.id, user.username or "", user.full_name or "")
    text = (
        f"Assalomu alaykum, {user.first_name}! 👋\n\n"
        "Men sizga rejalaringizni tartibga solishda va eslatib turishda yordam beraman.\n"
        "Quyidagi tugmalardan birini tanlang:"
    )
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, reply_markup=main_menu_keyboard())
    else:
        await update.message.reply_text(text, reply_markup=main_menu_keyboard())
