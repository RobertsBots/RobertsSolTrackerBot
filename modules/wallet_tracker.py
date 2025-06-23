from telegram.ext import CommandHandler, ContextTypes
from telegram import Update

wallets = {}

async def add_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text("❌ Nutzung: /add WALLET TAG")
        return
    wallet, tag = context.args
    wallets[wallet] = tag
    await update.message.reply_text(f"✅ Wallet {wallet} mit Tag '{tag}' hinzugefügt.")

async def list_wallets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not wallets:
        await update.message.reply_text("📭 Noch keine Wallets getrackt.")
        return
    msg = "\n".join([f"{tag}: {addr}" for addr, tag in wallets.items()])
    await update.message.reply_text(f"📋 Getrackte Wallets:\n{msg}")

def wallet_commands(application):
    application.add_handler(CommandHandler("add", add_wallet))
    application.add_handler(CommandHandler("list", list_wallets))