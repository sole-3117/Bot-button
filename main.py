import logging
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from config import BOT_TOKEN
import database as db
from utils.scheduler import check_tasks
from handlers.start import start, menu_callback
from handlers.task_handlers import (
    new_task_start,
    receive_title,
    receive_date,
    receive_time,
    receive_reminder,
    receive_repeat,
    receive_custom_interval,
    cancel,
    list_tasks,
    list_done,
    complete_task_callback,
    delete_task_callback,
    TITLE,
    DATE,
    TIME,
    REMINDER,
    REPEAT,
    CUSTOM_INTERVAL,
)
from handlers.admin import (
    backup_command,
    restore_start,
    restore_file_received,
    RESTORE_FILE,
    admin_cancel,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN topilmadi. .env faylida BOT_TOKEN ni belgilang.")

    db.init_db()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # /start
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(menu_callback, pattern="^menu$"))

    # Yangi vazifa yaratish (conversation)
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(new_task_start, pattern="^new_task$")],
        states={
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_title)],
            DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_date)],
            TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_time)],
            REMINDER: [CallbackQueryHandler(receive_reminder, pattern="^rem_")],
            REPEAT: [CallbackQueryHandler(receive_repeat, pattern="^rep_")],
            CUSTOM_INTERVAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_custom_interval)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(conv_handler)

    # Vazifalar roʻyxati
    app.add_handler(CallbackQueryHandler(list_tasks, pattern="^list_tasks$"))
    app.add_handler(CallbackQueryHandler(list_done, pattern="^list_done$"))
    app.add_handler(CallbackQueryHandler(complete_task_callback, pattern="^complete_"))
    app.add_handler(CallbackQueryHandler(delete_task_callback, pattern="^delete_"))

    # Admin (Backup va Restore) handlerlari
    app.add_handler(CommandHandler("backup", backup_command))

    restore_conv = ConversationHandler(
        entry_points=[CommandHandler("restore", restore_start)],
        states={
            RESTORE_FILE: [MessageHandler(filters.Document.ALL, restore_file_received)]
        },
        fallbacks=[CommandHandler("cancel", admin_cancel)],
        per_message=False,
    )
    app.add_handler(restore_conv)

    # Har daqiqada vazifalarni tekshirish (job_queue)
    app.job_queue.run_repeating(check_tasks, interval=60, first=5)

    logger.info("Rejachi bot ishga tushdi.")
    app.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
