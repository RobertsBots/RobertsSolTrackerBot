from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler
)

from core.ui import start_command, handle_callback_query
from core.wallet_tracker import handle_add_wallet, handle_remove_wallet, handle_list_wallets
from core.pnlsystem import handle_profit_command, handle_profit_button

def register_handlers(application):
    # Standard-Befehle
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("add", handle_add_wallet))
    application.add_handler(CommandHandler("rm", handle_remove_wallet))
    application.add_handler(CommandHandler("list", handle_list_wallets))
    application.add_handler(CommandHandler("profit", handle_profit_command))

    # Inline-Button Handler
    application.add_handler(CallbackQueryHandler(handle_callback_query))
