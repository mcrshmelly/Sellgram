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

from app import app
from bot import run_bot

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)


if __name__ == "__main__":
    # Run Flask in background thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Run bot in main thread
    run_bot()