# handlers/explore.py

import os
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from motor.motor_asyncio import AsyncIOMotorClient
from models.player import Player
from config.regions import REGIONS

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
mongo_client = AsyncIOMotorClient(MONGODB_URI)
db = mongo_client["demon_slayer_rpg"]
players_col = db["players"]

# We assume combat module has start_combat async function accepting post-combat callback
from handlers import combat  # adjust if your path differs

async def explore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    player_doc = await players_col.find_one({"telegram_id": user_id})
    if not player_doc:
        await update.message.reply_text("You must register before exploring. Use /start.")
        return

    player = Player.from_dict(player_doc)

    if player.has_explored:
        await update.message.reply_text("You have already explored here. Travel forward or backward first!")
        return

    region = REGIONS.get(player.location)
    if not region:
        await update.message.reply_text("This location cannot be explored right now. Contact admin.")
        return

    demons = region["encounters"].get("demons", [])
    if not demons:
        await update.message.reply_text("You find no enemies here to battle.")
        await players_col.update_one({"telegram_id": user_id}, {"$set": {"has_explored": True}})
        return

    demon = random.choice(demons)
    await update.message.reply_text(
        f"As you explore *{player.location}*, a *{demon}* appears! Prepare for battle.",
        parse_mode="Markdown"
    )

    # Mark as explored to prevent repeated explores in the same location/step
    await players_col.update_one(
        {"telegram_id": user_id},
        {"$set": {"has_explored": True}}
    )

    # Start combat with callback to handle post-combat options
    await combat.start_combat(update, context, enemy=demon, post_combat_callback=post_combat_conclusion)


async def post_combat_conclusion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """To be called by combat system after battle is resolved."""

    user_id = update.effective_user.id
    player_doc = await players_col.find_one({"telegram_id": user_id})
    if not player_doc:
        # Defensive check
        await update.message.reply_text("Player data lost. Please start again.")
        return
    player = Player.from_dict(player_doc)

    # Determine available directions
    # If player is on a route, show forward/backward buttons for that route
    if player.current_route:
        route_name = player.current_route
        steps = None
        if route_name in context.bot_data.get("routes", {}):
            steps = context.bot_data["routes"][route_name]["steps"]
        else:
            # fallback, import routes config for safety
            from config.routes import ROUTES
            steps = ROUTES.get(route_name, {}).get("steps", 0)

        progress = player.path_progress
        buttons = []

        # Backward button if can go back
        if progress > 0:
            buttons.append(
                InlineKeyboardButton("⬅️ Backward", callback_data=f"travel::{route_name}::backward")
            )
        # Forward button if not at end
        if progress < steps:
            buttons.append(
                InlineKeyboardButton("➡️ Forward", callback_data=f"travel::{route_name}::forward")
            )

        if not buttons:
            # No moves possible: maybe player is stuck, but handle gracefully
            await update.message.reply_text(
                f"You stand your ground at {player.location}. No apparent path forward or backward."
            )
            return

        keyboard = InlineKeyboardMarkup([buttons])
        await update.message.reply_text(
            "The battle is over. Which way will you go next?",
            reply_markup=keyboard
        )
    else:
        # Not on a route but in a main region - suggest travel normally
        current_region = REGIONS.get(player.location)
        if not current_region:
            await update.message.reply_text("Location invalid. Contact admin.")
            return
        
        destinations = current_region.get("connected_routes", [])
        buttons = [InlineKeyboardButton(dest, callback_data=f"travel::{dest}") for dest in destinations]
        
        keyboard = InlineKeyboardMarkup([[button] for button in buttons])
        await update.message.reply_text(
            "The battle is over. Where to next?",
            reply_markup=keyboard
        )

def get_explore_handler():
    from telegram.ext import CommandHandler
    return CommandHandler("explore", explore)
