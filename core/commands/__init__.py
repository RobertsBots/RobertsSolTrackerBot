# core/commands/__init__.py

from aiogram import Router

from .start_cmd import router as start_cmd
from .add_cmd import router as add_wallet_cmd
from .rm_cmd import router as rm_cmd_router
from .list_cmd import router as list_cmd_router
from .profit_cmd import router as profit_cmd_router
from .finder_cmd import router as finder_cmd_router

# ✅ Zentraler Router, der alles kombiniert
main_router = Router()

# Subrouter einbinden
main_router.include_router(start_cmd)
main_router.include_router(add_wallet_cmd)
main_router.include_router(rm_cmd_router)
main_router.include_router(list_cmd_router)
main_router.include_router(profit_cmd_router)
main_router.include_router(finder_cmd_router)

__all__ = ["main_router"]
