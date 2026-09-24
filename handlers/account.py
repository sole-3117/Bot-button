from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from config import PLANS, PAYMENT_CARD, PAYMENT_OWNER, ADMIN_IDS
import database as db

SELECT_PLAN, SEND_RECEIPT = range(2)

async def account_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    if not user:
        db.register_user(user_id, update.effective_user.username or "", update.effective_user.full_name or "")
        user = db.get_user(user_id)

    plan = user.get("plan", "free")
    plan_info = PLANS.get(plan, PLANS["free"])
    active_tasks = db.count_active_tasks(user_id)
    sub_until = user.get("subscription_until") or "Cheklovlarsiz (Free)"

    text = (
        "👤 *Shaxsiy kabinet*\n\n"
        f"🆔 ID: `{user_id}`\n"
        f"⭐️ Hozirgi tarif: *{plan_info['name']}*\n"
        f"⏳ Amal qilish muddati: `{sub_until}`\n"
        f"📌 Faol vazifalar: {active_tasks} / {plan_info['limit']} ta\n\n"
        "Tarifingizni yangilamoqchimisiz?"
    )

    keyboard = [
        [InlineKeyboardButton("⭐️ Tarifni yangilash", callback_data="buy_plan")],
        [InlineKeyboardButton("🔄 Yangilash", callback_data="refresh_account")]
    ]
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def buy_plan_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    text = (
        "💎 *Mavjud tariflar:*\n\n"
        "1️⃣ *Pro Rejachi* — 15,000 so'm / oy\n"
        "• 30 tagacha faol vazifalar\n"
        "• Barcha qulay eslatmalar\n\n"
        "2️⃣ *VIP Cheksiz* — 30,000 so'm / oy\n"
        "• Cheksiz vazifalar\n"
        "• Birinchi navbatdagi qo'llab-quvvatlash\n\n"
        "O'zingizga ma'qul tarifni tanlang:"
    )
    keyboard = [
        [InlineKeyboardButton("⚡️ Pro (15,000 so'm)", callback_data="plan_pro")],
        [InlineKeyboardButton("👑 VIP (30,000 so'm)", callback_data="plan_vip")],
        [InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_payment")]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return SELECT_PLAN

async def plan_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    plan_key = query.data.split("_")[1]
    context.user_data["selected_plan"] = plan_key
    plan_info = PLANS[plan_key]

    text = (
        f"💳 To'lov: *{plan_info['name']}*\n"
        f"💵 Summa: *{plan_info['price']:,} so'm*\n\n"
        f"Karta raqami: `{PAYMENT_CARD}`\n"
        f"Qabul qiluvchi: *{PAYMENT_OWNER}*\n\n"
        "Iltimos, to'lovni amalga oshirib, **chek rasmini (skrinshot)** ushbu chatga yuboring:"
    )
    await query.edit_message_text(text, parse_mode="Markdown")
    return SEND_RECEIPT

async def receive_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    plan_key = context.user_data.get("selected_plan", "pro")
    user = update.effective_user

    req_id = db.add_payment_request(user.id, plan_key, photo.file_id)

    # Foydalanuvchiga javob
    await update.message.reply_text(
        "✅ To'lov cheki qabul qilindi!\nAdminlar tekshirib, 10-15 daqiqada tarifingizni faollashtiradi."
    )

    # Adminlarga yuborish
    admin_markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"pay_ok_{req_id}"),
            InlineKeyboardButton("❌ Rad etish", callback_data=f"pay_no_{req_id}")
        ]
    ])
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_photo(
                chat_id=admin_id,
                photo=photo.file_id,
                caption=f"🔔 *Yangi to'lov arizasi!* (#{req_id})\n\n"
                        f"👤 Foydalanuvchi: {user.full_name} (`{user.id}`)\n"
                        f"💎 Tarif: *{PLANS[plan_key]['name']}*\n"
                        f"💰 Summa: {PLANS[plan_key]['price']:,} so'm",
                reply_markup=admin_markup,
                parse_mode="Markdown"
            )
        except Exception:
            pass

    context.user_data.clear()
    return ConversationHandler.END

async def cancel_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("❌ To'lov bekor qilindi.")
    context.user_data.clear()
    return ConversationHandler.END

# Admin tasdiqlash callbacki
async def admin_payment_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("_")
    action = data[1]
    req_id = int(data[2])

    if action == "ok":
        req = db.approve_payment(req_id)
        if req:
            await query.edit_message_caption(caption=f"{query.message.caption}\n\n✅ *TASDIQLANDI*")
            try:
                await context.bot.send_message(
                    chat_id=req["user_id"],
                    text=f"🎉 Tabriklaymiz! To'lovingiz tasdiqlandi. *{PLANS[req['plan']]['name']}* tarifi 30 kunga faollashtirildi!",
                    parse_mode="Markdown"
                )
            except Exception:
                pass
    else:
        db.reject_payment(req_id)
        req = db.get_payment_request(req_id)
        await query.edit_message_caption(caption=f"{query.message.caption}\n\n❌ *RAD ETILDI*")
        if req:
            try:
                await context.bot.send_message(
                    chat_id=req["user_id"],
                    text="❌ To'lov chekingiz rad etildi. Savollar bo'lsa adminga murojaat qiling."
                )
            except Exception:
                pass
