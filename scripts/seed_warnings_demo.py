# -*- coding: utf-8 -*-
"""
Seed realistic early warning / notification demo data.
Run: py -3.12 scripts/seed_warnings_demo.py
"""
import sys, io, os, asyncio, random
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sqlalchemy import text

WARN_TEMPLATES = [
    # (alert_type, severity, title, detail)
    ("no_visit","critical",
     "ผู้สูงอายุไม่ได้รับการเยี่ยมบ้านนานกว่า 60 วัน",
     "ผู้สูงอายุอยู่คนเดียว อายุ 82 ปี ไม่มีผู้ดูแล ไม่มีการเยี่ยมบ้านมากกว่า 60 วัน เสี่ยงต่อการเกิดอุบัติเหตุในบ้าน"),
    ("bedridden_alone","critical",
     "ผู้ป่วยติดเตียงอยู่คนเดียว ไม่มีผู้ดูแล",
     "ผู้ป่วยอัมพฤกษ์ติดเตียงอยู่คนเดียวในบ้าน ลูกทำงานต่างจังหวัด ไม่มีผู้ดูแลในชุมชน เสี่ยงต่อภาวะแทรกซ้อน"),
    ("open_referral","high",
     "การส่งต่อโรงพยาบาลค้างนานกว่า 30 วันยังไม่เสร็จสิ้น",
     "ส่งตัวผู้ป่วยความดันโลหิตสูงเรื้อรังไปพบแพทย์เฉพาะทางเมื่อ 30 วันก่อน ยังไม่ทราบผลการรักษา ไม่มีการติดตาม"),
    ("no_assessment","high",
     "ไม่มีการประเมินสุขภาพผู้สูงอายุนานกว่า 90 วัน",
     "ผู้สูงอายุอายุ 75 ปี มีโรคเบาหวานและความดันโลหิตสูง ไม่ได้รับการประเมินสุขภาพมากกว่า 3 เดือน"),
    ("weight_loss","high",
     "ผู้ป่วยน้ำหนักลดผิดปกติ 5 กก. ใน 1 เดือน",
     "บันทึกน้ำหนักพบว่าลดลง 5 กิโลกรัมในเวลา 1 เดือน ผู้ป่วยมีประวัติมะเร็งปอด ควรส่งพบแพทย์โดยด่วน"),
    ("social_isolation","medium",
     "ผู้สูงอายุมีภาวะโดดเดี่ยวทางสังคม ไม่ออกจากบ้าน",
     "ผู้สูงอายุหญิง อายุ 78 ปี ไม่ออกจากบ้านมากกว่า 2 เดือน ไม่มีการติดต่อกับเพื่อนบ้าน มีความเสี่ยงซึมเศร้า"),
    ("homebound_no_caregiver","medium",
     "ผู้ป่วยติดบ้านไม่มีผู้ดูแลในช่วงกลางวัน",
     "ผู้สูงอายุมีปัญหาเดิน ต้องใช้ไม้เท้า ลูกออกไปทำงานตั้งแต่เช้าถึงเย็น ไม่มีผู้ดูแลในช่วง 08.00-17.00 น."),
    ("no_visit","medium",
     "อสม. ไม่สามารถติดต่อผู้สูงอายุได้นาน 2 สัปดาห์",
     "โทรศัพท์ไม่รับสาย ไปที่บ้านก็ไม่มีคนเปิดประตู ไม่ทราบว่าผู้สูงอายุอยู่ที่ไหน"),
    ("no_assessment","medium",
     "ผู้ป่วยเบาหวานไม่ได้วัดระดับน้ำตาลในเลือดมานานกว่า 2 เดือน",
     "ผู้ป่วยเบาหวานชนิดที่ 2 ควบคุมไม่ได้ ไม่ได้ตรวจระดับน้ำตาลในเลือดมากกว่า 60 วัน อาจมีภาวะแทรกซ้อน"),
    ("open_referral","low",
     "นัดพบแพทย์จักษุแพทย์ยังไม่ได้ไป",
     "ส่งต่อผู้ป่วยไปพบจักษุแพทย์เรื่องตามัวจากเบาหวาน นัดแล้ว 3 ครั้ง ยังไม่ได้ไปทุกครั้ง"),
    ("social_isolation","low",
     "ผู้สูงอายุชายอยู่คนเดียวหลังภรรยาเสียชีวิต ขาดการติดต่อกับครอบครัว",
     "ภรรยาเพิ่งเสียชีวิตเมื่อ 3 เดือนก่อน ลูกอยู่ต่างประเทศ สังเกตว่าดูเศร้าและไม่ค่อยพูดคุย"),
    ("weight_loss","low",
     "ผู้สูงอายุรับประทานอาหารได้น้อย น้ำหนักลดลงต่อเนื่อง",
     "ผู้สูงอายุฟันหักหลายซี่ เคี้ยวอาหารลำบาก รับประทานได้เฉพาะอาหารอ่อน น้ำหนักลดลง 2 กก. ในเดือนที่ผ่านมา"),
    ("homebound_no_caregiver","low",
     "ผู้ป่วยหลังผ่าตัดขาต้องการความช่วยเหลือในการทำกายภาพบำบัด",
     "ผ่าตัดหัวเข่าเมื่อ 6 สัปดาห์ที่แล้ว แพทย์นัดทำกายภาพบำบัดแต่ไม่มีคนพาไป ยังใช้ไม้เท้าอยู่"),
    ("no_visit","critical",
     "ผู้สูงอายุที่มีความเสี่ยงสูงหายไปจากชุมชน",
     "ผู้สูงอายุมีประวัติสมองเสื่อมระดับปานกลาง หายออกจากบ้านในช่วงเย็น ครอบครัวตามหาไม่พบ"),
    ("bedridden_alone","high",
     "ผู้ป่วยติดเตียงมีแผลกดทับระยะที่ 3 ต้องการการรักษาเร่งด่วน",
     "พบแผลกดทับขนาดใหญ่บริเวณก้นกบและส้นเท้า ผู้ดูแลไม่มีความรู้การทำแผล ต้องส่งพบพยาบาลโดยเร็ว"),
]

