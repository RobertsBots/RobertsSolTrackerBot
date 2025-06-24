from telegram import Update
from telegram.ext import ContextTypes
from core.ui import start_command
from core.wallet_tracker import handle_add_wallet, handle_remove_wallet, handle_list_wallets
from core.pnlsystem import handle_profit_command, handle_profit_button
from core.buttons import handle_callback_query
from core.smartfinder import handle_finder_command, handle_moonbags_command, handle_scalpingbags_command

def register_handlers(application):
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("add", handle_add_wallet))
    application.add_handler(CommandHandler("rm", handle_remove_wallet))
    application.add_handler(CommandHandler("list", handle_list_wallets))
    application.add_handler(CommandHandler("profit", handle_profit_command))
    application.add_handler(CommandHandler("finder", handle_finder_command))
    application.add_handler(CommandHandler("moonbags", handle_moonbags_command))
    application.add_handler(CommandHandler("scalpings", handle_scalpingbags_command))

    application.add_handler(CallbackQueryHandler(handle_callback_query))
