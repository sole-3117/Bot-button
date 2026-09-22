from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from telegram.error import BadRequest
import database as db
from config import REMINDER_OPTIONS, REPEAT_TYPES
from handlers.start import main_menu_keyboard

# Conversation states
TITLE, DATE, TIME, REMINDER, REPEAT, CUSTOM_INTERVAL = range(6)


# ---------- Yordamchi xavfsiz tahrirlash ----------

async def safe_edit_message(query, text: str, reply_markup=None, parse_mode=None):
    """Xabar mazmuni o'zgarmagan bo'lsa BadRequest xatosini e'tiborsiz qoldiradi."""
    try:
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
        )
    except BadRequest as exc:
        if "Message is not modified" in str(exc):
            pass
        else:
            raise exc


# ---------- Yangi vazifa yaratish ----------

async def new_task_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await safe_edit_message(query, "📝 Vazifa nomini kiriting:")
    return TITLE


async def receive_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["title"] = update.message.text
    await update.message.reply_text(
        "📅 Sanani kiriting (KK.OO.YYYY, masalan 25.12.2026):"
    )
    return DATE


async def receive_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        parsed = datetime.strptime(text, "%d.%m.%Y")
        context.user_data["date"] = parsed
    except ValueError:
        await update.message.reply_text(
            "❌ Sana notoʻgʻri. Iltimos, KK.OO.YYYY formatida kiriting (masalan 25.12.2026):"
        )
        return DATE
    await update.message.reply_text("⏰ Vaqtni kiriting (SS:DD, masalan 14:30):")
    return TIME


async def receive_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        parsed_time = datetime.strptime(text, "%H:%M")
    except ValueError:
        await update.message.reply_text(
            "❌ Vaqt notoʻgʻri. Iltimos, SS:DD formatida kiriting (masalan 14:30):"
        )
        return TIME

    date_obj = context.user_data["date"]
    due = date_obj.replace(hour=parsed_time.hour, minute=parsed_time.minute)
    context.user_data["due_datetime"] = due.isoformat()

    keyboard = [
        [InlineKeyboardButton(f"{label} daqiqa oldin", callback_data=f"rem_{minutes}")]
        for label, minutes in REMINDER_OPTIONS.items()
    ]
    keyboard.append([InlineKeyboardButton("Eslatma kerak emas", callback_data="rem_0")])
    await update.message.reply_text(
        "🔔 Qancha vaqt oldin eslatilsin?",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return REMINDER


async def receive_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    minutes = int(query.data.split("_")[1])
    context.user_data["reminder_minutes"] = minutes

    keyboard = [
        [InlineKeyboardButton(label, callback_data=f"rep_{key}")]
        for key, label in REPEAT_TYPES.items()
    ]
    await safe_edit_message(
        query,
        "🔁 Takrorlanish turini tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return REPEAT


async def receive_repeat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    repeat_type = query.data.split("_")[1]
    context.user_data["repeat_type"] = repeat_type

    if repeat_type == "custom":
        await safe_edit_message(query, "🔢 Necha kunda bir marta takrorlansin? (son kiriting):")
        return CUSTOM_INTERVAL

    return await save_task(update, context)


async def receive_custom_interval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit() or int(text) <= 0:
        await update.message.reply_text("❌ Iltimos, musbat son kiriting:")
        return CUSTOM_INTERVAL
    context.user_data["repeat_interval_days"] = int(text)
    return await save_task(update, context, from_message=True)


async def save_task(update: Update, context: ContextTypes.DEFAULT_TYPE, from_message: bool = False):
    user_id = update.effective_user.id
    data = context.user_data

    task_id = db.add_task(
        user_id=user_id,
        title=data["title"],
        due_datetime=data["due_datetime"],
        reminder_minutes_before=data.get("reminder_minutes", 0),
        repeat_type=data.get("repeat_type", "none"),
        repeat_interval_days=data.get("repeat_interval_days"),
    )

    due = datetime.fromisoformat(data["due_datetime"])
    text = (
        f"✅ Vazifa yaratildi!\n\n"
        f"📌 {data['title']}\n"
        f"📅 {due.strftime('%d.%m.%Y %H:%M')}\n"
        f"🔔 Eslatma: {data.get('reminder_minutes', 0)} daqiqa oldin\n"
        f"🔁 Takrorlanish: {REPEAT_TYPES.get(data.get('repeat_type', 'none'))}"
    )

    if from_message:
        await update.message.reply_text(text, reply_markup=main_menu_keyboard())
    else:
        await safe_edit_message(update.callback_query, text, reply_markup=main_menu_keyboard())

    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Bekor qilindi.", reply_markup=main_menu_keyboard())
    return ConversationHandler.END


# ---------- Vazifalar roʻyxati ----------

async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    tasks = db.get_user_tasks(user_id, status="active")

    if not tasks:
        await safe_edit_message(
            query,
            "📋 Faol vazifalar yoʻq.",
            reply_markup=main_menu_keyboard(),
        )
        return

    await safe_edit_message(
        query,
        "📋 *Faol vazifalar roʻyxati:*",
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown",
    )

    for task in tasks:
        due = datetime.fromisoformat(task["due_datetime"])
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Bajarildi", callback_data=f"complete_{task['task_id']}"),
                InlineKeyboardButton("🗑 Oʻchirish", callback_data=f"delete_{task['task_id']}"),
            ]
        ])
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"📌 {task['title']}\n📅 {due.strftime('%d.%m.%Y %H:%M')}",
            reply_markup=keyboard,
        )


async def list_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    tasks = db.get_user_tasks(user_id, status="done")

    if not tasks:
        await safe_edit_message(
            query,
            "✅ Bajarilgan vazifalar yoʻq.",
            reply_markup=main_menu_keyboard(),
        )
        return

    lines = ["✅ *Bajarilgan vazifalar:*\n"]
    for task in tasks:
        due = datetime.fromisoformat(task["due_datetime"])
        lines.append(f"• {task['title']} ({due.strftime('%d.%m.%Y %H:%M')})")

    await safe_edit_message(
        query,
        "\n".join(lines),
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown",
    )


async def complete_task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Vazifa bajarildi! ✅")
    task_id = int(query.data.split("_")[1])
    db.complete_task(task_id)
    await safe_edit_message(query, "✅ Vazifa bajarildi deb belgilandi.")


async def delete_task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Oʻchirildi 🗑")
    task_id = int(query.data.split("_")[1])
    db.delete_task(task_id)
    await safe_edit_message(query, "🗑 Vazifa oʻchirildi.")
