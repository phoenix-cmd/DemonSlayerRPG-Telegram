from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"Welcome, {user.first_name}! Choose your gender:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("👦 Male", callback_data="gender_male"),
             InlineKeyboardButton("👧 Female", callback_data="gender_female")]
        ])
    )

