from telegram import Update
from telegram.ext import ContextTypes
from utils.db import get_players

async def mode_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    mode = "story" if query.data == "mode_story" else "explore"
    telegram_id = query.from_user.id
    players = get_players()
    players.update_one(
        {'telegram_id': telegram_id},
        {'$set': {'mode': mode}}
    )
    if mode == "story":
        await query.edit_message_text("You have chosen Story Mode! Get ready for your adventure.")
    else:
        await query.edit_message_text("Explore Mode unlocked! Use /explore to begin your journey.")
