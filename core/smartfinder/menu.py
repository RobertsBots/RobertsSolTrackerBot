# core/smartfinder/menu.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from core.smartfinder.finder import start_smartfinder_job, stop_smartfinder_job, set_finder_mode

# === /finder Befehl ===
async def handle_finder_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🛰️ Aktivieren", callback_data="finder_on")],
        [InlineKeyboardButton("🛑 Deaktivieren", callback_data="finder_off")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🔍 Smart Wallet Finder Menü:", reply_markup=reply_markup)

# === Auswahl des Modus ===
async def handle_finder_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "finder_on":
        mode_keyboard = [
            [InlineKeyboardButton("🌕 Moonbags", callback_data="mode_moonbags")],
            [InlineKeyboardButton("⚡️ Scalping Bags", callback_data="mode_scalping")]
        ]
        await query.edit_message_text("🚀 Wähle deinen Finder-Modus:", reply_markup=InlineKeyboardMarkup(mode_keyboard))

    elif query.data == "finder_off":
        stop_smartfinder_job()
        await query.edit_message_text("🛑 Smart Wallet Finder deaktiviert.")

    elif query.data == "mode_moonbags":
        set_finder_mode("moonbags")
        start_smartfinder_job(context.application)
        await query.edit_message_text("🌕 Moonbags-Finder aktiviert.")

    elif query.data == "mode_scalping":
        set_finder_mode("scalping")
        start_smartfinder_job(context.application)
        await query.edit_message_text("⚡️ Scalping-Finder aktiviert.")
