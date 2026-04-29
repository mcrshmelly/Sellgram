import os
import logging
import requests
from db import supabase

logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"


def send_telegram_message(chat_id: int, text: str):
    """Send a plain text message to a Telegram user."""
    requests.post(f"{TELEGRAM_API}/sendMessage", json={
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    })


def send_telegram_document(chat_id: int, file_path: str, caption: str = ""):
    """Send a file (PDF) to a Telegram user from Supabase Storage URL."""
    # Get public URL from Supabase Storage
    storage_url = supabase.storage.from_("products").get_public_url(file_path)

    requests.post(f"{TELEGRAM_API}/sendDocument", json={
        "chat_id": chat_id,
        "document": storage_url,
        "caption": caption,
        "parse_mode": "Markdown"
    })


def notify_seller(seller_id: int, product_name: str, buyer_id: int):
    """Notify seller on Telegram when a sale is made."""
    seller = supabase.table("sellers").select("*").eq("id", seller_id).single().execute().data
    if not seller or not seller.get("telegram_id"):
        return

    message = (
        f"🎉 *بيعة جديدة!*\n\n"
        f"📦 المنتج: {product_name}\n"
        f"👤 المشتري: `{buyer_id}`"
    )
    send_telegram_message(seller["telegram_id"], message)


def deliver_product(order: dict):
    """
    Main delivery function — called after payment is confirmed.
    Sends the product (PDF or invite link) to the buyer.
    """
    user_id = order["user_id"]
    product_id = order["product_id"]

    # Fetch product details
    result = supabase.table("products").select("*, sellers(*)").eq("id", product_id).single().execute()
    product = result.data

    if not product:
        logger.error(f"Product {product_id} not found for delivery")
        return

    product_type = product.get("type")
    product_name = product.get("name")
    file_path = product.get("file_path")

    try:
        if product_type == "digital" and file_path:
            if file_path.startswith("http") or "t.me" in file_path:
                # It's an invite link
                message = (
                    f"✅ *شكراً على شرائك!*\n\n"
                    f"📦 المنتج: *{product_name}*\n\n"
                    f"🔗 رابط الكورس الخاص بك:\n{file_path}\n\n"
                    f"⚠️ هذا الرابط للاستخدام مرة واحدة فقط."
                )
                send_telegram_message(user_id, message)
            else:
                # It's a PDF stored in Supabase Storage
                send_telegram_document(
                    chat_id=user_id,
                    file_path=file_path,
                    caption=f"✅ *{product_name}* — شكراً على شرائك!"
                )
        else:
            # Fallback message
            send_telegram_message(user_id, f"✅ تم تأكيد طلبك: *{product_name}*. سيتم التواصل معك قريباً.")

        # Notify the seller
        if product.get("sellers"):
            notify_seller(product["sellers"]["id"], product_name, user_id)

        # Mark as delivered
        supabase.table("orders").update({"status": "delivered"}).eq("id", order["id"]).execute()
        logger.info(f"Order {order['id']} delivered to user {user_id}")

    except Exception as e:
        logger.error(f"Delivery failed for order {order['id']}: {e}")
