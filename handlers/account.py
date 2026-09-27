from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from config import ADMIN_IDS
import database as db

SELECT_PLAN, SEND_RECEIPT = range(2)

def get_current_plans():
    st = db.get_all_settings()
    return {
        "free": {"name": "Oddiy (Free)", "price": 0, "limit": int(st.get("free_limit", 5))},
        "pro": {"name": "Pro Rejachi", "price": int(st.get("pro_price", 15000)), "limit": int(st.get("pro_limit", 30))},
        "vip": {"name": "VIP Cheksiz", "price": int(st.get("vip_price", 30000)), "limit": int(st.get("vip_limit", 999999))},
    }

async def account_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    if not user:
        db.register_user(user_id, update.effective_user.username or "", update.effective_user.full_name or "")
        user = db.get_user(user_id)

    plans = get_current_plans()
    plan = user.get("plan", "free")
    plan_info = plans.get(plan, plans["free"])
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
        try:
            await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        except Exception:
            pass
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def buy_plan_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    plans = get_current_plans()

    text = (
        "💎 *Mavjud tariflar:*\n\n"
        f"1️⃣ *Pro Rejachi* — {plans['pro']['price']:,} so'm / oy\n"
        f"• {plans['pro']['limit']} tagacha faol vazifalar\n"
        "• Barcha qulay eslatmalar\n\n"
        f"2️⃣ *VIP Cheksiz* — {plans['vip']['price']:,} so'm / oy\n"
        f"• {plans['vip']['limit'] if plans['vip']['limit'] < 999999 else 'Cheksiz'} vazifalar\n\n"
        "O'zingizga ma'qul tarifni tanlang:"
    )
    keyboard = [
        [InlineKeyboardButton(f"⚡️ Pro ({plans['pro']['price']:,} so'm)", callback_data="plan_pro")],
        [InlineKeyboardButton(f"👑 VIP ({plans['vip']['price']:,} so'm)", callback_data="plan_vip")],
        [InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_payment")]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return SELECT_PLAN

async def plan_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    plan_key = query.data.split("_")[1]
    context.user_data["selected_plan"] = plan_key
    
    plans = get_current_plans()
    plan_info = plans[plan_key]
    card_number = db.get_setting("payment_card", "8600 0000 0000 0000")
    card_owner = db.get_setting("payment_owner", "ISM FAMILIYA")

    text = (
        f"💳 To'lov: *{plan_info['name']}*\n"
        f"💵 Summa: *{plan_info['price']:,} so'm*\n\n"
        f"Karta raqami: `{card_number}`\n"
        f"Qabul qiluvchi: *{card_owner}*\n\n"
        "Iltimos, to'lovni amalga oshirib, **chek rasmini (skrinshot)** yuboring:"
    )
    await query.edit_message_text(text, parse_mode="Markdown")
    return SEND_RECEIPT

async def receive_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    plan_key = context.user_data.get("selected_plan", "pro")
    user = update.effective_user
    plans = get_current_plans()

    req_id = db.add_payment_request(user.id, plan_key, photo.file_id)

    await update.message.reply_text("✅ To'lov cheki qabul qilindi! Admin tasdiqlashi bilan tarif faollashtiriladi.")

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
                        f"💎 Tarif: *{plans[plan_key]['name']}*\n"
                        f"💰 Summa: {plans[plan_key]['price']:,} so'm",
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

async def admin_payment_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("_")
    action = data[1]
    req_id = int(data[2])
    plans = get_current_plans()

    if action == "ok":
        req = db.approve_payment(req_id)
        if req:
            await query.edit_message_caption(caption=f"{query.message.caption}\n\n✅ *TASDIQLANDI*")
            try:
                await context.bot.send_message(
                    chat_id=req["user_id"],
                    text=f"🎉 To'lovingiz tasdiqlandi! *{plans.get(req['plan'], {}).get('name', req['plan'])}* tarifi 30 kunga faollashtirildi!",
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
