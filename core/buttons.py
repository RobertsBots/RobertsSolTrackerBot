from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📈 Add Wallet", callback_data="add_wallet"),
            InlineKeyboardButton(text="🗑 Remove Wallet", callback_data="remove_wallet")
        ],
        [
            InlineKeyboardButton(text="💼 List Wallets", callback_data="list_wallets"),
            InlineKeyboardButton(text="💰 Add Profit", callback_data="add_profit")
        ],
        [
            InlineKeyboardButton(text="🛰️ SmartFinder", callback_data="smartfinder_menu")
        ]
    ])

def get_smart_finder_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🌕 Moonbags", callback_data="finder:moon"),
            InlineKeyboardButton(text="⚡️ Scalping Bags", callback_data="finder:scalp")
        ],
        [
            InlineKeyboardButton(text="❌ Deaktivieren", callback_data="finder:off"),
            InlineKeyboardButton(text="🔙 Zurück", callback_data="main_menu")
        ]
    ])

def start_buttons():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Wallet hinzufügen", callback_data="add_wallet"),
            InlineKeyboardButton(text="📃 Getrackte Wallets", callback_data="list_wallets")
        ],
        [
            InlineKeyboardButton(text="🔍 SmartFinder starten", callback_data="smartfinder_menu"),
        ]
    ])
