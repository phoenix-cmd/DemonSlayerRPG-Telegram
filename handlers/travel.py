# handlers/travel.py

import os
from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler
from motor.motor_asyncio import AsyncIOMotorClient
from models.player import Player
from config.regions import REGIONS
from config.routes import ROUTES

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
mongo_client = AsyncIOMotorClient(MONGODB_URI)
db = mongo_client["demon_slayer_rpg"]
players_col = db["players"]

async def travel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    player_doc = await players_col.find_one({"telegram_id": user_id})
    if not player_doc:
        await update.message.reply_text("You must register first! Use /start to begin.")
        return

    player = Player.from_dict(player_doc)

    # If currently on a route, show options to move forward/backward on the route
    if player.current_route:
        route_data = ROUTES.get(player.current_route)
        if not route_data:
            await update.message.reply_text("Route configuration error. Contact admin.")
            return
        
        max_steps = route_data["steps"]
        progress = player.path_progress

        keyboard = []
        # Add backward if possible
        if progress > 0:
            keyboard.append(
                InlineKeyboardButton("⬅️ Backward", callback_data=f"travel::{player.current_route}::backward")
            )
        # Add forward if possible
        if progress < max_steps:
            keyboard.append(
                InlineKeyboardButton("➡️ Forward", callback_data=f"travel::{player.current_route}::forward")
            )
        
        await update.message.reply_text(
            f"You are on *{player.current_route}* at step {progress}.\n{REGIONS.get(player.location, {}).get('lore', '')}\nWhich way will you go?",
            reply_markup=InlineKeyboardMarkup([keyboard]) if keyboard else None,
            parse_mode="Markdown"
        )
        return

    # Otherwise, normal region travel options
    current_region = REGIONS.get(player.location)
    if not current_region:
        await update.message.reply_text("Current region invalid. Contact admin.")
        return

    destinations = current_region["connected_routes"]
    keyboard = [
        [InlineKeyboardButton(dest, callback_data=f"travel::{dest}")]
        for dest in destinations
    ]

    await update.message.reply_text(
        f"You are in *{player.location}*.\n\n{current_region['lore']}\n\nWhere do you want to travel?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def handle_travel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    player_doc = await players_col.find_one({"telegram_id": user_id})
    if not player_doc:
        await query.edit_message_text("You must register first to travel.")
        return
    player = Player.from_dict(player_doc)

    data = query.data.split("::")
    if len(data) == 2:
        # Direct travel (region)
        dest_region = data[1]
        if dest_region not in REGIONS:
            await query.edit_message_text("Unknown destination.")
            return

        # If player is in a route currently, disallow
        if player.current_route:
            await query.edit_message_text("Finish current journey before moving to another region.")
            return

        # Check if destination is a connected route (region) from current region
        current_region = REGIONS.get(player.location)
        if dest_region not in current_region.get("connected_routes", []):
            await query.edit_message_text("You cannot travel there directly!")
            return

        # If this travel involves a route (start->end), transition player onto route steps
        route_name = None
        for route_key, route_val in ROUTES.items():
            if route_val["start"] == player.location and route_val["end"] == dest_region:
                route_name = route_key
                break
            if route_val["end"] == player.location and route_val["start"] == dest_region:
                route_name = route_key
                break

        if route_name:
            # Start route progress
            progress = 0
            # If going forward (start->end)
            moving_forward = ROUTES[route_name]["start"] == player.location
            progress = 1 if moving_forward else ROUTES[route_name]["steps"]
            new_location = f"{route_name} Step {progress}" if moving_forward else f"{route_name} Step {progress}"

            await players_col.update_one(
                {"telegram_id": user_id},
                {
                    "$set": {
                        "current_route": route_name,
                        "path_progress": progress,
                        "location": new_location,
                        "has_explored": False,
                        "last_active": datetime.utcnow()
                    }
                }
            )
            await query.edit_message_text(
                f"🛤️ You begin your journey on *{route_name}* at step {progress}. Use /explore to find out what awaits.",
                parse_mode="Markdown",
            )
            return
        else:
            # Normal direct region travel (no route)
            await players_col.update_one(
                {"telegram_id": user_id},
                {
                    "$set": {
                        "location": dest_region,
                        "current_route": None,
                        "path_progress": 0,
                        "has_explored": False,
                        "last_active": datetime.utcnow()
                    }
                }
            )
            lore = REGIONS[dest_region]["lore"]
            await query.edit_message_text(
                f"🗺️ You travel to *{dest_region}*.\n\n{lore}",
                parse_mode="Markdown"
            )
            return

    elif len(data) == 3:
        # Travel on a route with direction
        route_name, direction = data[1], data[2]
        route_data = ROUTES.get(route_name)

        if not route_data:
            await query.edit_message_text("Route data missing. Contact admin.")
            return

        max_steps = route_data["steps"]
        progress = player.path_progress

        if direction == "forward":
            if progress < max_steps:
                new_progress = progress + 1
                new_location = f"{route_name} Step {new_progress}"
                await players_col.update_one(
                    {"telegram_id": user_id},
                    {
                        "$set": {
                            "path_progress": new_progress,
                            "location": new_location,
                            "has_explored": False,
                            "last_active": datetime.utcnow()
                        }
                    }
                )
                await query.edit_message_text(
                    f"You move forward along *{route_name}*, step {new_progress}. Use /explore to see what happens next.",
                    parse_mode="Markdown"
                )
                return
            else:
                # Arrive at destination region
                await players_col.update_one(
                    {"telegram_id": user_id},
                    {
                        "$set": {
                            "location": route_data["end"],
                            "current_route": None,
                            "path_progress": 0,
                            "has_explored": False,
                            "last_active": datetime.utcnow()
                        }
                    }
                )
                lore = REGIONS[route_data["end"]]["lore"]
                await query.edit_message_text(
                    f"🎉 You have arrived at *{route_data['end']}*!\n\n{lore}",
                    parse_mode="Markdown"
                )
                return
        elif direction == "backward":
            if progress > 1:
                new_progress = progress - 1
                new_location = f"{route_name} Step {new_progress}"
                await players_col.update_one(
                    {"telegram_id": user_id},
                    {
                        "$set": {
                            "path_progress": new_progress,
                            "location": new_location,
                            "has_explored": False,
                            "last_active": datetime.utcnow()
                        }
                    }
                )
                await query.edit_message_text(
                    f"You move backward along *{route_name}*, step {new_progress}. Use /explore to check for dangers.",
                    parse_mode="Markdown"
                )
                return
            else:
                # Back to start region
                await players_col.update_one(
                    {"telegram_id": user_id},
                    {
                        "$set": {
                            "location": route_data["start"],
                            "current_route": None,
                            "path_progress": 0,
                            "has_explored": False,
                            "last_active": datetime.utcnow()
                        }
                    }
                )
                lore = REGIONS[route_data["start"]]["lore"]
                await query.edit_message_text(
                    f"You return to *{route_data['start']}*.\n\n{lore}",
                    parse_mode="Markdown"
                )
                return

def get_travel_handlers():
    return [
        CommandHandler("travel", travel),
        CallbackQueryHandler(handle_travel_callback, pattern="^travel::"),
    ]