async def main():
    from app.core.database import AsyncSessionLocal
    print("="*55)
    print("[Warning Seeder] Seeding 15 realistic warnings...")
    print("="*55)
    async with AsyncSessionLocal() as session:
        cit_ids = [str(r[0]) for r in
                   (await session.execute(text("SELECT id FROM citizens LIMIT 100"))).fetchall()]

        # Delete old demo warnings
        await session.execute(text(
            "UPDATE early_warnings SET is_deleted=true WHERE detail LIKE '%ผู้สูงอายุ%' "
            "AND created_by='demo_seed'"
        ))
        await session.commit()

        ok = 0
        statuses = ["open","open","open","acknowledged","resolved"]
        for i, (wtype, sev, title, detail) in enumerate(WARN_TEMPLATES):
            cid = random.choice(cit_ids) if cit_ids else None
            status = random.choice(statuses)
            try:
                await session.execute(text("""
                    INSERT INTO early_warnings
                        (id, citizen_id, alert_type, severity, title, detail,
                         status, is_deleted, created_at, updated_at, created_by, updated_by)
                    VALUES
                        (gen_random_uuid(), :cid, :atype, :sev, :title, :detail,
                         :status, false, NOW() - INTERVAL ':days days',
                         NOW(), 'demo_seed', 'demo_seed')
                """.replace(":days", str(random.randint(0,30))),
                {
                    "cid": cid, "atype": wtype, "sev": sev,
                    "title": title, "detail": detail, "status": status,
                }))
                ok += 1
            except Exception as e:
                # Try without interval interpolation issue
                try:
                    await session.execute(text("""
                        INSERT INTO early_warnings
                            (id, citizen_id, alert_type, severity, title, detail,
                             status, is_deleted, created_at, updated_at, created_by, updated_by)
                        VALUES
                            (gen_random_uuid(), :cid, :atype, :sev, :title, :detail,
                             :status, false, NOW(), NOW(), 'demo_seed', 'demo_seed')
                    """), {"cid": cid, "atype": wtype, "sev": sev,
                           "title": title, "detail": detail, "status": status})
                    ok += 1
                except Exception as e2:
                    print(f"  [WARN] Row {i+1}: {e2}")

        await session.commit()

        # Verify
        counts = (await session.execute(text("""
            SELECT severity, COUNT(*) FROM early_warnings
            WHERE created_by='demo_seed' AND (is_deleted=false OR is_deleted IS NULL)
            GROUP BY severity ORDER BY severity
        """))).fetchall()

    print(f"\n  [OK] Inserted {ok}/15 warnings")
    print("\n  Breakdown by severity:")
    SEV = {"critical":"วิกฤต","high":"สูง","medium":"ปานกลาง","low":"ต่ำ"}
    for r in counts:
        print(f"    {SEV.get(r[0],r[0]):12s} ({r[0]:8s}): {r[1]}")
    print("\n[DONE] Restart Streamlit to see updated alerts.")

if __name__ == "__main__":
    asyncio.run(main())
