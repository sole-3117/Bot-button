import logging
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import BOT_TOKEN
import database as db
from handlers.start import start_command
from handlers.account import (
    account_command,
    buy_plan_start,
    plan_selected,
    receive_receipt,
    cancel_payment,
    admin_payment_decision,
    SELECT_PLAN,
    SEND_RECEIPT,
)
from handlers.task_handlers import (
    new_task_start,
    receive_title,
    receive_description,
    skip_description,
    receive_date_callback,
    receive_date_text,
    receive_time_callback,
    receive_time_text,
    receive_reminder,
    receive_repeat,
    receive_custom_interval,
    list_tasks,
    list_done,
    complete_task_callback,
    delete_task_callback,
    cancel,
    TITLE,
    DESCRIPTION,
    DATE_PICK,
    TIME_PICK,
    REMINDER,
    REPEAT,
    CUSTOM_INTERVAL,
)
from handlers.admin import (
    admin_start,
    admin_refresh,
    give_plan_start,
    receive_target_user,
    receive_plan_choice,
    admin_cancel,
    GIVE_PLAN_USER,
    GIVE_PLAN_CHOOSE,
)
from utils.scheduler import check_tasks

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

async def post_init(application):
    """Event loop to'liq ishga tushgandan so'ng schedulerni start qiladi."""
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_tasks, "interval", minutes=1, args=[application])
    scheduler.start()
    application.bot_data["scheduler"] = scheduler
    logging.info("AsyncIOScheduler muvaffaqiyatli ishga tushirildi.")

async def post_shutdown(application):
    """Bot to'xtaganda schedulerni ham toza yopadi."""
    scheduler = application.bot_data.get("scheduler")
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
        logging.info("AsyncIOScheduler to'xtatildi.")

def main():
    # PostgreSQL bazasini initsializatsiya qilish
    db.init_db()

    # ApplicationBuilder ga post_init va post_shutdown hooklarini ulaymiz
    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    # Yangi vazifa qo'shish jarayoni
    task_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(new_task_start, pattern="^new_task$")],
        states={
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_title)],
            DESCRIPTION: [
                CallbackQueryHandler(skip_description, pattern="^skip_desc$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_description),
            ],
            DATE_PICK: [
                CallbackQueryHandler(receive_date_callback, pattern="^date_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_date_text),
            ],
            TIME_PICK: [
                CallbackQueryHandler(receive_time_callback, pattern="^time_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_time_text),
            ],
            REMINDER: [CallbackQueryHandler(receive_reminder, pattern="^rem_")],
            REPEAT: [CallbackQueryHandler(receive_repeat, pattern="^rep_")],
            CUSTOM_INTERVAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_custom_interval)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
    )

    # Shaxsiy kabinet / To'lov jarayoni
    account_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(buy_plan_start, pattern="^buy_plan$")],
        states={
            SELECT_PLAN: [
                CallbackQueryHandler(plan_selected, pattern="^plan_"),
                CallbackQueryHandler(cancel_payment, pattern="^cancel_payment$"),
            ],
            SEND_RECEIPT: [MessageHandler(filters.PHOTO, receive_receipt)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
    )

    # Admin: Tarif berish jarayoni
    admin_plan_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(give_plan_start, pattern="^admin_give_plan$")],
        states={
            GIVE_PLAN_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_target_user)],
            GIVE_PLAN_CHOOSE: [CallbackQueryHandler(receive_plan_choice, pattern="^setplan_")],
        },
        fallbacks=[CommandHandler("cancel", admin_cancel)],
        per_message=False,
    )

    # Asosiy buyruqlar
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("account", account_command))
    app.add_handler(CommandHandler("admin", admin_start))

    # Suhbatlarni ro'yxatdan o'tkazish
    app.add_handler(task_conv)
    app.add_handler(account_conv)
    app.add_handler(admin_plan_conv)

    # Callbacklar
    app.add_handler(CallbackQueryHandler(account_command, pattern="^(open_account|refresh_account)$"))
    app.add_handler(CallbackQueryHandler(admin_refresh, pattern="^admin_refresh$"))
    app.add_handler(CallbackQueryHandler(admin_payment_decision, pattern="^pay_(ok|no)_"))
    app.add_handler(CallbackQueryHandler(list_tasks, pattern="^list_tasks$"))
    app.add_handler(CallbackQueryHandler(list_done, pattern="^list_done$"))
    app.add_handler(CallbackQueryHandler(complete_task_callback, pattern="^complete_"))
    app.add_handler(CallbackQueryHandler(delete_task_callback, pattern="^delete_"))

    logging.info("Rejachi bot (dev) muvaffaqiyatli ishga tushdi.")
    app.run_polling()

if __name__ == "__main__":
    main()
