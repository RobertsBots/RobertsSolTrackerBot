from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

FINDER_STATE = {
    "active": False,
    "mode": None  # either "moonbags" or "scalpings"
}

async def finder_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔍 Aktivieren", callback_data="finder_activate")],
        [InlineKeyboardButton("🛑 Deaktivieren", callback_data="finder_deactivate")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📡 Smart Wallet Finder Menü", reply_markup=reply_markup)

async def finder_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "finder_activate":
        keyboard = [
            [InlineKeyboardButton("🌕 Moonbags", callback_data="finder_mode_moon")],
            [InlineKeyboardButton("⚡️ Scalping Bags", callback_data="finder_mode_scalp")]
        ]
        await query.edit_message_text("🔧 Modus wählen:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "finder_deactivate":
        FINDER_STATE["active"] = False
        FINDER_STATE["mode"] = None
        await query.edit_message_text("🛑 Smart Finder deaktiviert.")

    elif query.data == "finder_mode_moon":
        FINDER_STATE["active"] = True
        FINDER_STATE["mode"] = "moonbags"
        await query.edit_message_text("✅ Finder aktiviert: 🌕 Moonbags")

    elif query.data == "finder_mode_scalp":
        FINDER_STATE["active"] = True
        FINDER_STATE["mode"] = "scalpings"
        await query.edit_message_text("✅ Finder aktiviert: ⚡️ Scalping Bags")

def get_finder_state():
    return FINDER_STATE
