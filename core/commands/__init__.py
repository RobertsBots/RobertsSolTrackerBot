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

# Neue Callback-Handler für Start-Menu Buttons (start:add_wallet, start:remove_wallet, etc.)
async def handle_start_buttons_callback(callback_query):
    data = callback_query.data

    if data == "start:add_wallet":
        await callback_query.answer()
        await callback_query.message.answer(
            "Bitte sende mir die Wallet-Adresse im Format:\n\n"
            "<code>/add WALLET TAG</code>\n\n"
            "Beispiel:\n"
            "/add 7g3n...ABcd MeineWallet",
            parse_mode="HTML"
        )
    elif data == "start:remove_wallet":
        await callback_query.answer()
        await callback_query.message.answer(
            "Nutze <code>/rm</code>, um eine Wallet zu entfernen.",
            parse_mode="HTML"
        )
    elif data == "start:list_wallets":
        await callback_query.answer()
        await callback_query.message.answer(
            "Nutze <code>/list</code>, um deine getrackten Wallets anzuzeigen.",
            parse_mode="HTML"
        )
    elif data == "start:add_profit":
        await callback_query.answer()
        await callback_query.message.answer(
            "Nutze <code>/profit WALLET +10</code>, um Profit oder Verlust einzutragen.",
            parse_mode="HTML"
        )
    elif data == "start:finder_on":
        await callback_query.answer("SmartFinder wird gestartet!")
        # Hier optional: await Aufruf eines Kommandos oder Logik einfügen
    elif data == "start:finder_off":
        await callback_query.answer("SmartFinder wird gestoppt!")
        # Hier optional: await Aufruf eines Kommandos oder Logik einfügen
    elif data == "start:coach":
        await callback_query.answer()
        await callback_query.message.answer(
            "Nutze <code>/coach WALLET</code>, um eine SmartCoach-Analyse zu erhalten.",
            parse_mode="HTML"
        )
    elif data == "start:backup":
        await callback_query.answer()
        await callback_query.message.answer(
            "Backup-Funktion ist noch in Arbeit.",
            parse_mode="HTML"
        )
    else:
        await callback_query.answer("Unbekannte Aktion.", show_alert=True)

def register_start_buttons_callbacks(dp: Dispatcher):
    dp.register_callback_query_handler(handle_start_buttons_callback, lambda c: c.data and c.data.startswith("start:"))

# 🔁 Zentraler Router – wird in main.py aufgerufen
def main_router(dp: Dispatcher):
    register_start_cmd(dp)
    register_add_cmd(dp)
    register_rm_cmd(dp)
    register_list_cmd(dp)
    register_profit_cmd(dp)
    register_finder_cmd(dp)
    register_callback_buttons(dp)  # Andere Callback-Handler (z.B. smartcoach)
    register_coach_cmd(dp)
    register_start_buttons_callbacks(dp)  # Neu: Start-Menu Button Callbacks
