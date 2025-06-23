from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from core.buttons import get_start_buttons

# START-KOMMANDO
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from core.start import handle_start  # Import innerhalb der Funktion zur Vermeidung von Circular Imports
    await handle_start(update, context)

# CALLBACK HANDLING FÜR INLINE-BUTTONS
async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from core.start import handle_start  # ebenfalls lokal importiert
    query = update.callback_query
    await query.answer()

    if query.data == "start":
        await handle_start(update, context)
