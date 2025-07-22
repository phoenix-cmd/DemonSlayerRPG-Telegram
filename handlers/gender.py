from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.db import get_players

async def gender_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    gender = "male" if query.data == "gender_male" else "female"
    telegram_id = query.from_user.id
    name = query.from_user.full_name
    players = get_players()

    # Upsert user with initial data
    players.update_one(
        {'telegram_id': telegram_id},
        {'$set': {
            'name': name,
            'gender': gender,
            'level': 1,
            'exp': 0,
            'location': 'starting_village',
            'items': [],
            'created_at': datetime.datetime.utcnow()
        }},
        upsert=True
    )

    await query.edit_message_text(
        "Choose your game mode:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📖 Story Mode", callback_data="mode_story")],
            [InlineKeyboardButton("🌍 Explore Mode", callback_data="mode_explore")]
        ])
    )
