# -*- coding: utf-8 -*-
"""
Seed demo data for: CVI scores, community projects, campaigns, risk scores.
Run: py -3.12 scripts/seed_all_demo.py
"""
import sys, io, os, asyncio, random
from datetime import date, timedelta
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sqlalchemy import text

TODAY = date.today()


async def seed_cvi(session, cit_ids):
    """Seed CVI scores for all citizens."""
    print("\n[1/4] CVI Scores...")
    await session.execute(text("DELETE FROM cvi_scores WHERE created_by='demo_seed'"))
    ok = 0
    for cid in cit_ids:
        age_s    = round(random.uniform(0, 30), 1)
        social_s = round(random.uniform(0, 25), 1)
        health_s = round(random.uniform(0, 30), 1)
        env_s    = round(random.uniform(0, 15), 1)
        total    = round(age_s + social_s + health_s + env_s, 1)
        cat = ("critical" if total >= 65 else
               "high"     if total >= 45 else
               "moderate" if total >= 25 else "low")
        try:
            await session.execute(text("""
                INSERT INTO cvi_scores
                    (id, citizen_id, score, category,
                     age_score, social_score, health_score, environment_score,
                     last_calculated, created_at, updated_at, created_by, updated_by)
                VALUES
                    (gen_random_uuid(), :cid, :score, :cat,
                     :age, :soc, :hlt, :env,
                     :today, NOW(), NOW(), 'demo_seed', 'demo_seed')
                ON CONFLICT (citizen_id) DO UPDATE SET
                    score=EXCLUDED.score, category=EXCLUDED.category,
                    age_score=EXCLUDED.age_score, social_score=EXCLUDED.social_score,
                    health_score=EXCLUDED.health_score, environment_score=EXCLUDED.environment_score,
                    last_calculated=EXCLUDED.last_calculated, updated_at=NOW()
            """), {"cid": cid, "score": total, "cat": cat,
                   "age": age_s, "soc": social_s, "hlt": health_s, "env": env_s,
                   "today": str(TODAY)})
            ok += 1
        except Exception as e:
            if ok == 0: print(f"  [WARN] {e}")
    await session.commit()
    print(f"  [OK] {ok} CVI scores seeded")


