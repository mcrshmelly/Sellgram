import os
import logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from db import supabase
from fib import check_payment_status
from delivery import deliver_product

load_dotenv()

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# FIB Webhook — called by FIB when payment status changes
# ─────────────────────────────────────────────
@app.route("/webhook/fib", methods=["POST"])
def fib_webhook():
    data = request.json
    logger.info(f"FIB webhook received: {data}")

    payment_id = data.get("id")
    status = data.get("status")  # PAID, DECLINED

    if not payment_id or not status:
        return jsonify({"error": "invalid payload"}), 400

    # Find the order
    result = supabase.table("orders").select("*").eq("payment_id", payment_id).execute()
    orders = result.data

    if not orders:
        logger.warning(f"No order found for payment_id: {payment_id}")
        return jsonify({"error": "order not found"}), 404

    order = orders[0]

    if status == "PAID" and order["status"] != "paid":
        # Update order status
        supabase.table("orders").update({"status": "paid"}).eq("id", order["id"]).execute()

        # Deliver the product to the user
        deliver_product(order)

    elif status == "DECLINED":
        supabase.table("orders").update({"status": "cancelled"}).eq("id", order["id"]).execute()

    return jsonify({"ok": True}), 200


# ─────────────────────────────────────────────
# Dashboard API Routes
# ─────────────────────────────────────────────

@app.route("/api/stats", methods=["GET"])
def get_stats():
    """Overall stats for the dashboard."""
    orders = supabase.table("orders").select("*").eq("status", "paid").execute().data
    products = supabase.table("products").select("id").execute().data

    total_revenue = 0
    for order in orders:
        product = supabase.table("products").select("price").eq("id", order["product_id"]).single().execute().data
        if product:
            total_revenue += product["price"]

    return jsonify({
        "total_orders": len(orders),
        "total_products": len(products),
        "total_revenue": total_revenue,
    })


@app.route("/api/products", methods=["GET"])
def get_products():
    """Get all products."""
    data = supabase.table("products").select("*, sellers(name)").execute()
    return jsonify(data.data)


@app.route("/api/products", methods=["POST"])
def add_product():
    """Add a new product."""
    body = request.json
    required = ["seller_id", "name", "price", "type"]

    for field in required:
        if field not in body:
            return jsonify({"error": f"Missing field: {field}"}), 400

    result = supabase.table("products").insert(body).execute()
    return jsonify(result.data), 201


@app.route("/api/orders", methods=["GET"])
def get_orders():
    """Get all orders with product info."""
    data = supabase.table("orders").select("*, products(name, price)").order("id", desc=True).execute()
    return jsonify(data.data)


@app.route("/api/sellers", methods=["POST"])
def add_seller():
    """Register a new seller."""
    body = request.json
    if "name" not in body:
        return jsonify({"error": "name is required"}), 400

    result = supabase.table("sellers").insert(body).execute()
    return jsonify(result.data), 201


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)