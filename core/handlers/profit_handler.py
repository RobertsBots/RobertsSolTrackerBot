from telegram.ext import CommandHandler
from core.pnlsystem import handle_profit_command

def get_profit_handler():
    return CommandHandler("profit", handle_profit_command)