async def seed_projects(session):
    """Seed community projects."""
    print("\n[2/4] Community Projects...")
    projects = [
        ("CP-2569-001","ชมรมผู้สูงอายุสุขภาพดี สันทรายหลวง","elderly_club","active",
         "2026-01-15","2026-12-31",50000,42000,120,"นายสมชาย ใจดี","สันทราย",
         "โครงการส่งเสริมสุขภาพผู้สูงอายุ ออกกำลังกายทุกวันอังคาร-พฤหัส จัดกิจกรรมนันทนาการ และตรวจสุขภาพรายไตรมาส"),
        ("CP-2569-002","โปรแกรมออกกำลังกายผู้ป่วยโรคเรื้อรัง","exercise_program","active",
         "2026-02-01","2026-11-30",35000,28000,85,"นางสาวมาลี สุขใจ","เมืองเชียงใหม่",
         "ออกกำลังกายแบบ Low Impact สำหรับผู้ป่วยความดันโลหิตสูงและเบาหวาน ทุกวันจันทร์-ศุกร์ เช้า 07.00-08.00 น."),
        ("CP-2569-003","ปรับปรุงบ้านผู้สูงอายุและผู้พิการ","home_modification","completed",
         "2025-10-01","2026-03-31",80000,76500,18,"นายประสิทธิ์ แก้วมงคล","หางดง",
         "ปรับปรุงห้องน้ำ ติดราวจับ ทางลาด และพื้นกันลื่นสำหรับผู้สูงอายุและผู้พิการ 18 หลังในเขตรับผิดชอบ"),
        ("CP-2569-004","สำรวจสุขภาพชุมชนประจำปี 2569","community_survey","completed",
         "2026-01-05","2026-02-28",25000,23800,2797,"นางวราภรณ์ ทองคำ","สันทราย",
         "สำรวจข้อมูลสุขภาพประชาชนทั้งหมดในเขตรับผิดชอบ ครอบคลุมโรคเรื้อรัง การเยี่ยมบ้าน และความต้องการด้านสังคม"),
        ("CP-2569-005","กิจกรรมสุขภาพจิตผู้สูงอายุ ลดภาวะโดดเดี่ยว","health_activity","active",
         "2026-03-01","2026-08-31",20000,12000,65,"นางสาวอรุณี ดีมาก","เมืองเชียงใหม่",
         "จัดกิจกรรมกลุ่มสำหรับผู้สูงอายุที่อยู่คนเดียว หัตถกรรม ดนตรี และการเล่าเรื่อง ทุกวันพุธบ่าย"),
        ("CP-2569-006","อบรม อสม. เรื่องการดูแลผู้สูงอายุระยะยาว","health_activity","completed",
         "2026-01-20","2026-01-22",15000,14200,30,"นายวิชัย มั่นใจ","สันทราย",
         "อบรมเชิงปฏิบัติการ 3 วัน เรื่องการดูแลผู้สูงอายุ การทำแผล การป้องกันการหกล้ม และการสื่อสารกับผู้ป่วยสมองเสื่อม"),
        ("CP-2569-007","โครงการส่งยาถึงบ้านผู้สูงอายุติดเตียง","other","active",
         "2026-04-01","2026-12-31",45000,18000,42,"นางพิมพ์ใจ รักดี","หางดง",
         "อสม. รับยาจากโรงพยาบาลและส่งให้ผู้สูงอายุติดเตียงที่ไม่สามารถไปรับยาเองได้ ทุก 30 วัน"),
        ("CP-2569-008","สวนผักชุมชน ลดค่าครองชีพผู้สูงอายุ","other","planning",
         "2026-07-01","2026-12-31",30000,0,80,"นายสุรชัย ใจเย็น","ดอยสะเก็ด",
         "จัดสรรพื้นที่ปลูกผักปลอดสารพิษสำหรับผู้สูงอายุ สร้างรายได้เสริมและกิจกรรมทางสังคม"),
    ]

    await session.execute(text(
        "UPDATE community_projects SET is_deleted=true WHERE project_code LIKE 'CP-2569-%'"
    ))

    ok = 0
    for p in projects:
        (code, name, ptype, status, start, end, budget, actual, participants,
         owner, district, desc) = p
        try:
            await session.execute(text("""
                INSERT INTO community_projects
                    (id, project_code, project_name, project_type, status,
                     start_date, end_date, budget, actual_cost, participant_count,
                     owner, district, description, is_deleted,
                     created_at, updated_at, created_by, updated_by)
                VALUES
                    (gen_random_uuid(), :code, :name, :type, :status,
                     :start, :end, :budget, :actual, :parts,
                     :owner, :dist, :desc, false,
                     NOW(), NOW(), 'demo_seed', 'demo_seed')
                ON CONFLICT (project_code) DO UPDATE SET
                    project_name=EXCLUDED.project_name, status=EXCLUDED.status,
                    actual_cost=EXCLUDED.actual_cost, participant_count=EXCLUDED.participant_count,
                    is_deleted=false, updated_at=NOW()
            """), {"code": code, "name": name, "type": ptype, "status": status,
                   "start": start, "end": end, "budget": budget, "actual": actual,
                   "parts": participants, "owner": owner, "dist": district, "desc": desc})
            ok += 1
        except Exception as e:
            print(f"  [WARN] {code}: {e}")
    await session.commit()
    print(f"  [OK] {ok} community projects seeded")


