from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def start_menu_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("➕ Wallet hinzufügen", callback_data="start:add_wallet"),
        InlineKeyboardButton("📤 Wallet entfernen", callback_data="start:remove_wallet"),
    )
    keyboard.add(
        InlineKeyboardButton("📋 Getrackte Wallets", callback_data="start:list_wallets"),
        InlineKeyboardButton("➕ Profit eintragen", callback_data="start:add_profit"),
    )
    keyboard.add(
        InlineKeyboardButton("🚀 SmartFinder starten", callback_data="start:finder_on"),
        InlineKeyboardButton("🛑 SmartFinder stoppen", callback_data="start:finder_off"),
    )
    keyboard.add(
        InlineKeyboardButton("🧠 SmartCoach Analyse", callback_data="start:coach"),
        InlineKeyboardButton("💾 Backup senden", callback_data="start:backup"),
    )
    return keyboard


def confirm_remove_keyboard(wallet: str):
    return InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("✅ Ja, entfernen", callback_data=f"confirm_remove:{wallet}"),
        InlineKeyboardButton("↩️ Abbrechen", callback_data="cancel_remove")
    )


def profit_cancel_button(wallet: str):
    return InlineKeyboardMarkup().add(
        InlineKeyboardButton("❌ Abbrechen", callback_data=f"cancel:profit:{wallet}")
    )


def cancel_button():
    return InlineKeyboardMarkup().add(
        InlineKeyboardButton("❌ Abbrechen", callback_data="cancel")
    )


def finder_mode_keyboard():
    return InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("🌕 Moonbags", callback_data="finder:moon"),
        InlineKeyboardButton("⚡️ Scalping Bags", callback_data="finder:scalp")
    )


def smartcoach_button(wallet: str):
    return InlineKeyboardMarkup().add(
        InlineKeyboardButton("🧠 SmartCoach Analyse", callback_data=f"coach:{wallet}")
    )


def add_wallet_button():
    return InlineKeyboardMarkup().add(
        InlineKeyboardButton("➕ Wallet hinzufügen", callback_data="start:add_wallet")
    )


def remove_wallet_button():
    return InlineKeyboardMarkup().add(
        InlineKeyboardButton("📤 Wallet entfernen", callback_data="start:remove_wallet")
    )


def list_wallets_button():
    return InlineKeyboardMarkup().add(
        InlineKeyboardButton("📋 Getrackte Wallets", callback_data="start:list_wallets")
    )


# Alias für Kompatibilität mit bisherigen Imports
start_buttons = start_menu_keyboard
