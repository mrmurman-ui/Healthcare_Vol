# -*- coding: utf-8 -*-
"""
Seed 30 demo tasks: 20 completed, 5 assigned/pending, 5 overdue.
Run: py -3.12 scripts/seed_tasks_demo.py
"""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio, random
from datetime import date, timedelta
from sqlalchemy import text


TASK_TITLES = [
    "เยี่ยมบ้านผู้สูงอายุกลุ่มเสี่ยงสูง ชุมชนวัดเกต",
    "ติดตามผู้ป่วยเบาหวานที่ขาดยา 3 สัปดาห์",
    "ส่งเอกสารสิทธิ์สวัสดิการผู้สูงอายุ 80 ปีขึ้นไป",
    "ประเมินสุขภาพประจำปีผู้สูงอายุ อสม.หมู่ 5",
    "จัดกิจกรรมออกกำลังกายชมรมผู้สูงอายุสันทราย",
    "สำรวจครัวเรือนใหม่ชุมชนหนองหอย",
    "ติดตามผู้ป่วยหลังส่งตัวโรงพยาบาลนครพิงค์",
    "แจกยาผู้ป่วยความดันโลหิตสูงเรื้อรัง",
    "ลงทะเบียนผู้สูงอายุรับเบี้ยยังชีพรายใหม่",
    "ตรวจสอบบ้านผู้สูงอายุที่อยู่คนเดียวชุมชนช้างเผือก",
    "ประสานงานมูลนิธิปอเต็กตึ้งขอรับผ้าอ้อมผู้ใหญ่",
    "นัดหมายรถรับส่งผู้ป่วยติดเตียงไปพบแพทย์",
    "เก็บข้อมูลสุขภาพจิตผู้ดูแลผู้สูงอายุ",
    "แจ้งเตือนรับวัคซีนไข้หวัดใหญ่กลุ่มเสี่ยง",
    "ติดตามผู้ป่วยโรคหัวใจที่มีอาการเจ็บหน้าอก",
    "ส่งมอบอุปกรณ์ช่วยเหลือผู้พิการ ไม้เท้าและรถเข็น",
    "ตรวจวัดความดันโลหิตกลุ่มเสี่ยงชุมชนป่าแดด",
    "ให้ความรู้โรคเบาหวานและการควบคุมอาหาร",
    "ติดตามผู้ป่วยติดเตียงที่มีแผลกดทับ",
    "รายงานผลการเยี่ยมบ้านประจำเดือนมิถุนายน",
    "ประชุม อสม. ประจำเดือนและวางแผนการดูแล",
    "ตรวจสอบสต็อกยาและอุปกรณ์การแพทย์",
    "บันทึกข้อมูลผู้ป่วยโรคเรื้อรังรายใหม่",
    "ติดตามเด็กที่มีภาวะทุพโภชนาการในชุมชน",
    "จัดทำทะเบียนครัวเรือนเขตรับผิดชอบ",
    "ส่งต่อผู้ป่วยฉุกเฉินไปโรงพยาบาลมหาราชฯ",
    "ตรวจคัดกรองมะเร็งปากมดลูกกลุ่มเสี่ยง",
    "ดูแลหญิงตั้งครรภ์ในพื้นที่รับผิดชอบ",
    "ตรวจวัดระดับน้ำตาลในเลือดผู้ป่วยเบาหวาน",
    "สำรวจแหล่งเพาะพันธุ์ยุงลายในชุมชน",
]

TASK_TYPES = ["home_visit","referral_followup","citizen_followup",
              "community_survey","health_education","medication_delivery"]


