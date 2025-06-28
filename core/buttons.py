from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📈 Add Wallet", callback_data="add_wallet")],
        [InlineKeyboardButton(text="🗑 Remove Wallet", callback_data="remove_wallet")],
        [InlineKeyboardButton(text="💼 List Wallets", callback_data="list_wallets")],
        [InlineKeyboardButton(text="💰 Add Profit", callback_data="add_profit")],
        [InlineKeyboardButton(text="🧠 Smart Finder", callback_data="smart_finder")]
    ])

def get_smart_finder_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌕 Moonbags", callback_data="finder_moonbags")],
        [InlineKeyboardButton(text="⚡️ Scalping Bags", callback_data="finder_scalping")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="main_menu")]
    ])