async def seed_campaigns(session):
    """Seed health campaigns."""
    print("\n[3/4] Health Campaigns...")
    campaigns = [
        ("CAMP-2569-001","คัดกรองมะเร็งปากมดลูกและมะเร็งเต้านม","health_screening","women",
         "active","2026-04-01","2026-06-30",40000,350,312,"ศูนย์สุขภาพชุมชนช้างเผือก","เมืองเชียงใหม่",
         "โรงพยาบาลนครพิงค์ ร่วมกับ อสม.",
         "คัดกรองมะเร็งปากมดลูกโดยวิธี Pap Smear และตรวจเต้านมด้วยตนเอง สำหรับหญิงอายุ 30-60 ปี"),
        ("CAMP-2569-002","ฉีดวัคซีนไข้หวัดใหญ่กลุ่มเสี่ยง 2569","vaccination","elderly",
         "completed","2026-03-01","2026-03-31",60000,500,487,"รพ.สต.บ้านสันทรายหลวง","สันทราย",
         "สำนักงานสาธารณสุขจังหวัดเชียงใหม่",
         "ฉีดวัคซีนไข้หวัดใหญ่ฟรีสำหรับผู้สูงอายุ 65 ปีขึ้นไป ผู้ป่วยโรคเรื้อรัง และหญิงตั้งครรภ์"),
        ("CAMP-2569-003","ให้ความรู้โรคเบาหวานและความดันโลหิตสูง","health_education","all",
         "active","2026-05-01","2026-07-31",25000,200,0,"ศูนย์บริการสาธารณสุข 1 (หายยา)","เมืองเชียงใหม่",
         "เทศบาลนครเชียงใหม่",
         "อบรมให้ความรู้เรื่องการควบคุมอาหาร การออกกำลังกาย และการรับประทานยาสำหรับผู้ป่วยเรื้อรัง"),
        ("CAMP-2569-004","ตรวจคัดกรองสุขภาพผู้สูงอายุประจำปี","health_screening","elderly",
         "active","2026-05-15","2026-08-15",55000,600,234,"โรงพยาบาลสันทราย","สันทราย",
         "โรงพยาบาลสันทราย ร่วมกับ อสม.สันทราย",
         "ตรวจสุขภาพครบชุดสำหรับผู้สูงอายุ 60 ปีขึ้นไป ได้แก่ เลือด ปัสสาวะ ความดัน สายตา และการได้ยิน"),
        ("CAMP-2569-005","รณรงค์หยุดสูบบุหรี่วันงดสูบบุหรี่โลก","disease_prevention","all",
         "completed","2026-05-31","2026-05-31",10000,300,289,"ทุก รพ.สต. ในอำเภอสันทราย","สันทราย",
         "สาธารณสุขอำเภอสันทราย",
         "จัดกิจกรรมวันงดสูบบุหรี่โลก แจกสื่อรณรงค์ มอบรางวัลผู้เลิกสูบบุหรี่ และให้คำปรึกษาการเลิกบุหรี่"),
        ("CAMP-2569-006","ดูแลสุขภาพแม่และเด็ก 0-5 ปี","maternal_health","pregnant",
         "active","2026-01-01","2026-12-31",70000,150,143,"โรงพยาบาลนครพิงค์","เมืองเชียงใหม่",
         "กองทุนหลักประกันสุขภาพ",
         "ติดตามพัฒนาการเด็ก ตรวจสุขภาพแม่ก่อนและหลังคลอด แจกนมผงและอาหารเสริม"),
        ("CAMP-2569-007","ทันตสุขภาพเด็กนักเรียน ฟันดีสุขภาพดี","dental_health","children",
         "active","2026-05-01","2026-09-30",30000,800,0,"โรงเรียนในเขตสันทราย 5 แห่ง","สันทราย",
         "โรงพยาบาลสันทราย ร่วมกับ สปสช.",
         "ตรวจฟัน เคลือบฟลูออไรด์ และเคลือบหลุมร่องฟันสำหรับเด็กนักเรียน ป.1-ป.3"),
        ("CAMP-2569-008","ส่งเสริมสุขภาพจิตผู้ดูแลผู้สูงอายุ","mental_health","all",
         "planning","2026-07-01","2026-09-30",20000,80,0,"ศูนย์สุขภาพชุมชนช้างเผือก","เมืองเชียงใหม่",
         "มูลนิธิสุขภาพไทย",
         "กลุ่มบำบัดและสนับสนุนสำหรับผู้ดูแลผู้สูงอายุ เพื่อป้องกันภาวะหมดไฟ ทุก 2 สัปดาห์"),
        ("CAMP-2569-009","โภชนาการดีสำหรับผู้สูงอายุ ลดทุพโภชนาการ","nutrition","elderly",
         "active","2026-04-15","2026-10-15",35000,200,167,"รพ.สต.วัดเกต","เมืองเชียงใหม่",
         "โรงพยาบาลมหาราชนครเชียงใหม่",
         "ประเมินภาวะโภชนาการ แจกอาหารเสริม และสอนทำอาหารที่เหมาะสมกับผู้สูงอายุที่มีฟันน้อย"),
        ("CAMP-2569-010","ออกกำลังกายผู้สูงอายุ 100 วัน 100 คน","exercise","elderly",
         "active","2026-04-01","2026-07-09",15000,100,78,"สวนสาธารณะหนองบวกหาด","เมืองเชียงใหม่",
         "เทศบาลนครเชียงใหม่",
         "ออกกำลังกายรวมกลุ่ม 100 วันติดต่อกัน วัดและบันทึกผลสุขภาพก่อน-หลัง มอบรางวัลผู้เข้าร่วมครบ 100 วัน"),
    ]

    await session.execute(text(
        "UPDATE health_campaigns SET is_deleted=true WHERE campaign_code LIKE 'CAMP-2569-%'"
    ))

    ok = 0
    for c in campaigns:
        (code, name, ctype, tgroup, status, start, end, budget, target, actual,
         venue, district, organizer, desc) = c
        try:
            await session.execute(text("""
                INSERT INTO health_campaigns
                    (id, campaign_code, campaign_name, campaign_type, target_group,
                     status, start_date, end_date, budget, target_count, actual_count,
                     venue, district, organizer, description, is_deleted,
                     created_at, updated_at, created_by, updated_by)
                VALUES
                    (gen_random_uuid(), :code, :name, :type, :tgroup,
                     :status, :start, :end, :budget, :target, :actual,
                     :venue, :dist, :org, :desc, false,
                     NOW(), NOW(), 'demo_seed', 'demo_seed')
                ON CONFLICT (campaign_code) DO UPDATE SET
                    campaign_name=EXCLUDED.campaign_name, status=EXCLUDED.status,
                    actual_count=EXCLUDED.actual_count, is_deleted=false, updated_at=NOW()
            """), {"code": code, "name": name, "type": ctype, "tgroup": tgroup,
                   "status": status, "start": start, "end": end, "budget": budget,
                   "target": target, "actual": actual, "venue": venue,
                   "dist": district, "org": organizer, "desc": desc})
            ok += 1
        except Exception as e:
            print(f"  [WARN] {code}: {e}")
    await session.commit()
    print(f"  [OK] {ok} campaigns seeded")


