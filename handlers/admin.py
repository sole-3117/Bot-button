import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler

from config import ADMIN_IDS, LOCAL_TZ, PLANS
import database as db

logger = logging.getLogger(__name__)

# GIVE_PLAN holatlari
GIVE_PLAN_USER, GIVE_PLAN_CHOOSE = range(2)

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS
