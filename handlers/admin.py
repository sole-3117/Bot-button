from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from config import ADMIN_IDS
import database as db

GIVE_PLAN_USER, GIVE_PLAN_CHOOSE = range(2)
SETTING_VALUE = 2

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
        [InlineKeyboardButton("⚙️ Bot Sozlamalari (Narx/Karta)", callback_data="admin_settings")],
        [InlineKeyboardButton("⭐️ Qo'lda tarif berish", callback_data="admin_give_plan")],
        [InlineKeyboardButton("📊 Yangilash", callback_data="admin_refresh")]
    ]
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def admin_refresh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await admin_start(update, context)

# ---------- Sozlamalar menyusi ----------
async def admin_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    st = db.get_all_settings()

    text = (
        "⚙️ *Joriy bot sozlamalari:*\n\n"
        f"💳 Karta raqam: `{st.get('payment_card')}`\n"
        f"👤 Karta egasi: *{st.get('payment_owner')}*\n\n"
        f"⚡️ Pro narxi: *{int(st.get('pro_price', 0)):,} so'm* | Limiti: {st.get('pro_limit')} ta\n"
        f"👑 VIP narxi: *{int(st.get('vip_price', 0)):,} so'm* | Limiti: {st.get('vip_limit')} ta\n"
        f"🆓 Free limiti: *{st.get('free_limit')} ta*\n\n"
        "O'zgartirmoqchi bo'lgan ma'lumotingizni tanlang:"
    )

    keyboard = [
        [InlineKeyboardButton("💳 Kartani o'zgartirish", callback_data="set_payment_card")],
        [InlineKeyboardButton("👤 Karta egasini o'zgartirish", callback_data="set_payment_owner")],
        [InlineKeyboardButton("⚡️ Pro narxi", callback_data="set_pro_price"), InlineKeyboardButton("⚡️ Pro limiti", callback_data="set_pro_limit")],
        [InlineKeyboardButton("👑 VIP narxi", callback_data="set_vip_price"), InlineKeyboardButton("👑 VIP limiti", callback_data="set_vip_limit")],
        [InlineKeyboardButton("🆓 Free limiti", callback_data="set_free_limit")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="admin_refresh")]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def setting_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    key = query.data.replace("set_", "")
    context.user_data["editing_setting_key"] = key

    prompts = {
        "payment_card": "💳 Yangi karta raqamini kiriting (masalan: 9860 1234 5678 9012):",
        "payment_owner": "👤 Yangi karta egasining to'liq ismini kiriting:",
        "pro_price": "⚡️ Pro tarifi uchun yangi narxni kiriting (faqat son, masalan: 20000):",
        "pro_limit": "⚡️ Pro tarifi uchun vazifalar soni limitini kiriting:",
        "vip_price": "👑 VIP tarifi uchun yangi narxni kiriting (faqat son, masalan: 40000):",
        "vip_limit": "👑 VIP tarifi uchun vazifalar limiti (cheksiz bo'lsa 999999):",
        "free_limit": "🆓 Free (bepul) tarifi uchun ruxsat etilgan vazifalar sonini kiriting:"
    }
    await query.edit_message_text(prompts.get(key, "Yangi qiymatni kiriting:") + "\n\nBekor qilish uchun /cancel yozing.")
    return SETTING_VALUE

async def receive_setting_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_val = update.message.text.strip()
    key = context.user_data.get("editing_setting_key")

    if key in ["pro_price", "pro_limit", "vip_price", "vip_limit", "free_limit"]:
        if not new_val.isdigit():
            await update.message.reply_text("❌ Iltimos, faqat musbat butun son kiriting:")
            return SETTING_VALUE

    db.set_setting(key, new_val)
    context.user_data.clear()
    
    await update.message.reply_text(
        f"✅ Sozlama muvaffaqiyatli saqlandi!\n`{key}` = `{new_val}`",
        parse_mode="Markdown"
    )
    return ConversationHandler.END

# ---------- Qo'lda tarif berish ----------
async def give_plan_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Foydalanuvchining **Telegram ID** sini yuboring:\nBekor qilish uchun /cancel")
    return GIVE_PLAN_USER

async def receive_target_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("❌ ID faqat raqamlardan iborat bo'ladi. Qaytadan kiriting:")
        return GIVE_PLAN_USER

    target_id = int(text)
    user = db.get_user(target_id)
    if not user:
        await update.message.reply_text("❌ Foydalanuvchi bazadan topilmadi (/start bosmagan bo'lishi mumkin).")
        return GIVE_PLAN_USER

    context.user_data["target_user_id"] = target_id
    keyboard = [
        [InlineKeyboardButton("Free (Cheklovli)", callback_data="setplan_free")],
        [InlineKeyboardButton("Pro (30 kun)", callback_data="setplan_pro")],
        [InlineKeyboardButton("VIP (30 kun)", callback_data="setplan_vip")]
    ]
    await update.message.reply_text(
        f"Foydalanuvchi: {user['full_name']} (Hozirgi: {user['plan']})\nQaysi tarifni berasiz?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return GIVE_PLAN_CHOOSE

async def receive_plan_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    plan = query.data.split("_")[1]
    target_id = context.user_data.get("target_user_id")

    conn = db.get_connection()
    c = conn.cursor()
    from datetime import timedelta
    from config import LOCAL_TZ
    until = (datetime.now(LOCAL_TZ) + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
    c.execute("UPDATE users SET plan = %s, subscription_until = %s WHERE user_id = %s;", (plan, until, target_id))
    conn.commit()
    conn.close()

    await query.edit_message_text(f"✅ `{target_id}` uchun **{plan.upper()}** tarifi berildi!", parse_mode="Markdown")
    try:
        await context.bot.send_message(
            chat_id=target_id,
            text=f"🎉 Sizga admin tomonidan **{plan.upper()}** tarifi faollashtirildi!",
            parse_mode="Markdown"
        )
    except Exception:
        pass

    context.user_data.clear()
    return ConversationHandler.END

async def admin_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Amal bekor qilindi.")
    return ConversationHandler.END
