from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from core.utils import (
    add_wallet_to_tracking,
    remove_wallet_from_tracking,
    get_tracked_wallets_with_stats,
    set_manual_profit,
    toggle_smart_finder,
    get_finder_status
)

router = Router()

@router.message(Command("start"))
async def start_handler(message: Message):
    status = await get_finder_status()
    finder_button_text = "🛑 SmartFinder deaktivieren" if status else "🚀 SmartFinder aktivieren"
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📄 Wallets anzeigen", callback_data="list_wallets")],
        [InlineKeyboardButton(text="➕ Wallet hinzufügen", callback_data="add_wallet")],
        [InlineKeyboardButton(text="💸 Profit setzen", callback_data="set_profit")],
        [InlineKeyboardButton(text=finder_button_text, callback_data="toggle_finder")]
    ])
    await message.answer("👋 Willkommen beim RobertsSolTrackerBot!\n\nWähle eine Option:", reply_markup=markup)

@router.message(Command("add"))
async def add_handler(message: Message):
    try:
        _, address, tag = message.text.strip().split()
        await add_wallet_to_tracking(address, tag)
        await message.answer(f"✅ Wallet `{address}` mit Tag `{tag}` wurde hinzugefügt.", parse_mode="Markdown")
    except Exception:
        await message.answer("⚠️ Nutzung: `/add <WALLET> <TAG>`", parse_mode="Markdown")

@router.message(Command("rm"))
async def remove_handler(message: Message):
    try:
        _, address = message.text.strip().split()
        await remove_wallet_from_tracking(address)
        await message.answer(f"❌ Wallet `{address}` wurde entfernt.", parse_mode="Markdown")
    except Exception:
        await message.answer("⚠️ Nutzung: `/rm <WALLET>`", parse_mode="Markdown")

@router.message(Command("list"))
async def list_handler(message: Message):
    msg = await get_tracked_wallets_with_stats()
    await message.answer(msg, parse_mode="Markdown")

@router.message(Command("profit"))
async def profit_handler(message: Message):
    try:
        _, address, value = message.text.strip().split()
        if not (value.startswith("+") or value.startswith("-")):
            raise ValueError("Kein gültiges Plus- oder Minuszeichen")
        await set_manual_profit(address, float(value))
        await message.answer(f"📈 Profit für `{address}` gesetzt auf `{value} SOL`.", parse_mode="Markdown")
    except Exception:
        await message.answer("⚠️ Nutzung: `/profit <WALLET> <+/-BETRAG>`", parse_mode="Markdown")

@router.callback_query(F.data == "list_wallets")
async def cb_list_wallets(callback: CallbackQuery):
    msg = await get_tracked_wallets_with_stats()
    await callback.message.edit_text(msg, parse_mode="Markdown")

@router.callback_query(F.data == "toggle_finder")
async def cb_toggle_finder(callback: CallbackQuery):
    status = await toggle_smart_finder()
    new_text = "🛑 SmartFinder deaktivieren" if status else "🚀 SmartFinder aktivieren"
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌕 Moonbags", callback_data="finder_moon")],
        [InlineKeyboardButton(text="⚡️ Scalping Bags", callback_data="finder_scalp")]
    ]) if status else InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 SmartFinder aktivieren", callback_data="toggle_finder")]
    ])
    msg = "✅ SmartFinder aktiviert!" if status else "🛑 SmartFinder deaktiviert!"
    await callback.message.edit_text(msg, reply_markup=markup)

@router.callback_query(F.data.in_(["finder_moon", "finder_scalp"]))
async def cb_select_finder_mode(callback: CallbackQuery):
    mode = "moon" if callback.data == "finder_moon" else "scalp"
    await toggle_smart_finder(True, mode)
    await callback.message.edit_text(f"✅ SmartFinder läuft im Modus: **{mode.capitalize()} Bags**", parse_mode="Markdown")
