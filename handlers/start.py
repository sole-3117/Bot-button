# handlers/start.py ichidagi start funksiyasiga qo'shiladi:
from database import register_user

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user.id, user.username or "", user.full_name or "")
    # ... qolgan start menyusi kodi ...
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import database as db


def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Yangi vazifa", callback_data="new_task")],
        [InlineKeyboardButton("📋 Vazifalarim", callback_data="list_tasks")],
        [InlineKeyboardButton("✅ Bajarilganlar", callback_data="list_done")],
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.add_user(user.id, user.username, user.first_name)
    await update.message.reply_text(
        f"Assalomu alaykum, {user.first_name}! 👋\n\n"
        "Men *Rejachi* botiman — vazifalaringizni belgilangan vaqtda eslataman.\n\n"
        "Quyidagi menyudan foydalaning:",
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown",
    )


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "Asosiy menyu:",
        reply_markup=main_menu_keyboard(),
    )
