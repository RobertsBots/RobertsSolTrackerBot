from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_main_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Wallets anzeigen", callback_data="list_wallets")],
        [InlineKeyboardButton("➕ Wallet hinzufügen", callback_data="add_wallet")],
        [InlineKeyboardButton("📈 Profit eintragen", callback_data="add_profit")],
    ])


def get_start_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Wallets anzeigen", callback_data="list_wallets")],
        [InlineKeyboardButton("➕ Wallet hinzufügen", callback_data="add_wallet")],
        [InlineKeyboardButton("📈 Profit eintragen", callback_data="add_profit")],
    ])
