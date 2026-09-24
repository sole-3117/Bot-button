from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from telegram.error import BadRequest
import database as db
from config import REMINDER_OPTIONS, REPEAT_TYPES, PLANS, LOCAL_TZ
from handlers.start import main_menu_keyboard

TITLE, DESCRIPTION, DATE_PICK, TIME_PICK, REMINDER, REPEAT, CUSTOM_INTERVAL = range(7)

async def safe_edit_message(query, text: str, reply_markup=None, parse_mode=None):
    try:
        await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode=parse_mode)
    except BadRequest as exc:
        if "Message is not modified" in str(exc):
            pass
        else:
            raise exc

async def new_task_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    user = db.get_user(user_id) or {"plan": "free"}
    plan_limit = PLANS.get(user.get("plan", "free"), PLANS["free"])["limit"]
    active_count = db.count_active_tasks(user_id)

    if active_count >= plan_limit:
        await safe_edit_message(
            query,
            f"⚠️ Sizning tarfingizdagi ({user.get('plan', 'free').upper()}) vazifalar limiti ({plan_limit} ta) to'ldi!\n\n"
            "Cheklovni kengaytirish uchun /account bo'limiga kiring.",
            reply_markup=main_menu_keyboard()
        )
        return ConversationHandler.END

    await safe_edit_message(query, "📝 Vazifa nomini (sarlavhasini) kiriting:")
    return TITLE