async def main():
    from app.core.database import AsyncSessionLocal

    print("="*55)
    print("[Task Seeder] 30 Demo Tasks: 20 done / 5 pending / 5 overdue")
    print("="*55)

    async with AsyncSessionLocal() as session:
        # Get IDs
        cit_ids = [str(r[0]) for r in
                   (await session.execute(text("SELECT id FROM citizens LIMIT 100"))).fetchall()]
        vol_ids = [str(r[0]) for r in
                   (await session.execute(text("SELECT id FROM volunteers LIMIT 30"))).fetchall()]

        print(f"  Citizens available: {len(cit_ids)}")
        print(f"  Volunteers available: {len(vol_ids)}")

        # Clear previous demo tasks
        await session.execute(text(
            "UPDATE tasks SET is_deleted=true WHERE task_code LIKE 'TASK-2569-C%' "
            "OR task_code LIKE 'TASK-2569-P%' OR task_code LIKE 'TASK-2569-O%'"
        ))
        await session.commit()
        print("  [OK] Cleared previous demo tasks")

        today = date.today()
        tasks = []

        # 20 COMPLETED
        for i in range(20):
            due = today - timedelta(days=random.randint(5, 60))
            tasks.append({
                "code": f"TASK-2569-C{i+1:03d}",
                "title": TASK_TITLES[i],
                "type": random.choice(TASK_TYPES),
                "priority": random.choices(
                    ["low","medium","high","critical"],[15,45,28,12])[0],
                "status": "completed",
                "due": str(due),
                "cid": random.choice(cit_ids) if cit_ids else None,
                "vid": random.choice(vol_ids) if vol_ids else None,
            })

        # 5 ASSIGNED (pending, future due date)
        for i in range(5):
            due = today + timedelta(days=random.randint(3, 14))
            tasks.append({
                "code": f"TASK-2569-P{i+1:03d}",
                "title": TASK_TITLES[20+i],
                "type": random.choice(TASK_TYPES),
                "priority": random.choices(["medium","high"],[60,40])[0],
                "status": "assigned",
                "due": str(due),
                "cid": random.choice(cit_ids) if cit_ids else None,
                "vid": random.choice(vol_ids) if vol_ids else None,
            })

        # 5 OVERDUE (past due date, not completed)
        for i in range(5):
            due = today - timedelta(days=random.randint(1, 15))
            tasks.append({
                "code": f"TASK-2569-O{i+1:03d}",
                "title": TASK_TITLES[25+i],
                "type": random.choice(TASK_TYPES),
                "priority": random.choices(["high","critical"],[50,50])[0],
                "status": "overdue",
                "due": str(due),
                "cid": random.choice(cit_ids) if cit_ids else None,
                "vid": random.choice(vol_ids) if vol_ids else None,
            })

        ok = 0
        for t in tasks:
            try:
                await session.execute(text("""
                    INSERT INTO tasks
                        (id, task_code, title, task_type, priority, status,
                         due_date, citizen_id, is_deleted,
                         created_at, updated_at, created_by, updated_by)
                    VALUES
                        (gen_random_uuid(), :code, :title, :type, :priority, :status,
                         :due, :cid, false,
                         NOW(), NOW(), 'demo', 'demo')
                    ON CONFLICT (task_code) DO UPDATE SET
                        title=EXCLUDED.title, status=EXCLUDED.status,
                        priority=EXCLUDED.priority, due_date=EXCLUDED.due_date,
                        is_deleted=false, updated_at=NOW()
                """), {"code":t["code"],"title":t["title"],"type":t["type"],
                       "priority":t["priority"],"status":t["status"],
                       "due":t["due"],"cid":t["cid"]})

                # Assign volunteer
                if t["vid"]:
                    try:
                        tid = (await session.execute(text(
                            "SELECT id FROM tasks WHERE task_code=:c"
                        ), {"c": t["code"]})).scalar()
                        if tid:
                            await session.execute(text("""
                                INSERT INTO task_volunteers (id,task_id,volunteer_id)
                                VALUES (gen_random_uuid(),:tid,:vid)
                                ON CONFLICT DO NOTHING
                            """), {"tid":str(tid),"vid":t["vid"]})
                    except Exception:
                        pass

                ok += 1
            except Exception as e:
                print(f"  [WARN] {t['code']}: {e}")

        await session.commit()

        # Verify
        rows = (await session.execute(text("""
            SELECT status, COUNT(*) FROM tasks
            WHERE (is_deleted=false OR is_deleted IS NULL)
              AND (task_code LIKE 'TASK-2569-C%'
                OR task_code LIKE 'TASK-2569-P%'
                OR task_code LIKE 'TASK-2569-O%')
            GROUP BY status ORDER BY status
        """))).fetchall()

    print(f"\n  [OK] Inserted/updated {ok}/30 tasks")
    print("\n  Status breakdown:")
    STATUS_TH = {
        "completed":  "[Done]    เสร็จสิ้น",
        "assigned":   "[Pending] มอบหมายแล้ว/รอดำเนิน",
        "overdue":    "[Overdue] เกินกำหนด",
        "in_progress":"[Running] กำลังดำเนินการ",
        "new":        "[New]     ใหม่",
    }
    total = 0
    for r in rows:
        label = STATUS_TH.get(r[0], r[0])
        print(f"    {label:35s}: {r[1]}")
        total += r[1]
    print(f"    {'Total':35s}: {total}")
    print("\n[OK] Task seeding complete!")
    print("    Restart Streamlit to clear cache and see updated figures.")


if __name__ == "__main__":
    asyncio.run(main())
