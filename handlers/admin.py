import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler

from config import ADMIN_IDS, LOCAL_TZ, PLANS
import database as db

logger = logging.getLogger(__name__)

GIVE_PLAN_USER, GIVE_PLAN_CHOOSE = range(2)

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

def build_admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Yangilash", callback_data="admin_refresh")],
        [InlineKeyboardButton("🎁 Foydalanuvchiga tarif berish", callback_data="admin_give_plan")]
    ])

async def admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return

    stats = db.get_admin_stats()
    plans_text = "\n".join([f"  • {p.upper()}: {cnt} ta" for p, cnt in stats["plans"].items()])
    
    text = (
        "👑 <b>Admin Boshqaruv Paneli</b>\n\n"
        f"👥 <b>Jami foydalanuvchilar:</b> {stats['total_users']}\n"
        f"📊 <b>Tariflar bo'yicha:</b>\n{plans_text if plans_text else '  • Ma\'lumot yo\'q'}\n"
        f"📝 <b>Jami vazifalar:</b> {stats['total_tasks']}"
    )

    if update.message:
        await update.message.reply_text(text, reply_markup=build_admin_keyboard(), parse_mode="HTML")
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=build_admin_keyboard(), parse_mode="HTML")

async def admin_refresh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Ma'lumotlar yangilandi 🔄")
    await admin_start(update, context)

async def give_plan_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await query.answer("Ruxsat yo'q!", show_alert=True)
        return ConversationHandler.END

    await query.answer()
    await query.edit_message_text(
        "Foydalanuvchining <b>Telegram ID</b> raqamini yuboring:\n\n"
        "Bekor qilish uchun /cancel buyrug'ini bosing.",
        parse_mode="HTML"
    )
    return GIVE_PLAN_USER

async def receive_target_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("Iltimos, faqat raqamlardan iborat to'g'ri Telegram ID kiriting:")
        return GIVE_PLAN_USER

    target_id = int(text)
    user = db.get_user(target_id)
    if not user:
        await update.message.reply_text("Bu ID ga ega foydalanuvchi bot bazasidan topilmadi. Qaytadan urinib ko'ring:")
        return GIVE_PLAN_USER

    context.user_data["target_user_id"] = target_id
    
    buttons = [
        [InlineKeyboardButton(f"{p_data['name']} ({p_data['price']:,} so'm)", callback_data=f"setplan_{p_name}")]
        for p_name, p_data in PLANS.items() if p_name != "free"
    ]
    buttons.append([InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_payment")])

    await update.message.reply_text(
        f"Foydalanuvchi: <b>{user.get('full_name', 'N/A')}</b> (ID: <code>{target_id}</code>)\n"
        f"Hozirgi tarifi: <b>{user.get('plan', 'free').upper()}</b>\n\n"
        "Qaysi tarifni bermoqchisiz?",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="HTML"
    )
    return GIVE_PLAN_CHOOSE

async def receive_plan_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    plan_name = query.data.split("_")[1]
    target_id = context.user_data.get("target_user_id")

    if not target_id or plan_name not in PLANS:
        await query.edit_message_text("Xatolik yuz berdi. Qaytadan urinib ko'ring.")
        return ConversationHandler.END

    # To'g'ridan-to'g'ri limitlarni belgilash
    plan_data = PLANS[plan_name]
    days = plan_data['duration_days']
    until = (datetime.now(LOCAL_TZ) + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")

    conn = db.get_connection()
    c = conn.cursor()
    c.execute("""
        UPDATE users 
        SET plan = %s, subscription_until = %s, tasks_limit = %s, voice_limit = %s, sms_limit = %s 
        WHERE user_id = %s;
    """, (plan_name, until, plan_data['max_tasks'], plan_data['max_voice'], plan_data['max_sms'], target_id))
    conn.commit()
    conn.close()

    await query.edit_message_text(
        f"✅ Foydalanuvchiga (ID: <code>{target_id}</code>) <b>{plan_name.upper()}</b> tarifi muvaffaqiyatli berildi!",
        parse_mode="HTML"
    )

    try:
        await context.bot.send_message(
            chat_id=target_id,
            text=f"🎉 Sizga admin tomonidan <b>{plan_name.upper()}</b> tarifi taqdim etildi!",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.warning(f"Foydalanuvchiga xabar yuborib bo'lmadi: {e}")

    context.user_data.clear()
    return ConversationHandler.END

async def admin_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Amaliyot bekor qilindi.")
    return ConversationHandler.END
