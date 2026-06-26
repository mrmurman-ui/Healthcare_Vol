# Database Backup Guide
## AI Community Health & Volunteer Operations Platform — V2.54

---

## Backup Strategy

| Frequency | Type | Format | Retention |
|---|---|---|---|
| Daily | Incremental JSON export | JSON | 30 days |
| Weekly | Full data export | Excel + JSON | 12 weeks |
| Monthly | Archive | SQL dump | 12 months |

---

## Method 1 — In-App Backup (Recommended)

1. Login as Super Admin
2. Navigate to **System Admin → Backup & Restore**
3. Click **Export All Data (JSON)** or **Export All Data (Excel)**
4. Save the downloaded file to a safe location

---

## Method 2 — Supabase Dashboard Backup

1. Supabase Dashboard → **Settings** → **Database**
2. Scroll to **Backups** (Pro plan feature)
3. Click **Download backup**

Free tier: no automatic backups — use Method 1 or 3.

---

## Method 3 — pg_dump (Full SQL Backup)

```powershell
# Install psql tools on Windows
# Download from: https://www.postgresql.org/download/windows/

# Supabase backup
pg_dump "postgresql://postgres.[REF]:[PASS]@aws-1-ap-northeast-1.pooler.supabase.com:5432/postgres" `
  --no-owner --no-acl `
  > backup_2026_01_01.sql

# Restore
psql "postgresql://postgres.[REF]:[PASS]@aws-1-ap-northeast-1.pooler.supabase.com:5432/postgres" `
  < backup_2026_01_01.sql
```

---

## Recovery Procedure

```powershell
# 1. Restore database from SQL backup
psql [connection_string] < backup_YYYYMMDD.sql

# 2. Run any pending migrations
alembic upgrade head

# 3. Seed missing configuration
python scripts/seed_data.py

# 4. Restart application
streamlit run app/main.py

# 5. Verify — open System Health dashboard
# http://localhost:8501 → System Admin → System Health
```

---

## Automated Backup Script (Windows Task Scheduler)

Create `backup.ps1`:
```powershell
$timestamp = Get-Date -Format "yyyyMMdd_HHmm"
$backup_dir = "C:\Backups\HealthPlatform"

# Create backup directory
New-Item -ItemType Directory -Force -Path $backup_dir

# Export via Python
cd C:\path\to\health-platform
.venv\Scripts\activate
python -c "
import sys
sys.path.insert(0, '.')
import json
from app.core.db_sync import get_sync_db
from sqlalchemy import text

tables = ['volunteers','households','citizens','home_visits','referrals']
backup = {}
with get_sync_db() as db:
    for tbl in tables:
        rows = db.execute(text(f'SELECT * FROM {tbl}')).mappings().all()
        backup[tbl] = [dict(r) for r in rows]

with open(r'$backup_dir\backup_$timestamp.json', 'w', encoding='utf-8') as f:
    json.dump(backup, f, ensure_ascii=False, default=str)
print('Backup complete')
"
```

Schedule in Windows Task Scheduler to run daily at 2:00 AM.

---

## Backup Validation

After each backup:
1. Open the JSON file — verify it's valid JSON
2. Check record counts match System Health dashboard
3. Test restore on a staging environment monthly
