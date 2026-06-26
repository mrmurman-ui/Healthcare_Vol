# -*- coding: utf-8 -*-
"""
EMERGENCY PATCH: Assign CA codes to all citizens immediately.
Run from Healthcare_Production_02 folder:
    py -3.12 scripts/patch_citizens_now.py
"""
import sys, io, os, asyncio
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sqlalchemy import text

async def main():
    from app.core.database import AsyncSessionLocal
    print("="*55)
    print("[PATCH] Assigning CA codes + national IDs to citizens")
    print("="*55)
    async with AsyncSessionLocal() as session:
        # Add columns if missing
        for col, coltype in [
            ("citizen_code", "VARCHAR(20)"),
            ("national_id",  "VARCHAR(13)"),
            ("house_number", "VARCHAR(50)"),
            ("village",      "VARCHAR(100)"),
            ("district",     "VARCHAR(100)"),
            ("address",      "TEXT"),
            ("notes",        "TEXT"),
        ]:
            try:
                await session.execute(text(
                    f"ALTER TABLE citizens ADD COLUMN IF NOT EXISTS {col} {coltype}"
                ))
            except Exception: pass
        await session.commit()
        print("  [OK] Columns ensured")

        # Assign CA codes
        max_row = (await session.execute(text(
            "SELECT citizen_code FROM citizens "
            "WHERE citizen_code LIKE 'CA%' "
            "ORDER BY citizen_code DESC LIMIT 1"
        ))).fetchone()
        start = 1
        if max_row and max_row[0]:
            try: start = int(max_row[0][2:]) + 1
            except: start = 1

        no_code = (await session.execute(text(
            "SELECT id FROM citizens "
            "WHERE citizen_code IS NULL OR citizen_code = '' "
            "ORDER BY created_at, full_name"
        ))).fetchall()
        print(f"  Citizens needing CA code: {len(no_code)}")

        for i, row in enumerate(no_code):
            await session.execute(text(
                "UPDATE citizens SET citizen_code=:code "
                "WHERE id=:id AND (citizen_code IS NULL OR citizen_code='')"
            ), {"code": f"CA{start+i:05d}", "id": str(row[0])})
            if i % 500 == 0 and i > 0:
                print(f"    ... {i} done")
        await session.commit()
        print(f"  [OK] Assigned CA{start:05d} - CA{start+len(no_code)-1:05d}")

        # Assign national IDs
        import random
        def gen_nid():
            d1 = random.choice([1,1,1,2,3])
            prov = random.randint(10,96)
            dist = random.randint(10,99)
            seq  = random.randint(10000,99999)
            seq2 = random.randint(10,99)
            digits = f"{d1}{prov:02d}{dist:02d}{seq}{seq2}"
            total = sum(int(digits[i]) * (13-i) for i in range(12))
            check = (11 - (total % 11)) % 10
            return f"{digits}{check}"

        no_nid = (await session.execute(text(
            "SELECT id FROM citizens "
            "WHERE national_id IS NULL OR national_id = '' "
            "ORDER BY created_at"
        ))).fetchall()
        print(f"  Citizens needing national ID: {len(no_nid)}")

        used = set()
        for row in no_nid:
            nid = gen_nid()
            while nid in used: nid = gen_nid()
            used.add(nid)
            await session.execute(text(
                "UPDATE citizens SET national_id=:nid "
                "WHERE id=:id AND (national_id IS NULL OR national_id='')"
            ), {"nid": nid, "id": str(row[0])})
        await session.commit()
        print(f"  [OK] {len(no_nid)} national IDs assigned")

        # Verify
        total = (await session.execute(text(
            "SELECT COUNT(*) FROM citizens WHERE citizen_code LIKE 'CA%'"
        ))).scalar()
        print(f"\n  Total with CA code: {total}")
        sample = (await session.execute(text(
            "SELECT citizen_code, full_name, national_id FROM citizens "
            "WHERE citizen_code LIKE 'CA%' ORDER BY citizen_code LIMIT 5"
        ))).fetchall()
        print("\n  Sample records:")
        for r in sample:
            n = r[2] or ""
            fmt = f"{n[0]}-{n[1:5]}-{n[5:10]}-{n[10:12]}-{n[12]}" if len(n)==13 else n
            print(f"    {r[0]}  {r[1][:20]:20s}  {fmt}")

    print("\n[DONE] Now restart Streamlit to see the changes.")

if __name__ == "__main__":
    asyncio.run(main())
