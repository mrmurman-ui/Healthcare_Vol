# Supabase Setup Guide
## AI Community Health & Volunteer Operations Platform — V2.54

---

## Step 1 — Create Supabase Project

1. Go to [supabase.com](https://supabase.com) → Sign up / Sign in
2. Click **New Project**
3. Choose:
   - **Organization**: your org
   - **Project name**: `health-platform`
   - **Database password**: strong password (save it!)
   - **Region**: `Southeast Asia (Singapore)` or `Northeast Asia (Tokyo)` for Thailand
4. Click **Create new project** — takes ~2 minutes

---

## Step 2 — Get Connection Credentials

### Database URL
1. Dashboard → **Settings** → **Database**
2. Scroll to **Connection string** → select **URI** tab
3. Copy the string — it looks like:
```
postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-1-ap-northeast-1.pooler.supabase.com:5432/postgres
```

> ⚠️ **Always use port 5432** (direct connection).
> Port 6543 is PgBouncer — causes `prepared statement` errors with asyncpg.

### Project Reference
Found in:
- Settings → General → **Reference ID** (e.g. `jmmvjatilibasxpmfxbe`)
- This goes after `postgres.` in your username

### Full credentials for .env:
```env
DATABASE_URL=postgresql+asyncpg://postgres.[REF]:[PASSWORD]@aws-1-ap-northeast-1.pooler.supabase.com:5432/postgres?sslmode=require
DATABASE_URL_SYNC=postgresql+psycopg2://postgres.[REF]:[PASSWORD]@aws-1-ap-northeast-1.pooler.supabase.com:5432/postgres?sslmode=require
```

---

## Step 3 — Get API Keys (for file storage)

Dashboard → **Settings** → **API**:

| Key | Description |
|---|---|
| `anon` / `public` | For client-side calls |
| `service_role` | For server-side (admin) calls |
| `Project URL` | Your Supabase project URL |

---

## Step 4 — Verify Connection with pgAdmin

Open pgAdmin → Register Server:
| Field | Value |
|---|---|
| Name | `Healthcare DB` |
| Host | `aws-1-ap-northeast-1.pooler.supabase.com` |
| Port | `5432` |
| Database | `postgres` |
| Username | `postgres.[YOUR_PROJECT_REF]` |
| Password | your database password |

---

## Step 5 — Run Migrations

```powershell
# From your project directory with .env configured
alembic upgrade head
```

Verify in Supabase Dashboard → **Table Editor** — you should see all tables.

---

## Database Password Reset

If you forget your password:
1. Dashboard → **Settings** → **Database**
2. Scroll to **Database password**
3. Click **Reset database password**
4. Update your `.env` and Streamlit secrets

---

## Special Characters in Password

If your password contains `@`, `#`, `!`, `$`, URL-encode them:
| Character | Encoded |
|---|---|
| `@` | `%40` |
| `#` | `%23` |
| `!` | `%21` |
| `$` | `%24` |
| `%` | `%25` |

Example: `my@pass!` → `my%40pass%21`

---

## Free Tier Limits

| Resource | Free Tier |
|---|---|
| Database size | 500 MB |
| Bandwidth | 5 GB/month |
| API requests | Unlimited |
| Projects | 2 active |
| Pausing | After 1 week inactivity |

> Upgrade to **Pro ($25/month)** for production workloads.

---

## Row Level Security (RLS)

Supabase enables RLS by default on new tables.
Our platform uses server-side psycopg2/asyncpg connections which bypass RLS.
No additional RLS configuration needed.
