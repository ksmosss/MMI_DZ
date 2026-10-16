-- Run once in Supabase SQL Editor before enabling Google sign-in.
-- These records are short-lived, single-use codes, not OAuth access tokens.
CREATE TABLE IF NOT EXISTS oauth_exchange_tickets (
  token_hash VARCHAR(64) PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  expires_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_oauth_exchange_tickets_expires_at ON oauth_exchange_tickets(expires_at);
