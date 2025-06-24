from telegram import Update
from telegram.ext import ContextTypes
from core.database import add_wallet, remove_wallet, list_wallets

async def handle_add_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("❌ Bitte benutze /add <wallet> <tag>")
        return

    wallet, tag = context.args[0], " ".join(context.args[1:])
    success = add_wallet(wallet, tag)

    if success:
        await update.message.reply_text(f"✅ <b>{wallet}</b> mit Tag <b>{tag}</b> hinzugefügt.")
    else:
        await update.message.reply_text(f"⚠️ <b>{wallet}</b> wird bereits getrackt.")

async def handle_remove_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Bitte benutze /rm <wallet>")
        return

    wallet = context.args[0]
    remove_wallet(wallet)
    await update.message.reply_text(f"🗑 Wallet <b>{wallet}</b> wurde entfernt.")

async def handle_list_wallets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    wallets = list_wallets()

    if not wallets:
        await update.message.reply_text("📭 Keine Wallets gefunden.")
        return

    message_lines = ["<b>📋 Getrackte Wallets:</b>\n"]

    for wallet in wallets:
        pnl = float(wallet.get("pnl", 0))
        wins = wallet.get("wins", 0)
        losses = wallet.get("losses", 0)
        wr = f"{wins}/{wins+losses}" if wins + losses > 0 else "0/0"
        color = "🟢" if pnl > 0 else "🔴" if pnl < 0 else "⚪️"
        message_lines.append(
            f"{color} <code>{wallet['address']}</code>\n🏷 {wallet['tag']} — WR({wr}) — PnL({pnl:+.2f} SOL)\n"
        )

    await update.message.reply_text("\n".join(message_lines))
