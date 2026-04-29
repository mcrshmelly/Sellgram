-- ─────────────────────────────────────────────
-- Run this in Supabase SQL Editor (in order)
-- ─────────────────────────────────────────────

-- 1. Sellers table
CREATE TABLE sellers (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  fib_account TEXT,
  telegram_id BIGINT  -- seller's Telegram ID for notifications
);

-- 2. Products table
CREATE TABLE products (
  id SERIAL PRIMARY KEY,
  seller_id INT REFERENCES sellers(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  price INT NOT NULL,
  type TEXT CHECK (type IN ('digital', 'physical')) DEFAULT 'digital',
  file_path TEXT  -- PDF path in Supabase Storage OR invite link URL
);

-- 3. Orders table
CREATE TABLE orders (
  id SERIAL PRIMARY KEY,
  payment_id TEXT UNIQUE,
  user_id BIGINT NOT NULL,           -- Telegram user ID
  product_id INT REFERENCES products(id) ON DELETE SET NULL,
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'paid', 'cancelled', 'delivered')),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- Enable Row Level Security (safety measure)
-- ─────────────────────────────────────────────
ALTER TABLE sellers ENABLE ROW LEVEL SECURITY;
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

-- ─────────────────────────────────────────────
-- Supabase Storage bucket for PDFs
-- Run this AFTER creating the bucket named "products" in Storage UI
-- ─────────────────────────────────────────────
-- INSERT INTO storage.buckets (id, name, public) VALUES ('products', 'products', true);
