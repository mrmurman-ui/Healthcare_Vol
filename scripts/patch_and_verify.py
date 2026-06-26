# -*- coding: utf-8 -*-
"""
SELF-LOCATING PATCH: Finds THIS app's citizens/page.py and patches it directly.
Run from ANY folder: py -3.12 path/to/Healthcare_Production_02/scripts/patch_and_verify.py
"""
import sys, io, os, asyncio, shutil, random
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ── Find the app root (same folder as this script's parent) ──────────────────
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
APP_ROOT    = os.path.dirname(SCRIPT_DIR)
CITIZENS_PY = os.path.join(APP_ROOT, "app", "modules", "citizens", "page.py")
PROFILE_PY  = os.path.join(APP_ROOT, "app", "modules", "citizens", "profile.py")
PYCACHE     = os.path.join(APP_ROOT, "app", "modules", "citizens", "__pycache__")

print("="*60)
print("[PATCH] Citizens Page Fix")
print("="*60)
print(f"  App root  : {APP_ROOT}")
print(f"  page.py   : {CITIZENS_PY}")
print(f"  Exists    : {os.path.exists(CITIZENS_PY)}")

# ── Step 1: Patch page.py if it doesn't have CA code logic ───────────────────
current = open(CITIZENS_PY, encoding="utf-8").read()
needs_patch = "CA{start+i:05d}" not in current

if needs_patch:
    print("\n  [!] page.py needs patching — injecting CA code logic...")

    # Find and replace _ensure_columns
    old_snippet = '''def _ensure_columns():
    with get_sync_db() as db:
        for col, coltype in [
            ("citizen_code","VARCHAR(20)"),
            ("community_code","VARCHAR(10)"),
            ("house_number","VARCHAR(50)"),
            ("village","VARCHAR(100)"),
            ("district","VARCHAR(100)"),
            ("address","TEXT"),
            ("notes","TEXT"),
            ("is_deleted","BOOLEAN DEFAULT FALSE"),
        ]:
            try:
                db.execute(text(
                    f"ALTER TABLE citizens ADD COLUMN IF NOT EXISTS {col} {coltype}"
                ))
            except Exception:
                pass'''

    new_snippet = '''def _ensure_columns():
    with get_sync_db() as db:
        for col, coltype in [
            ("citizen_code","VARCHAR(20)"),
            ("community_code","VARCHAR(10)"),
            ("house_number","VARCHAR(50)"),
            ("village","VARCHAR(100)"),
            ("district","VARCHAR(100)"),
            ("address","TEXT"),
            ("notes","TEXT"),
            ("is_deleted","BOOLEAN DEFAULT FALSE"),
            ("national_id","VARCHAR(13)"),
        ]:
            try:
                db.execute(text(
                    f"ALTER TABLE citizens ADD COLUMN IF NOT EXISTS {col} {coltype}"
                ))
            except Exception:
                pass
        # Auto-assign CA codes
        try:
            max_row = db.execute(text(
                "SELECT citizen_code FROM citizens "
                "WHERE citizen_code LIKE \'CA%\' ORDER BY citizen_code DESC LIMIT 1"
            )).fetchone()
            start = 1
            if max_row and max_row[0]:
                try: start = int(max_row[0][2:]) + 1
                except: start = 1
            no_code = db.execute(text(
                "SELECT id FROM citizens "
                "WHERE citizen_code IS NULL OR citizen_code = \'\' "
                "ORDER BY created_at, full_name"
            )).fetchall()
            for i, row in enumerate(no_code):
                db.execute(text(
                    "UPDATE citizens SET citizen_code=:code "
                    "WHERE id=:id AND (citizen_code IS NULL OR citizen_code=\'\')"
                ), {"code": f"CA{start+i:05d}", "id": str(row[0])})
        except Exception:
            pass'''

    if old_snippet in current:
        shutil.copy2(CITIZENS_PY, CITIZENS_PY + ".bak")
        patched = current.replace(old_snippet, new_snippet)
        open(CITIZENS_PY, "w", encoding="utf-8").write(patched)
        print("  [OK] page.py patched and backup saved as page.py.bak")
    else:
        print("  [WARN] Could not find expected snippet — skipping page.py patch")
        print("         Please copy page.py manually from the fix zip")
else:
    print("\n  [OK] page.py already has CA code logic")

# ── Step 2: Clear pycache ─────────────────────────────────────────────────────
if os.path.exists(PYCACHE):
    shutil.rmtree(PYCACHE)
    print("  [OK] __pycache__ cleared")

# ── Step 3: Patch DB directly ─────────────────────────────────────────────────
print("\n  [DB] Patching database...")
sys.path.insert(0, APP_ROOT)

from sqlalchemy import text as _text

async def patch_db():
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        # Add columns
        for col, coltype in [
            ("citizen_code","VARCHAR(20)"), ("national_id","VARCHAR(13)"),
            ("house_number","VARCHAR(50)"), ("village","VARCHAR(100)"),
            ("district","VARCHAR(100)"),    ("address","TEXT"),
            ("notes","TEXT"),
        ]:
            try:
                await session.execute(_text(
                    f"ALTER TABLE citizens ADD COLUMN IF NOT EXISTS {col} {coltype}"
                ))
            except Exception: pass
        await session.commit()

        # Assign CA codes
        max_row = (await session.execute(_text(
            "SELECT citizen_code FROM citizens WHERE citizen_code LIKE 'CA%' "
            "ORDER BY citizen_code DESC LIMIT 1"
        ))).fetchone()
        start = 1
        if max_row and max_row[0]:
            try: start = int(max_row[0][2:]) + 1
            except: pass

        no_code = (await session.execute(_text(
            "SELECT id FROM citizens WHERE citizen_code IS NULL OR citizen_code='' "
            "ORDER BY created_at, full_name"
        ))).fetchall()

        for i, row in enumerate(no_code):
            await session.execute(_text(
                "UPDATE citizens SET citizen_code=:c WHERE id=:id "
                "AND (citizen_code IS NULL OR citizen_code='')"
            ), {"c": f"CA{start+i:05d}", "id": str(row[0])})
        await session.commit()

        # Assign national IDs
        def gen():
            d = f"{random.choice([1,1,2])}{random.randint(10,96):02d}{random.randint(10,99):02d}{random.randint(10000,99999)}{random.randint(10,99)}"
            t = sum(int(d[i])*(13-i) for i in range(12))
            return d + str((11-(t%11))%10)

        no_nid = (await session.execute(_text(
            "SELECT id FROM citizens WHERE national_id IS NULL OR national_id='' ORDER BY created_at"
        ))).fetchall()
        used = set()
        for row in no_nid:
            n = gen()
            while n in used: n = gen()
            used.add(n)
            await session.execute(_text(
                "UPDATE citizens SET national_id=:n WHERE id=:id AND (national_id IS NULL OR national_id='')"
            ), {"n": n, "id": str(row[0])})
        await session.commit()

        # Verify
        total  = (await session.execute(_text("SELECT COUNT(*) FROM citizens WHERE citizen_code LIKE 'CA%'"))).scalar()
        sample = (await session.execute(_text(
            "SELECT citizen_code, full_name, national_id FROM citizens "
            "WHERE citizen_code LIKE 'CA%' ORDER BY citizen_code LIMIT 3"
        ))).fetchall()
        return total, len(no_code), len(no_nid), sample

total, codes, nids, sample = asyncio.run(patch_db())

print(f"  [OK] CA codes assigned: {codes}")
print(f"  [OK] National IDs assigned: {nids}")
print(f"  [OK] Total with CA code: {total}")
print("\n  Sample:")
for r in sample:
    n = r[2] or ""
    fmt = f"{n[0]}-{n[1:5]}-{n[5:10]}-{n[10:12]}-{n[12]}" if len(n)==13 else n
    print(f"    {r[0]}  {(r[1] or '')[:25]:25s}  NID:{fmt}")

print("\n" + "="*60)
print("[DONE] Now restart Streamlit!")
print("="*60)
