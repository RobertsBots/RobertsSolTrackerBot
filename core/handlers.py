from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# /start
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("➕ Add Wallet", callback_data="add_wallet")],
        [InlineKeyboardButton("📋 List Wallets", callback_data="list_wallets")],
        [InlineKeyboardButton("💰 Add Profit", callback_data="add_profit")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Willkommen beim 🧠 <b>RobertsSolTrackerBot</b>!\nWähle eine Aktion:",
        reply_markup=reply_markup
    )

# /add
async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("❌ Usage: /add <WALLET> <TAG>")
        return
    wallet, tag = context.args[0], " ".join(context.args[1:])
    await update.message.reply_text(f"✅ Wallet <code>{wallet}</code> mit Tag <b>{tag}</b> hinzugefügt.")

# /rm
async def remove_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text("❌ Usage: /rm <WALLET>")
        return
    wallet = context.args[0]
    await update.message.reply_text(f"🗑️ Wallet <code>{wallet}</code> entfernt.")

# /list
async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Dummy-Output
    await update.message.reply_text(
        "<b>📊 Getrackte Wallets:</b>\n• 7gYv...ds1Q – WR(5/2), PnL +12.3 SOL\n• 9uhR...GGX – WR(3/4), PnL –2.1 SOL"
    )

# /profit
async def profit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("❌ Usage: /profit <WALLET> <+/-BETRAG>")
        return
    wallet, profit = context.args[0], context.args[1]
    await update.message.reply_text(f"💰 Manuell Profit <b>{profit}</b> für Wallet <code>{wallet}</code> gesetzt.")

# Inline-Buttons
async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "add_wallet":
        await query.edit_message_text("Verwende: /add <WALLET> <TAG>")
    elif query.data == "list_wallets":
        await list_command(update, context)
    elif query.data == "add_profit":
        await query.edit_message_text("Verwende: /profit <WALLET> <+/-BETRAG>")
