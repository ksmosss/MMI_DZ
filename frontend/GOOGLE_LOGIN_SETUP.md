# Google OAuth: Vercel + Supabase

## 1. Supabase migration
Supabase → SQL Editor → New query: paste and Run `backend/migrations/002_google_oauth_tickets.sql`.
Verify via `SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'oauth_exchange_tickets';`.

## 2. Google Cloud Console
Go to https://console.cloud.google.com/apis/credentials and choose your project.
Configure **Google Auth Platform → Branding/Audience** (OAuth consent screen), then create an OAuth client **Web application** under **Clients**.
Authorized JavaScript origins: `https://mmidz.vercel.app` (optional for this server-side redirect flow, but safe).
Authorized redirect URI, EXACT: `https://mmidz.vercel.app/api/auth/google/callback`.
For External apps in Testing, add your Google account as a test user; for public access, publish and comply with Google's verification requirements, if any.

## 3. Vercel → Project → Settings → Environment Variables (Production)
- GOOGLE_CLIENT_ID = Google OAuth Web application Client ID
- GOOGLE_CLIENT_SECRET = Google OAuth Web application Client secret
- FRONTEND_URL = https://mmidz.vercel.app
- COOKIE_SECURE = true
- JWT_SECRET = existing secret (keep unchanged)
- DATABASE_URL = existing Supabase transaction pooler connection string

Ensure `VITE_API_BASE_URL` is missing or `/api`, not an unrelated host. Redeploy after editing environment variables.

## 4. Verify
Visit https://mmidz.vercel.app/ → «Войти через Google». It redirects to Google and back. If Google shows `redirect_uri_mismatch`, confirm exact URI from step 2 and your deployed domain. If server returns 503, confirm Google variables and redeploy. If exchange fails, check that SQL migration ran and Vercel Runtime Logs show no DB error.

## Security
Do not commit OAuth secrets or DATABASE_URL to Git. New login codes are hashed and consumed atomically in Supabase so multiple Vercel invocations work correctly. Old login tokens will continue working as JWT_SECRET is unchanged.
