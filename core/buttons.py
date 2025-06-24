from telegram import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📈 Add Wallet", callback_data="add_wallet")],
        [InlineKeyboardButton("🗑 Remove Wallet", callback_data="remove_wallet")],
        [InlineKeyboardButton("💼 List Wallets", callback_data="list_wallets")],
        [InlineKeyboardButton("💰 Add Profit", callback_data="add_profit")],
        [InlineKeyboardButton("🧠 Smart Finder", callback_data="smart_finder")],
    ])

def get_smart_finder_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌕 Moonbags", callback_data="finder_moonbags")],
        [InlineKeyboardButton("⚡️ Scalping Bags", callback_data="finder_scalping")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ])
