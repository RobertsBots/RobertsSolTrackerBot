from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def profit_buttons(address):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("+0.1 SOL", callback_data=f"profit:{address}:+0.1")],
        [InlineKeyboardButton("-0.1 SOL", callback_data=f"profit:{address}:-0.1")]
    ])