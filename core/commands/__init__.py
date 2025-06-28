# core/commands/__init__.py

from aiogram import Router, F

from .start_cmd import router as start_cmd
from .add_cmd import router as add_wallet_cmd
from .rm_cmd import remove_wallet_cmd, handle_rm_callback
from .list_cmd import list_wallets_cmd
from .profit_cmd import router as profit_cmd_router, handle_profit_callback
from .finder_cmd import finder_menu_cmd, handle_finder_selection

# ✅ Zentraler Router, der alles kombiniert
main_router = Router()

# Subrouter einbinden
main_router.include_router(start_cmd)
main_router.include_router(add_wallet_cmd)
main_router.include_router(profit_cmd_router)

# Message Commands
main_router.message.register(remove_wallet_cmd, F.text.startswith("/rm"))
main_router.message.register(list_wallets_cmd, F.text == "/list")
main_router.message.register(finder_menu_cmd, F.text == "/finder")

# Callback Queries
main_router.callback_query.register(handle_profit_callback, F.data.startswith("profit:"))
main_router.callback_query.register(handle_rm_callback, F.data.startswith("rm_"))
main_router.callback_query.register(
    handle_finder_selection,
    F.data.in_({"moonbags", "scalpbags", "finder_off"})
)

__all__ = ["main_router"]
