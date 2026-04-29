"""
main.py — runs Flask (webhook server) and Telegram bot together.
Flask handles FIB webhooks + dashboard API.
Bot handles Telegram messages.
"""
import threading
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

from flask_app.app import app
from bot.bot import run_bot


def run_flask():
    app.run(host="0.0.0.0", port=5000, debug=False)


if __name__ == "__main__":
    # Run Flask in background thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Run bot in main thread
    run_bot()
