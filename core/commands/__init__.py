from aiogram import Dispatcher

# ✅ Handler für Telegram-Kommandos
from .start_cmd import register_handlers as register_start_cmd
from .add_cmd import register_handlers as register_add_cmd
from .rm_cmd import register_handlers as register_rm_cmd
from .list_cmd import register_handlers as register_list_cmd
from .profit_cmd import register_handlers as register_profit_cmd
from .finder_cmd import register_handlers as register_finder_cmd

# ✅ Button-Callback-Handler
from .callbacks import register_callback_buttons

# 🔁 Zentraler Router – wird in main.py aufgerufen
def main_router(dp: Dispatcher):
    register_start_cmd(dp)
    register_add_cmd(dp)
    register_rm_cmd(dp)
    register_list_cmd(dp)
    register_profit_cmd(dp)
    register_finder_cmd(dp)
    register_callback_buttons(dp)
