from aiogram import types, Router
from aiogram.types import Message
from aiogram.filters import Command
from core.commands.start_cmd import start_cmd
from core.commands.add_cmd import add_cmd
from core.commands.rm_cmd import rm_cmd
from core.commands.list_cmd import list_cmd
from core.commands.profit_cmd import profit_cmd

router = Router()

@router.message(Command("start"))
async def handle_start(message: Message):
    await start_cmd(message)

@router.message(Command("add"))
async def handle_add(message: Message):
    await add_cmd(message)

@router.message(Command("rm"))
async def handle_rm(message: Message):
    await rm_cmd(message)

@router.message(Command("list"))
async def handle_list(message: Message):
    await list_cmd(message)

@router.message(Command("profit"))
async def handle_profit(message: Message):
    await profit_cmd(message)
