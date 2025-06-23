from telegram.ext import CallbackQueryHandler

async def button_callback(update, context):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(f"Du hast '{query.data}' gedrückt.")

callback_handler = CallbackQueryHandler(button_callback)
