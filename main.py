from telegram.ext import ApplicationBuilder
from config import BOT_TOKEN, WEBHOOK_URL, PORT
import logging

def setup_jobs(application):
    # Cronjobs etc. kommen später hierhin
    pass

def setup_handlers(application):
    from handlers.wallet_tracking import wallet_handlers
    for handler in wallet_handlers:
        application.add_handler(handler)

def main():
    logging.basicConfig(level=logging.INFO)
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    setup_handlers(application)
    setup_jobs(application)

    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL
    )

if __name__ == "__main__":
    main()