async def receive_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["title"] = update.message.text
    keyboard = [[InlineKeyboardButton("O'tkazib yuborish ⏭", callback_data="skip_desc")]]
    await update.message.reply_text(
        "📄 Vazifaga batafsil izoh/eslatma kiritasizmi?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return DESCRIPTION

async def receive_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["description"] = update.message.text
    return await prompt_date(update.message.reply_text)

async def skip_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["description"] = ""
    return await prompt_date(query.edit_message_text)

async def prompt_date(send_func):
    now = datetime.now(LOCAL_TZ)
    today_str = now.strftime("%d.%m.%Y")
    tomorrow_str = (now + timedelta(days=1)).strftime("%d.%m.%Y")
    day_after_str = (now + timedelta(days=2)).strftime("%d.%m.%Y")

    keyboard = [
        [InlineKeyboardButton(f"Bugun ({today_str[:5]})", callback_data=f"date_{today_str}")],
        [InlineKeyboardButton(f"Ertaga ({tomorrow_str[:5]})", callback_data=f"date_{tomorrow_str}")],
        [InlineKeyboardButton(f"Indinga ({day_after_str[:5]})", callback_data=f"date_{day_after_str}")],
        [InlineKeyboardButton("✍️ Boshqa sana kiritish", callback_data="date_manual")]
    ]
    await send_func("📅 Vazifa sanasini tanlang:", reply_markup=InlineKeyboardMarkup(keyboard))
    return DATE_PICK

async def receive_date_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("_")[1]

    if data == "manual":
        await safe_edit_message(query, "📅 Sanani KK.OO.YYYY ko'rinishida yozing (masalan: 25.12.2026):")
        return DATE_PICK

    context.user_data["date"] = datetime.strptime(data, "%d.%m.%Y")
    return await prompt_time(query.edit_message_text)

async def receive_date_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        context.user_data["date"] = datetime.strptime(text, "%d.%m.%Y")
    except ValueError:
        await update.message.reply_text("❌ Noto'g'ri format. KK.OO.YYYY formatida yozing:")
        return DATE_PICK
    return await prompt_time(update.message.reply_text)

async def prompt_time(send_func):
    keyboard = [
        [InlineKeyboardButton("09:00", callback_data="time_09:00"), InlineKeyboardButton("12:00", callback_data="time_12:00")],
        [InlineKeyboardButton("15:00", callback_data="time_15:00"), InlineKeyboardButton("18:00", callback_data="time_18:00")],
        [InlineKeyboardButton("21:00", callback_data="time_21:00"), InlineKeyboardButton("⏳ 1 soatdan keyin", callback_data="time_plus1h")],
        [InlineKeyboardButton("✍️ Boshqa vaqt", callback_data="time_manual")]
    ]
    await send_func("⏰ Vaqtni tanlang:", reply_markup=InlineKeyboardMarkup(keyboard))
    return TIME_PICK

async def receive_time_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data.split("_")[1]

    if choice == "manual":
        await safe_edit_message(query, "⏰ Vaqtni SS:DD ko'rinishida yozing (masalan: 14:30):")
        return TIME_PICK

    if choice == "plus1h":
        target = datetime.now(LOCAL_TZ) + timedelta(hours=1)
        due = target.replace(second=0, microsecond=0)
    else:
        hour, minute = map(int, choice.split(":"))
        date_obj = context.user_data["date"]
        due = date_obj.replace(hour=hour, minute=minute)

    context.user_data["due_datetime"] = due.isoformat()
    return await prompt_reminder(query.edit_message_text)

async def receive_time_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        parsed_time = datetime.strptime(text, "%H:%M")
    except ValueError:
        await update.message.reply_text("❌ Noto'g'ri vaqt formati. SS:DD ko'rinishida yozing:")
        return TIME_PICK

    date_obj = context.user_data["date"]
    due = date_obj.replace(hour=parsed_time.hour, minute=parsed_time.minute)
    context.user_data["due_datetime"] = due.isoformat()
    return await prompt_reminder(update.message.reply_text)

async def prompt_reminder(send_func):
    keyboard = [
        [InlineKeyboardButton(f"{label} daqiqa oldin", callback_data=f"rem_{minutes}")]
        for label, minutes in REMINDER_OPTIONS.items()
    ]
    keyboard.append([InlineKeyboardButton("Eslatma kerak emas", callback_data="rem_0")])
    await send_func("🔔 Qancha vaqt oldin eslatilsin?", reply_markup=InlineKeyboardMarkup(keyboard))
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
    await safe_edit_message(query, "🔁 Takrorlanish turini tanlang:", reply_markup=InlineKeyboardMarkup(keyboard))
    return REPEAT

async def receive_repeat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    repeat_type = query.data.split("_")[1]
    context.user_data["repeat_type"] = repeat_type

    if repeat_type == "custom":
        await safe_edit_message(query, "🔢 Necha kunda bir marta takrorlansin? (musbat son yozing):")
        return CUSTOM_INTERVAL

    return await save_task(update, context)

async def receive_custom_interval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit() or int(text) <= 0:
        await update.message.reply_text("❌ Musbat son kiriting:")
        return CUSTOM_INTERVAL
    context.user_data["repeat_interval_days"] = int(text)
    return await save_task(update, context, from_message=True)

async def save_task(update: Update, context: ContextTypes.DEFAULT_TYPE, from_message: bool = False):
    user_id = update.effective_user.id
    data = context.user_data

    db.add_task(
        user_id=user_id,
        title=data["title"],
        description=data.get("description", ""),
        due_datetime=data["due_datetime"],
        reminder_minutes_before=data.get("reminder_minutes", 0),
        repeat_type=data.get("repeat_type", "none"),
        repeat_interval_days=data.get("repeat_interval_days"),
    )

    due = datetime.fromisoformat(data["due_datetime"])
    desc_part = f"\n📄 Izoh: {data['description']}" if data.get("description") else ""
    text = (
        f"✅ Vazifa muvaffaqiyatli saqlandi!\n\n"
        f"📌 Sarlavha: *{data['title']}*{desc_part}\n"
        f"📅 Muddat: {due.strftime('%d.%m.%Y %H:%M')}\n"
        f"🔔 Eslatma: {data.get('reminder_minutes', 0)} daqiqa oldin\n"
        f"🔁 Takrorlanish: {REPEAT_TYPES.get(data.get('repeat_type', 'none'))}"
    )

    if from_message:
        await update.message.reply_text(text, reply_markup=main_menu_keyboard(), parse_mode="Markdown")
    else:
        await safe_edit_message(update.callback_query, text, reply_markup=main_menu_keyboard(), parse_mode="Markdown")

    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Bekor qilindi.", reply_markup=main_menu_keyboard())
    return ConversationHandler.END

async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    tasks = db.get_user_tasks(user_id, status="active")

    if not tasks:
        await safe_edit_message(query, "📋 Faol vazifalar yo'q.", reply_markup=main_menu_keyboard())
        return

    await safe_edit_message(query, "📋 *Sizning faol vazifalaringiz:*", reply_markup=main_menu_keyboard(), parse_mode="Markdown")

    for task in tasks:
        due = datetime.fromisoformat(task["due_datetime"])
        desc_line = f"\n📄 {task['description']}" if task.get("description") else ""
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Bajarildi", callback_data=f"complete_{task['task_id']}"),
                InlineKeyboardButton("🗑 O'chirish", callback_data=f"delete_{task['task_id']}"),
            ]
        ])
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"📌 *{task['title']}*{desc_line}\n📅 {due.strftime('%d.%m.%Y %H:%M')}",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

async def list_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    tasks = db.get_user_tasks(user_id, status="done")

    if not tasks:
        await safe_edit_message(query, "✅ Bajarilgan vazifalar yo'q.", reply_markup=main_menu_keyboard())
        return

    lines = ["✅ *Bajarilgan vazifalar:*\n"]
    for task in tasks:
        due = datetime.fromisoformat(task["due_datetime"])
        lines.append(f"• {task['title']} ({due.strftime('%d.%m.%Y %H:%M')})")

    await safe_edit_message(query, "\n".join(lines), reply_markup=main_menu_keyboard(), parse_mode="Markdown")

async def complete_task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Vazifa bajarildi! ✅")
    task_id = int(query.data.split("_")[1])
    db.complete_task(task_id)
    await safe_edit_message(query, "✅ Vazifa bajarildi deb belgilandi.")

async def delete_task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("O'chirildi 🗑")
    task_id = int(query.data.split("_")[1])
    db.delete_task(task_id)
    await safe_edit_message(query, "🗑 Vazifa o'chirildi.")
