from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from config import ADMIN_IDS
import database as db

# State
GIVE_PLAN_USER, GIVE_PLAN_CHOOSE = range(2)

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

async def admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("⛔️ Siz admin emassiz.")
        return

    stats = db.get_admin_stats()
    text = (
        "👑 *Admin Boshqaruv Paneli*\n\n"
        f"👥 Umumiy foydalanuvchilar: {stats['total_users']}\n"
        f"• Free: {stats['plans'].get('free', 0)}\n"
        f"• Pro: {stats['plans'].get('pro', 0)}\n"
        f"• VIP: {stats['plans'].get('vip', 0)}\n\n"
        f"📝 Jami vazifalar: {stats['total_tasks']}\n"
    )

    keyboard = [
        [InlineKeyboardButton("⭐️ Tarif berish", callback_data="admin_give_plan")],
        [InlineKeyboardButton("📊 Yangilash", callback_data="admin_refresh")]
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def admin_refresh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    stats = db.get_admin_stats()
    text = (
        "👑 *Admin Boshqaruv Paneli*\n\n"
        f"👥 Umumiy foydalanuvchilar: {stats['total_users']}\n"
        f"• Free: {stats['plans'].get('free', 0)}\n"
        f"• Pro: {stats['plans'].get('pro', 0)}\n"
        f"• VIP: {stats['plans'].get('vip', 0)}\n\n"
        f"📝 Jami vazifalar: {stats['total_tasks']}\n"
    )
    keyboard = [
        [InlineKeyboardButton("⭐️ Tarif berish", callback_data="admin_give_plan")],
        [InlineKeyboardButton("📊 Yangilash", callback_data="admin_refresh")]
    ]
    try:
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    except Exception:
        pass

async def give_plan_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Foydalanuvchining **Telegram ID** sini yuboring:")
    return GIVE_PLAN_USER

async def receive_target_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("❌ ID faqat raqamlardan iborat boʻlishi kerak. Qaytadan kiriting:")
        return GIVE_PLAN_USER

    target_id = int(text)
    user = db.get_user(target_id)
    if not user:
        await update.message.reply_text("❌ Foydalanuvchi bazadan topilmadi. Avval u botga /start bosgan boʻlishi kerak.")
        return GIVE_PLAN_USER

    context.user_data["target_user_id"] = target_id
    keyboard = [
        [InlineKeyboardButton("Free (Cheklovli)", callback_data="setplan_free")],
        [InlineKeyboardButton("Pro (30 kun)", callback_data="setplan_pro")],
        [InlineKeyboardButton("VIP (30 kun)", callback_data="setplan_vip")]
    ]
    await update.message.reply_text(
        f"Foydalanuvchi: {user['full_name']} (Hozirgi tarifi: {user['plan']})\nQaysi tarifni berasiz?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return GIVE_PLAN_CHOOSE

async def receive_plan_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    plan = query.data.split("_")[1]
    target_id = context.user_data.get("target_user_id")

    db.update_user_plan(target_id, plan, days=30)
    await query.edit_message_text(f"✅ Foydalanuvchi `{target_id}` uchun **{plan.upper()}** tarifi 30 kunga faollashtirildi!", parse_mode="Markdown")

    # Foydalanuvchiga xushxabar yuborish
    try:
        await context.bot.send_message(
            chat_id=target_id,
            text=f"🎉 Tabriklaymiz! Sizning profilingizga **{plan.upper()}** tarifi faollashtirildi.",
            parse_mode="Markdown"
        )
    except Exception:
        pass

    context.user_data.clear()
    return ConversationHandler.END

async def admin_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Bekor qilindi.")
    return ConversationHandler.END
