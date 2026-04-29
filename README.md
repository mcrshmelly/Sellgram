# Sellgram Backend

Telegram bot + Flask API for selling digital products with FIB payment.

## Project Structure

```
sellgram/
├── main.py              # Entry point (runs bot + Flask together)
├── db.py                # Supabase client
├── fib.py               # FIB payment integration
├── delivery.py          # Delivers product after payment
├── requirements.txt
├── .env.example         # Copy to .env and fill in values
├── supabase_setup.sql   # Run this in Supabase SQL Editor
├── bot/
│   └── bot.py           # Telegram bot handlers
└── flask_app/
    └── app.py           # Flask webhook + dashboard API
```

## Setup Steps

### 1. Clone & install
```bash
pip install -r requirements.txt
```

### 2. Set up Supabase
- Create a project at supabase.com
- Go to SQL Editor → paste & run `supabase_setup.sql`
- Go to Storage → create a bucket named `products` (set to Public)
- Go to Settings → API → copy URL and service_role key

### 3. Set up Telegram Bot
- Message @BotFather → /newbot
- Copy the token

### 4. Fill in .env
```bash
cp .env.example .env
# Edit .env with your real values
```

### 5. Run locally
```bash
python main.py
```

### 6. Deploy to Railway
- Push to GitHub
- Connect repo to Railway
- Add env variables in Railway dashboard
- Railway will auto-detect and run main.py

## API Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| POST | /webhook/fib | FIB payment callback |
| GET | /api/stats | Dashboard stats |
| GET | /api/products | List all products |
| POST | /api/products | Add a product |
| GET | /api/orders | List all orders |
| POST | /api/sellers | Register a seller |

## Adding a Product (via API)

```bash
curl -X POST http://localhost:5000/api/products \
  -H "Content-Type: application/json" \
  -d '{
    "seller_id": 1,
    "name": "كورس Python المتقدم",
    "price": 25000,
    "type": "digital",
    "file_path": "https://t.me/+invite_link_here"
  }'
```

## How Payment Flow Works

1. User presses "شراء" in bot
2. Bot calls FIB API → gets payment code
3. Order saved in DB with status `pending`
4. User pays via FIB app
5. FIB calls `/webhook/fib` with status `PAID`
6. System calls `deliver_product()` → sends PDF or invite link to user
7. Seller gets notified on Telegram
8. Order status updated to `delivered`
