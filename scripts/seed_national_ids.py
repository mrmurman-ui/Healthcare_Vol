# -*- coding: utf-8 -*-
"""
Generate realistic fake Thai national ID numbers for demo citizens.
Run: py -3.12 scripts/seed_national_ids.py
Format: x-xxxx-xxxxx-xx-x  (13 digits, Luhn-like structure)
"""
import sys, io, os, asyncio, random
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sqlalchemy import text

# Thai province codes 10-96 (valid range)
PROVINCE_CODES = list(range(10, 97))


def gen_thai_nid() -> str:
    """Generate a syntactically valid fake Thai 13-digit national ID."""
    # Digit 1: type (1=Thai citizen, 2=Thai with permanent residence, etc.)
    d1 = random.choice([1, 1, 1, 2, 3])
    # Digits 2-5: province + district code
    province = random.choice(PROVINCE_CODES)
    d2_5 = f"{province:02d}{random.randint(10,99):02d}"
    # Digits 6-10: birth/sequence
    d6_10 = f"{random.randint(10000,99999)}"
    # Digits 11-12: sequence
    d11_12 = f"{random.randint(10,99)}"
    # Digit 13: check digit (computed)
    digits = f"{d1}{d2_5}{d6_10}{d11_12}"
    # Thai NID check digit: sum(d[i] * (13-i)) mod 11, check = (11 - sum%11) % 10
    total = sum(int(digits[i]) * (13 - i) for i in range(12))
    check = (11 - (total % 11)) % 10
    return f"{digits}{check}"


async def main():
    from app.core.database import AsyncSessionLocal
    print("="*55)
    print("[National ID] Generating fake Thai IDs for citizens...")
    print("="*55)
    async with AsyncSessionLocal() as session:
        # Add column if not exists
        try:
            await session.execute(text(
                "ALTER TABLE citizens ADD COLUMN IF NOT EXISTS national_id VARCHAR(13)"
            ))
            await session.commit()
        except Exception: pass

        # Get citizens without national_id
        rows = (await session.execute(text("""
            SELECT id FROM citizens
            WHERE national_id IS NULL OR national_id = ''
            ORDER BY created_at
        """))).fetchall()

        print(f"  Citizens needing ID: {len(rows)}")
        updated = 0
        used_ids = set()
        for row in rows:
            # Ensure uniqueness
            nid = gen_thai_nid()
            while nid in used_ids:
                nid = gen_thai_nid()
            used_ids.add(nid)
            await session.execute(text(
                "UPDATE citizens SET national_id=:nid WHERE id=:id "
                "AND (national_id IS NULL OR national_id='')"
            ), {"nid": nid, "id": str(row[0])})
            updated += 1

        await session.commit()
        total = (await session.execute(text(
            "SELECT COUNT(*) FROM citizens WHERE national_id IS NOT NULL AND national_id != ''"
        ))).scalar()

    print(f"  [OK] Assigned {updated} national IDs")
    print(f"  [OK] Total citizens with ID: {total}")
    print("\n  Sample format: 1-1203-12345-67-8")
    print("  NOTE: These are fake IDs for demo only, not real citizens.")
    print("\n[DONE] Restart Streamlit to see national IDs in profiles.")

if __name__ == "__main__":
    asyncio.run(main())
