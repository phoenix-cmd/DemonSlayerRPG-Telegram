import os
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from handlers import start, gender, mode

# Load the token from environment variable
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Raise an error if the token is not set in environment variables
if not BOT_TOKEN:
    raise ValueError("No BOT_TOKEN found in environment variables")

app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start.start))
app.add_handler(CallbackQueryHandler(gender.gender_selection, pattern="^gender_"))
app.add_handler(CallbackQueryHandler(mode.mode_selection, pattern="^mode_"))

app.run_polling()

