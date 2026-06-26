# -*- coding: utf-8 -*-
"""
Assign CA00001-format citizen codes to all citizens that don't have one.
Run: py -3.12 scripts/assign_citizen_codes.py
"""
import sys, io, os, asyncio
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sqlalchemy import text

async def main():
    from app.core.database import AsyncSessionLocal
    print("="*55)
    print("[Citizen Code] Assigning CA00001 format codes...")
    print("="*55)
    async with AsyncSessionLocal() as session:
        # Add column if missing
        try:
            await session.execute(text(
                "ALTER TABLE citizens ADD COLUMN IF NOT EXISTS citizen_code VARCHAR(20)"
            ))
            await session.commit()
        except Exception: pass

        # Get citizens without codes, ordered by created_at
        rows = (await session.execute(text("""
            SELECT id FROM citizens
            WHERE citizen_code IS NULL OR citizen_code = ''
            ORDER BY created_at, full_name
        """))).fetchall()

        # Find highest existing code
        max_row = (await session.execute(text("""
            SELECT citizen_code FROM citizens
            WHERE citizen_code LIKE 'CA%'
            ORDER BY citizen_code DESC LIMIT 1
        """))).fetchone()

        start_num = 1
        if max_row and max_row[0]:
            try: start_num = int(max_row[0][2:]) + 1
            except: start_num = 1

        updated = 0
        for i, row in enumerate(rows):
            code = f"CA{start_num + i:05d}"
            await session.execute(text(
                "UPDATE citizens SET citizen_code=:code WHERE id=:id AND (citizen_code IS NULL OR citizen_code='')"
            ), {"code": code, "id": str(row[0])})
            updated += 1

        await session.commit()

        # Verify
        total = (await session.execute(text(
            "SELECT COUNT(*) FROM citizens WHERE citizen_code LIKE 'CA%'"
        ))).scalar()

    print(f"  [OK] Assigned {updated} new codes")
    print(f"  [OK] Total citizens with CA codes: {total}")
    print(f"  Range: CA{start_num:05d} - CA{start_num+updated-1:05d}")
    print("\n[DONE] Restart Streamlit to see codes in citizen list.")

if __name__ == "__main__":
    asyncio.run(main())
