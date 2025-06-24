from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from core.database import db
from core.utils import format_wallet_info, format_profit_value


async def start_cmd(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Add Wallet", callback_data="add_wallet")
    builder.button(text="📋 List Wallets", callback_data="list_wallets")
    builder.button(text="💰 Profit hinzufügen", callback_data="add_profit")
    builder.button(text="🚀 Finder-Menü", callback_data="open_finder_menu")

    await message.answer(
        "Willkommen beim SolTracker Bot! Was möchtest du tun?",
        reply_markup=builder.as_markup(),
    )


async def add_cmd(message: types.Message):
    await message.answer("Sende mir eine Wallet-Adresse und ein optionales Tag.\nFormat:\n`/add <WALLET> <TAG>`", parse_mode="Markdown")


async def rm_cmd(message: types.Message):
    await message.answer("Sende mir die Wallet-Adresse, die du entfernen willst.\nFormat:\n`/rm <WALLET>`", parse_mode="Markdown")


async def list_cmd(message: types.Message):
    wallets = db.get_all_wallets()
    if not wallets:
        await message.answer("🚫 Keine Wallets getrackt.")
        return

    response = "📊 *Getrackte Wallets:*\n\n"
    for wallet in wallets:
        pnl_display = format_profit_value(wallet.get("profit", 0))
        wr = wallet.get("wr", {"win": 0, "loss": 0})
        wr_display = f"WR({wr['win']}/{wr['loss']})"
        tag = wallet.get("tag", "")
        wallet_info = format_wallet_info(wallet["address"], tag)
        response += f"{wallet_info}\n{wr_display} • {pnl_display}\n\n"

    await message.answer(response, parse_mode="Markdown")


async def profit_cmd(message: types.Message):
    await message.answer("Sende den Profit im Format:\n`/profit <WALLET> <+/-BETRAG>`\nBeispiel: `/profit 7abc... +25`", parse_mode="Markdown")
