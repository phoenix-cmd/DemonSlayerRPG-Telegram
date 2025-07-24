# handlers/travel.py

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

import os

# Import your region config and Player model/class
from config.regions import REGIONS
from models.player import Player

# Prepare MongoDB client/col
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
mongo_client = AsyncIOMotorClient(MONGODB_URI)
db = mongo_client["demon_slayer_rpg"]
players_col = db["players"]

async def travel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main travel command – shows options from the current region."""
    user_id = update.effective_user.id
    player_doc = await players_col.find_one({"telegram_id": user_id})
    if not player_doc:
        await update.message.reply_text("You must register before you can travel! Use /start.")
        return

    player = Player.from_dict(player_doc)
    current_region = REGIONS.get(player.location)
    if not current_region:
        await update.message.reply_text("Current region not found in game config. Contact the admin.")
        return

    # Show available connected routes as destinations
    destinations = current_region["connected_routes"]
    keyboard = [
        [InlineKeyboardButton(dest, callback_data=f"travel::{dest}")]
        for dest in destinations
    ]
    await update.message.reply_text(
        f"You are in *{player.location}*.\n\n{current_region['lore']}\n\n"
        "Where do you want to travel?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def handle_travel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles inline travel button presses."""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    player_doc = await players_col.find_one({"telegram_id": user_id})
    if not player_doc:
        await query.edit_message_text("You must register before you can travel!")
        return
    player = Player.from_dict(player_doc)

    data = query.data
    if not data.startswith("travel::"):
        return

    dest_region = data[len("travel::") :]
    if dest_region not in REGIONS:
        await query.edit_message_text("That region doesn't exist!")
        return

    # Only allow travel to connected routes
    current_region = REGIONS.get(player.location)
    if dest_region not in current_region["connected_routes"]:
        await query.edit_message_text("You cannot travel directly there from here.")
        return

    # Update location in DB
    await players_col.update_one(
        {"telegram_id": user_id},
        {"$set": {"location": dest_region, "last_active": datetime.utcnow()}}
    )

    # Feedback with new region’s lore
    lore = REGIONS[dest_region]["lore"]
    await query.edit_message_text(
        f"🗺️ You have traveled to *{dest_region}*.\n\n{lore}",
        parse_mode="Markdown"
    )

def get_travel_handlers():
    """Returns handlers for bot setup."""
    return [
        CommandHandler("travel", travel),
        CallbackQueryHandler(handle_travel_callback, pattern="^travel::"),
    ]

