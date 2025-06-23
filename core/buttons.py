from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_main_buttons():
    keyboard = [
        [
            InlineKeyboardButton("➕ Wallet hinzufügen", callback_data="add_wallet"),
            InlineKeyboardButton("➖ Wallet entfernen", callback_data="remove_wallet")
        ],
        [
            InlineKeyboardButton("📋 Getrackte Wallets", callback_data="list_wallets")
        ],
        [
            InlineKeyboardButton("💰 Profit eintragen", callback_data="enter_profit")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_cancel_button():
    keyboard = [
        [InlineKeyboardButton("❌ Abbrechen", callback_data="cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)
