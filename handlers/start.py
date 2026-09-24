# handlers/start.py ichidagi start funksiyasiga qo'shiladi:
from database import register_user

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user.id, user.username or "", user.full_name or "")
    # ... qolgan start menyusi kodi ...
