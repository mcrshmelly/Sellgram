import os
import requests
from dotenv import load_dotenv

load_dotenv()

FIB_BASE_URL = os.getenv("FIB_BASE_URL", "https://fib.iq/openapi")
FIB_CLIENT_ID = os.getenv("FIB_CLIENT_ID")
FIB_CLIENT_SECRET = os.getenv("FIB_CLIENT_SECRET")
WEBHOOK_BASE_URL = os.getenv("WEBHOOK_BASE_URL")

_token_cache = {"token": None}


def get_fib_token() -> str:
    """Get OAuth access token from FIB."""
    if _token_cache["token"]:
        return _token_cache["token"]

    response = requests.post(
        f"{FIB_BASE_URL}/auth/token",
        data={
            "grant_type": "client_credentials",
            "client_id": FIB_CLIENT_ID,
            "client_secret": FIB_CLIENT_SECRET,
        },
    )
    response.raise_for_status()
    token = response.json()["access_token"]
    _token_cache["token"] = token
    return token


def create_payment(amount: int, order_id: int, description: str) -> dict:
    """
    Create a FIB payment request.
    Returns dict with: paymentId, readableCode, personalAppLink, qrCodeBase64
    """
    token = get_fib_token()

    payload = {
        "monetaryValue": {
            "amount": amount,
            "currency": "IQD"
        },
        "statusCallbackUrl": f"{WEBHOOK_BASE_URL}/webhook/fib",
        "description": description,
    }

    response = requests.post(
        f"{FIB_BASE_URL}/payments",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    response.raise_for_status()
    return response.json()


def check_payment_status(payment_id: str) -> str:
    """Check FIB payment status. Returns: PAID, UNPAID, DECLINED."""
    token = get_fib_token()

    response = requests.get(
        f"{FIB_BASE_URL}/payments/{payment_id}/status",
        headers={"Authorization": f"Bearer {token}"},
    )
    response.raise_for_status()
    return response.json().get("status", "UNPAID")
