from aiogram import Dispatcher

# ✅ Einzelrouter pro Kommando
from .start_cmd import register_start_cmd
from .add_cmd import register_add_cmd
from .rm_cmd import register_rm_cmd
from .list_cmd import register_list_cmd
from .profit_cmd import register_profit_cmd
from .finder_cmd import register_finder_cmd
from .coach_cmd import register_coach_cmd

# ✅ Callback-Handler für Buttons
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
    register_coach_cmd(dp)
