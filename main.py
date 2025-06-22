from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = "7953666029:AAEKunPOhUdeoS-57OlTDuZbRoOTgGY5P5o"
CHANNEL_ID = -4690026526

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Der Bot ist aktiv und bereit!")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()
