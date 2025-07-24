import random
from telegram import Update
from telegram.ext import ContextTypes
from motor.motor_asyncio import AsyncIOMotorClient

# If you have a 'get_db' utility in utils, import it:
# from utils.db import get_db

# MongoDB URI should be set via environment variables
import os

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
mongo_client = AsyncIOMotorClient(MONGODB_URI)
db = mongo_client["demon_slayer_rpg"]
players_col = db["players"]

# Example: regions could be loaded from a JSON/config or separate data module
REGIONS = {
    "Mount Natagumo": {
        "lore": "A web-shrouded forest infamous for its deadly silk.",
        "demons": ["Rui", "Spider Demon"],
        "loot": ["Spider Silk", "Moonstone", "Health Elixir"],
        "events": [
            "A Kasugai crow delivers a secret message.",
            "You discover an ancient, web-choked shrine."
        ]
    },
    # Expand with additional regions
}

# Weighted exploration outcome probabilities
OUTCOMES = [
    ("demon", 0.3),
    ("loot", 0.25),
    ("event", 0.2),
    ("nothing", 0.25),
]
def weighted_outcome():
    names, weights = zip(*OUTCOMES)
    return random.choices(names, weights)[0]

# --- Main Explore Handler ---

async def explore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Retrieve player (assume 'user_id' is the Mongo key)
    player = await players_col.find_one({"user_id": user_id})
    if not player:
        await update.message.reply_text("You are not registered! Use /start to join the Demon Slayer Corps.")
        return

    region_name = player.get("region", "Mount Natagumo")
    region = REGIONS.get(region_name)
    if not region:
        await update.message.reply_text("Error: Unknown region. Please contact an admin.")
        return

    outcome = weighted_outcome()

    if outcome == "demon":
        demon = random.choice(region["demons"])
        await update.message.reply_text(
            f"As you move through {region_name}, a {demon} appears, blocking your path!"
        )
        # Combat handler integration (adjust import as needed)
        from handlers import combat
        await combat.start_combat(update, context, enemy=demon)
    elif outcome == "loot":
        loot = random.choice(region["loot"])
        await players_col.update_one(
            {"user_id": user_id},
            {"$push": {"inventory": loot}}
        )
        await update.message.reply_text(
            f"You found a hidden stash: {loot} added to your inventory!"
        )
    elif outcome == "event":
        event_text = random.choice(region["events"])
        await update.message.reply_text(
            f"Event: {event_text}"
        )
    else:
        await update.message.reply_text(
            "You wander in suspense... nothing happens, but the forest feels alive."
        )

# --- Optional: Add Command Handler Registration Helper ---

def get_explore_handler():
    from telegram.ext import CommandHandler
    return CommandHandler("explore", explore)