async def seed_risk_scores(session, cit_ids):
    """Seed risk stratification scores."""
    print("\n[4/4] Risk Scores...")
    await session.execute(text("DELETE FROM risk_scores WHERE created_by='demo_seed'"))

    ok = 0
    for cid in cit_ids:
        score = round(random.uniform(5, 95), 1)
        level = ("critical" if score >= 75 else
                 "high"     if score >= 50 else
                 "moderate" if score >= 25 else "low")
        factors_list = []
        if score >= 75: factors_list.extend(["is_bedridden","is_elderly","no_caregiver"])
        elif score >= 50: factors_list.extend(["is_elderly","chronic_disease"])
        elif score >= 25: factors_list.extend(["is_elderly"])
        factors = ",".join(factors_list) if factors_list else "none"

        try:
            await session.execute(text("""
                INSERT INTO risk_scores
                    (id, citizen_id, score, risk_level, calculation_date, factors,
                     created_at, updated_at, created_by, updated_by)
                VALUES
                    (gen_random_uuid(), :cid, :score, :level, :today, :factors,
                     NOW(), NOW(), 'demo_seed', 'demo_seed')
                ON CONFLICT (citizen_id) DO UPDATE SET
                    score=EXCLUDED.score, risk_level=EXCLUDED.risk_level,
                    calculation_date=EXCLUDED.calculation_date, updated_at=NOW()
            """), {"cid": cid, "score": score, "level": level,
                   "today": str(TODAY), "factors": factors})
            ok += 1
        except Exception as e:
            if ok == 0: print(f"  [WARN] {e}")
    await session.commit()
    print(f"  [OK] {ok} risk scores seeded")


async def main():
    from app.core.database import AsyncSessionLocal

    print("=" * 58)
    print("[Demo Seeder] CVI / Projects / Campaigns / Risk Scores")
    print("=" * 58)

    async with AsyncSessionLocal() as session:
        cit_ids = [str(r[0]) for r in
                   (await session.execute(text("SELECT id FROM citizens LIMIT 500"))).fetchall()]
        print(f"  Citizens found: {len(cit_ids)}")

        await seed_cvi(session, cit_ids)
        await seed_projects(session)
        await seed_campaigns(session)
        await seed_risk_scores(session, cit_ids)

    print("\n" + "=" * 58)
    print("[DONE] All demo data seeded successfully!")
    print("  Restart Streamlit to see updated data.")
    print("=" * 58)


if __name__ == "__main__":
    asyncio.run(main())
