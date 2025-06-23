from telegram import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("➕ Wallet hinzufügen", callback_data="add_wallet")],
        [InlineKeyboardButton("📃 Getrackte Wallets", callback_data="list_wallets")],
        [InlineKeyboardButton("💰 PnL setzen", callback_data="set_profit")],
        [InlineKeyboardButton("🗑️ Wallet entfernen", callback_data="remove_wallet")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_profit_buttons(wallet_address):
    keyboard = [
        [InlineKeyboardButton("➕ +1 sol", callback_data=f"profit|{wallet_address}|+1")],
        [InlineKeyboardButton("➖ -1 sol", callback_data=f"profit|{wallet_address}|-1")],
        [InlineKeyboardButton("🔙 Zurück", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)
