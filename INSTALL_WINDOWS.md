# Windows Installation Guide
## AI Community Health & Volunteer Operations Platform — V2.54

---

## Prerequisites

| Software | Version | Download |
|---|---|---|
| Python | 3.12+ | [python.org](https://python.org) |
| Git | Latest | [git-scm.com](https://git-scm.com) |
| VS Code (recommended) | Latest | [code.visualstudio.com](https://code.visualstudio.com) |

---

## Step 1 — Clone the Repository

```powershell
git clone https://github.com/your-org/health-platform.git
cd health-platform
```

---

## Step 2 — Create Virtual Environment

```powershell
python -m venv .venv
.venv\Scripts\activate
```

> You should see `(.venv)` at the start of your prompt.

---

## Step 3 — Install Dependencies

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Step 4 — Configure Environment

```powershell
copy .env.example .env
notepad .env
```

Fill in your Supabase credentials:
```env
DATABASE_URL=postgresql+asyncpg://postgres.[PROJECT_REF]:[PASSWORD]@aws-1-ap-northeast-1.pooler.supabase.com:5432/postgres?sslmode=require
DATABASE_URL_SYNC=postgresql+psycopg2://postgres.[PROJECT_REF]:[PASSWORD]@aws-1-ap-northeast-1.pooler.supabase.com:5432/postgres?sslmode=require
SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
JWT_SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
SUPERADMIN_EMAIL=admin
SUPERADMIN_PASSWORD=ChangeMe123!
```

---

## Step 5 — Run Migrations

```powershell
alembic upgrade head
```

---

## Step 6 — Seed Data

```powershell
python scripts/seed_data.py
```

---

## Step 7 — Start the Application

```powershell
streamlit run app/main.py
```

Open browser: **http://localhost:8501**

Login: `admin` / `ChangeMe123!`

---

## Running Tests

```powershell
pip install aiosqlite pytest pytest-asyncio pytest-cov
pytest --cov=app --cov-report=term-missing
```

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `ModuleNotFoundError` | Activate venv: `.venv\Scripts\activate` |
| `alembic: command not found` | Run `pip install alembic` |
| DB connection error | Check `.env` credentials and port (use 5432, not 6543) |
| `bcrypt` error | Pin: `pip install bcrypt==4.0.1` |
| Port 8501 in use | Run: `streamlit run app/main.py --server.port=8502` |
