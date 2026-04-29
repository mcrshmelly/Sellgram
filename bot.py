import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from dotenv import load_dotenv
from db import supabase
from fib import create_payment

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
BOT_USERNAME = os.getenv("BOT_USERNAME", "SellgramBot")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args  # e.g. /start product_3

    # If user came via direct product link (t.me/Bot?start=product_3)
    if args and args[0].startswith("product_"):
        product_id = int(args[0].split("_")[1])
        await show_product(update, context, product_id)
        return

    # Otherwise show all products
    await show_all_products(update, context)

# Show all products

async def show_all_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = supabase.table("products").select("*").execute()
    products = result.data

    if not products:
        await update.message.reply_text("لا توجد منتجات متاحة حالياً.")
        return

    text = "🛍️ *المنتجات المتاحة:*\n\n"
    keyboard = []

    for p in products:
        text += f"• *{p['name']}* — {p['price']:,} IQD\n"
        keyboard.append([
            InlineKeyboardButton(
                f"🛒 شراء: {p['name']}",
                callback_data=f"buy_{p['id']}"
            )
        ])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)

# Show single product detail
async def show_product(update: Update, context: ContextTypes.DEFAULT_TYPE, product_id: int):
    result = supabase.table("products").select("*").eq("id", product_id).single().execute()
    product = result.data

    if not product:
        await update.message.reply_text("المنتج غير موجود.")
        return

    text = (
        f"📦 *{product['name']}*\n"
        f"💰 السعر: {product['price']:,} IQD\n\n"
        f"اضغط الزر أدناه للشراء:"
    )

    keyboard = [[InlineKeyboardButton("🛒 اشتري الآن", callback_data=f"buy_{product_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)

# Handle "buy" button press → create FIB payment
async def handle_buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    product_id = int(query.data.split("_")[1])
    user_id = query.from_user.id

    # Fetch product
    result = supabase.table("products").select("*").eq("id", product_id).single().execute()
    product = result.data

    if not product:
        await query.edit_message_text("المنتج غير موجود.")
        return

    # Create FIB payment
    try:
        payment = create_payment(
            amount=product["price"],
            order_id=product_id,
            description=f"شراء: {product['name']}"
        )
    except Exception as e:
        logger.error(f"FIB payment error: {e}")
        await query.edit_message_text("حدث خطأ أثناء إنشاء رابط الدفع. حاول مرة أخرى.")
        return

    payment_id = payment["paymentId"]

    # Save order in DB
    supabase.table("orders").insert({
        "payment_id": payment_id,
        "user_id": user_id,
        "product_id": product_id,
        "status": "pending"
    }).execute()

    # Send payment info to user
    text = (
        f"✅ *طلبك جاهز!*\n\n"
        f"📦 المنتج: {product['name']}\n"
        f"💰 المبلغ: {product['price']:,} IQD\n\n"
        f"🔑 كود الدفع: `{payment.get('readableCode', '')}`\n\n"
        f"افتح تطبيق FIB وادفع باستخدام الكود أعلاه.\n"
        f"سيتم إرسال المنتج تلقائياً بعد تأكيد الدفع."
    )

    keyboard = []
    if payment.get("personalAppLink"):
        keyboard.append([InlineKeyboardButton("💳 ادفع عبر FIB", url=payment["personalAppLink"])])

    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=reply_markup)


# Run bot

def run_bot():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_buy, pattern=r"^buy_\d+$"))

    logger.info("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    run_bot()
