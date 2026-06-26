# -*- coding: utf-8 -*-
"""
Seed Operations + Health Monitoring demo data.
Targets citizens, volunteers, households already in DB.
Safe to run multiple times — skips existing data.

Run: py -3.12 scripts/seed_operations_health.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import random
from datetime import date, datetime, timedelta, UTC

from faker import Faker
from sqlalchemy import select, func, text

from app.core.database import AsyncSessionLocal

fake = Faker("th_TH")

# ── Thai-realistic data pools ──────────────────────────────────────────────────
TASK_TITLES = [
    "เยี่ยมบ้านผู้สูงอายุกลุ่มเสี่ยง",
    "ติดตามผู้ป่วยเบาหวานรายใหม่",
    "ส่งเอกสารสวัสดิการผู้พิการ",
    "ประเมินสุขภาพผู้สูงอายุประจำปี",
    "ประชุม อสม. ประจำเดือน",
    "จัดกิจกรรมออกกำลังกายผู้สูงอายุ",
    "สำรวจครัวเรือนใหม่ในหมู่บ้าน",
    "ติดตามผู้ป่วยหลังส่งต่อโรงพยาบาล",
    "แจกยาผู้ป่วยความดันโลหิตสูง",
    "ลงทะเบียนประชาชนใหม่",
    "ตรวจสอบสภาพบ้านผู้สูงอายุ",
    "ประสานงานส่งต่อผู้ป่วยฉุกเฉิน",
    "อบรมความรู้สุขภาพชุมชน",
    "รณรงค์ฉีดวัคซีนไข้หวัดใหญ่",
    "เยี่ยมมารดาหลังคลอด",
]
TASK_TYPES = [
    "home_visit", "referral_followup", "citizen_followup",
    "community_survey", "health_education", "medication_delivery",
]
FOLLOWUP_RULES = [
    "No home visit in 90 days",
    "Referral unresolved 30+ days",
    "Volunteer inactive 60 days",
    "High CVI score without recent contact",
    "Post-referral follow-up required",
    "Bedridden citizen monthly check",
]
VISIT_NOTES = [
    "ผู้ป่วยมีสุขภาพแข็งแรง ไม่มีอาการผิดปกติ รับประทานยาสม่ำเสมอ",
    "แนะนำให้ดูแลสุขภาพและออกกำลังกายสม่ำเสมอ ลดการรับประทานอาหารหวาน",
    "ติดตามการรับประทานยาอย่างต่อเนื่อง พบว่าลืมกินยาบางมื้อ",
    "ผู้ป่วยมีอาการดีขึ้นหลังจากได้รับคำแนะนำในการดูแลตนเอง",
    "ตรวจพบความเสี่ยงด้านสุขภาพ แนะนำให้พบแพทย์ภายใน 2 สัปดาห์",
    "ครอบครัวให้ความร่วมมือดี มีผู้ดูแลเพียงพอ บ้านมีความปลอดภัย",
    "ผู้ป่วยติดบ้าน ไม่สามารถเดินทางไปโรงพยาบาลได้ด้วยตนเอง",
    "ตรวจวัดความดันโลหิต 130/85 mmHg อยู่ในเกณฑ์ที่ควบคุมได้",
    "น้ำหนักลดลง 2 กิโลกรัมในเดือนที่ผ่านมา แนะนำโภชนาการที่เหมาะสม",
    "ผู้ป่วยมีอาการซึมเศร้า แนะนำให้ปรึกษาแพทย์และเข้าร่วมกิจกรรมชุมชน",
]
ANN_DATA = [
    ("รณรงค์ตรวจสุขภาพประจำปี 2026", "ขอเชิญประชาชนทุกท่านเข้ารับการตรวจสุขภาพประจำปีที่สถานพยาบาลใกล้บ้าน ฟรีทุกสิทธิ์การรักษา", "health_campaign"),
    ("ประชุม อสม. ประจำเดือนมิถุนายน", "ขอเชิญ อสม. ทุกท่านเข้าร่วมประชุมประจำเดือนมิถุนายน 2026 ณ ศาลาประชาคม หมู่ 3", "volunteer_notice"),
    ("แจ้งเตือนฤดูฝน: ระวังโรคไข้เลือดออก", "ช่วงฤดูฝนขอให้ประชาชนทำลายแหล่งเพาะพันธุ์ยุง และป้องกันการถูกยุงกัด", "community_news"),
    ("โครงการวัคซีนไข้หวัดใหญ่ผู้สูงอายุ", "ผู้สูงอายุ 60 ปีขึ้นไปสามารถรับวัคซีนไข้หวัดใหญ่ได้ฟรี ที่ รพ.สต. ทุกแห่ง", "health_campaign"),
    ("ประกาศเตือนภัยสุขภาพ", "พบผู้ป่วยโรคมือเท้าปาก (Hand, Foot and Mouth Disease) ในพื้นที่ ขอให้ผู้ปกครองดูแลบุตรหลานอย่างใกล้ชิด", "emergency_alert"),
    ("กิจกรรมออกกำลังกายผู้สูงอายุ", "เชิญผู้สูงอายุร่วมกิจกรรมออกกำลังกาย ทุกเช้าวันจันทร์-ศุกร์ เวลา 07.00-08.00 น. ที่สวนสาธารณะ", "community_news"),
    ("แจ้งผลการตรวจสุขภาพหมู่บ้าน", "ผลการตรวจสุขภาพประจำปีพบว่า 35% ของประชาชนมีความดันโลหิตสูง โปรดติดตามการรักษาอย่างต่อเนื่อง", "health_campaign"),
]
PROJ_DATA = [
    ("PROJ0001", "ชมรมผู้สูงอายุสุขใจ", "elderly_club", "active", 50000, "นายสมชาย ใจดี"),
    ("PROJ0002", "โครงการออกกำลังกายเพื่อสุขภาพ", "exercise_program", "active", 30000, "นางสาวมาลี สวรรค์"),
    ("PROJ0003", "ปรับปรุงบ้านผู้พิการและผู้สูงอายุ", "home_modification", "completed", 120000, "นายวิชัย ประสาน"),
    ("PROJ0004", "สำรวจสุขภาพชุมชนประจำปี", "community_survey", "planning", 20000, "นางสาวรัตนา ทองดี"),
    ("PROJ0005", "อบรม อสม. อาสาฉุกเฉิน", "health_activity", "active", 45000, "นายพิชัย มั่นคง"),
    ("PROJ0006", "สวนผักปลอดสารพิษชุมชน", "other", "planning", 35000, "นางสาวสมศรี ธรรมดี"),
    ("PROJ0007", "โครงการอาหารปลอดภัยสำหรับผู้สูงอายุ", "health_activity", "completed", 28000, "นายธนากร ศรีสวัสดิ์"),
    ("PROJ0008", "คลินิกเคลื่อนที่ดูแลผู้สูงอายุ", "health_activity", "active", 150000, "นายแพทย์สมศักดิ์"),
]

def _rand_date(days_back: int = 365) -> date:
    return date.today() - timedelta(days=random.randint(0, days_back))

def _rand_date_str(days_back: int = 365) -> str:
    return str(_rand_date(days_back))


# ── OPERATIONS SEEDS ──────────────────────────────────────────────────────────

async def seed_tasks(session, cit_ids: list, vol_ids: list) -> int:
    from app.modules.tasks.model import Task
    cnt = (await session.execute(
        select(func.count()).select_from(Task).where(Task.is_deleted == False)
    )).scalar() or 0
    if cnt >= 50:
        print(f"  ℹ️  Tasks already seeded ({cnt}), skipping")
        return 0

    priorities = ["low", "medium", "high", "critical"]
    pw = [20, 45, 25, 10]
    statuses = ["new", "assigned", "in_progress", "completed", "overdue"]
    sw = [15, 20, 25, 30, 10]
    added = 0
    for i in range(60):
        due = date.today() + timedelta(days=random.randint(-15, 45))
        session.add(Task(
            task_code=f"TASK{cnt+i+1:05d}",
            title=random.choice(TASK_TITLES),
            task_type=random.choice(TASK_TYPES),
            priority=random.choices(priorities, weights=pw)[0],
            status=random.choices(statuses, weights=sw)[0],
            due_date=str(due),
            citizen_id=random.choice(cit_ids) if cit_ids and random.random() < 0.6 else None,
            volunteer_id=random.choice(vol_ids) if vol_ids and random.random() < 0.5 else None,
            description=f"งานมอบหมายโดยระบบ อ้างอิง TASK{cnt+i+1:05d}",
            created_by="demo", updated_by="demo",
        ))
        added += 1
    await session.commit()
    print(f"  ✅ Tasks: {added}")
    return added


async def seed_followups(session, cit_ids: list, vol_ids: list) -> int:
    from app.modules.followups.model import Followup
    cnt = (await session.execute(
        select(func.count()).select_from(Followup)
    )).scalar() or 0
    if cnt >= 30:
        print(f"  ℹ️  Follow-ups already seeded ({cnt}), skipping")
        return 0

    types = ["citizen_not_visited", "referral_unresolved", "volunteer_inactive"]
    statuses = ["pending", "in_progress", "completed"]
    sw = [40, 35, 25]
    added = 0
    for i in range(50):
        session.add(Followup(
            citizen_id=random.choice(cit_ids) if cit_ids else None,
            followup_type=random.choice(types),
            followup_date=_rand_date_str(60),
            status=random.choices(statuses, weights=sw)[0],
            rule_triggered=random.choice(FOLLOWUP_RULES),
            notes=f"ติดตามอัตโนมัติ รอบที่ {random.randint(1,3)}",
            created_by="demo", updated_by="demo",
        ))
        added += 1
    await session.commit()
    print(f"  ✅ Follow-Ups: {added}")
    return added


async def seed_announcements(session) -> int:
    from app.modules.announcements.service import Announcement
    cnt = (await session.execute(
        select(func.count()).select_from(Announcement)
    )).scalar() or 0
    if cnt >= 5:
        print(f"  ℹ️  Announcements already seeded ({cnt}), skipping")
        return 0

    added = 0
    for title, content, atype in ANN_DATA:
        session.add(Announcement(
            title=title, content=content,
            announcement_type=atype,
            start_date=_rand_date_str(30),
            end_date=str(date.today() + timedelta(days=random.randint(7, 90))),
            target_province="เชียงใหม่",
            target_district=random.choice(["เมือง", "สันทราย", "หางดง", ""]),
            is_active=True,
            created_by="demo", updated_by="demo",
        ))
        added += 1
    await session.commit()
    print(f"  ✅ Announcements: {added}")
    return added


async def seed_community_projects(session) -> int:
    from app.modules.community_projects.service import CommunityProject
    cnt = (await session.execute(
        select(func.count()).select_from(CommunityProject)
    )).scalar() or 0
    if cnt >= 5:
        print(f"  ℹ️  Projects already seeded ({cnt}), skipping")
        return 0

    added = 0
    for code, name, ptype, status, budget, owner in PROJ_DATA:
        session.add(CommunityProject(
            project_code=code, project_name=name,
            project_type=ptype, status=status, budget=budget,
            start_date=_rand_date_str(180),
            end_date=str(date.today() + timedelta(days=random.randint(30, 365))),
            owner=owner, province="เชียงใหม่",
            district=random.choice(["เมือง", "สันทราย", "หางดง"]),
            description=f"โครงการ{name} เพื่อพัฒนาคุณภาพชีวิตประชาชนในพื้นที่",
            created_by="demo", updated_by="demo",
        ))
        added += 1
    await session.commit()
    print(f"  ✅ Community Projects: {added}")
    return added


async def seed_notifications(session) -> int:
    from app.modules.notifications.service import Notification
    from app.modules.users.model import User
    cnt = (await session.execute(
        select(func.count()).select_from(Notification)
    )).scalar() or 0
    if cnt >= 20:
        print(f"  ℹ️  Notifications already seeded ({cnt}), skipping")
        return 0

    users = (await session.execute(select(User).limit(5))).scalars().all()
    notif_pool = [
        ("new_task", "มีงานใหม่ที่ต้องดำเนินการ", "กรุณาตรวจสอบงานเยี่ยมบ้านที่ได้รับมอบหมาย"),
        ("overdue_task", "งานเกินกำหนด", "มีงาน 5 รายการที่เกินกำหนดส่ง กรุณาดำเนินการ"),
        ("followup_reminder", "แจ้งเตือนการติดตาม", "มีการติดตามที่รอดำเนินการ 12 รายการ"),
        ("referral_reminder", "การส่งต่อค้างนาน", "การส่งต่อ 3 รายการยังไม่ได้รับการดำเนินการ"),
        ("new_announcement", "ประกาศใหม่", "รณรงค์ตรวจสุขภาพประจำปี 2026 เริ่มแล้ว"),
        ("alert_critical", "การแจ้งเตือนวิกฤต", "พบผู้สูงอายุติดบ้านที่ไม่มีผู้ดูแล 3 ราย"),
        ("system_info", "อัพเดทระบบ", "ระบบได้รับการอัพเดทเป็นเวอร์ชัน 2.54.2C"),
    ]
    added = 0
    for user in users:
        for ntype, title, msg in random.sample(notif_pool, min(5, len(notif_pool))):
            session.add(Notification(
                user_id=user.id, type=ntype,
                title=title, message=msg,
                is_read=random.random() < 0.4,
                created_by="demo", updated_by="demo",
            ))
            added += 1
    await session.commit()
    print(f"  ✅ Notifications: {added}")
    return added


# ── HEALTH MONITORING SEEDS ───────────────────────────────────────────────────

async def seed_health_profiles(session, cit_ids: list) -> int:
    from app.modules.health_profiles.model import HealthProfile
    cnt = (await session.execute(
        select(func.count()).select_from(HealthProfile)
    )).scalar() or 0
    if cnt >= len(cit_ids) * 0.4:
        print(f"  ℹ️  Health Profiles already seeded ({cnt}), skipping")
        return 0

    # Seed for citizens that don't have profiles yet
    existing_ids = set(
        str(r[0]) for r in
        (await session.execute(select(HealthProfile.citizen_id))).all()
    )
    candidates = [c for c in cit_ids if str(c) not in existing_ids]
    sample = random.sample(candidates, min(200, len(candidates)))

    added = 0
    for cid in sample:
        n_chronic = random.choices([0, 1, 2, 3], weights=[40, 35, 18, 7])[0]
        chronic_flags = random.sample([
            "has_diabetes", "has_hypertension", "has_dyslipidemia",
            "has_heart_disease", "has_stroke", "has_cancer",
            "has_kidney_disease", "has_lung_disease"
        ], n_chronic)

        is_elderly_profile = random.random() < 0.35
        is_homebound = is_elderly_profile and random.random() < 0.2
        lives_alone = is_elderly_profile and random.random() < 0.25

        profile = HealthProfile(
            citizen_id=cid,
            blood_type=random.choice(["A+","B+","O+","AB+","A-","B-","O-",None,None]),
            primary_caregiver=fake.name() if not lives_alone and random.random() < 0.5 else None,
            caregiver_phone=fake.phone_number()[:15] if random.random() < 0.4 else None,
            allergies=random.choice([
                None, None, None, "ยาเพนนิซิลิน", "อาหารทะเล", "ฝุ่น"
            ]),
            medication_notes=random.choice([
                None, None, "รับประทานยาความดัน Amlodipine 5mg OD",
                "ยาเบาหวาน Metformin 500mg BID", "ยาลดไขมัน Simvastatin 20mg HS"
            ]) if n_chronic > 0 else None,
            has_diabetes="has_diabetes" in chronic_flags,
            has_hypertension="has_hypertension" in chronic_flags,
            has_dyslipidemia="has_dyslipidemia" in chronic_flags,
            has_heart_disease="has_heart_disease" in chronic_flags,
            has_stroke="has_stroke" in chronic_flags,
            has_cancer="has_cancer" in chronic_flags,
            has_kidney_disease="has_kidney_disease" in chronic_flags,
            has_lung_disease="has_lung_disease" in chronic_flags,
            other_conditions=None,
            walks_independently=not is_homebound,
            uses_cane=is_elderly_profile and random.random() < 0.15,
            uses_walker=is_elderly_profile and random.random() < 0.08,
            uses_wheelchair=is_homebound and random.random() < 0.3,
            is_homebound=is_homebound,
            is_bedridden_profile=is_homebound and random.random() < 0.2,
            lives_alone_profile=lives_alone,
            has_caregiver=not lives_alone and random.random() < 0.5,
            has_income_problems=random.random() < 0.2,
            has_food_insecurity=random.random() < 0.1,
            has_social_isolation=lives_alone and random.random() < 0.4,
            has_healthcare_access_issues=random.random() < 0.15,
            unsafe_bathroom=is_elderly_profile and random.random() < 0.2,
            slippery_floor=is_elderly_profile and random.random() < 0.25,
            poor_lighting=random.random() < 0.1,
            unsafe_stairs=is_elderly_profile and random.random() < 0.15,
            electrical_hazards=random.random() < 0.05,
            structural_damage=random.random() < 0.05,
            needs_home_visit=True if is_homebound else random.random() < 0.3,
            needs_transportation=is_homebound and random.random() < 0.6,
            needs_welfare_assistance=random.random() < 0.2,
            needs_home_modification=is_elderly_profile and random.random() < 0.25,
            needs_equipment_support=is_homebound and random.random() < 0.4,
            needs_social_support=lives_alone and random.random() < 0.5,
            created_by="demo", updated_by="demo",
        )
        session.add(profile)
        added += 1
        if added % 50 == 0:
            await session.flush()

    await session.commit()
    print(f"  ✅ Health Profiles: {added}")
    return added


async def seed_health_assessments(session, cit_ids: list, vol_ids: list) -> int:
    from app.modules.health_assessments.model import HealthAssessment
    from app.modules.health_assessments.service import calculate_bmi

    cnt = (await session.execute(
        select(func.count()).select_from(HealthAssessment)
        .where(HealthAssessment.is_deleted == False)
    )).scalar() or 0
    if cnt >= 200:
        print(f"  ℹ️  Assessments already seeded ({cnt}), skipping")
        return 0

    sample = random.sample(cit_ids, min(150, len(cit_ids)))
    added = 0
    for cid in sample:
        n = random.choices([1, 2, 3, 4], weights=[20, 35, 30, 15])[0]
        base_date = _rand_date(365)
        # Base measurements — realistic Thai adult values
        base_height = random.uniform(152, 175)
        base_weight = random.uniform(48, 90)

        for j in range(n):
            assess_date = base_date + timedelta(days=j * random.randint(30, 90))
            if assess_date > date.today():
                assess_date = date.today()

            # Slight variation each visit
            weight = base_weight + random.uniform(-3, 3)
            height = base_height
            bmi = calculate_bmi(weight, height)

            # Realistic BP values — some hypertensive
            is_hypertensive = random.random() < 0.3
            bp_sys = random.uniform(140, 165) if is_hypertensive else random.uniform(100, 130)
            bp_dia = random.uniform(88, 100) if is_hypertensive else random.uniform(60, 85)

            session.add(HealthAssessment(
                citizen_id=cid,
                volunteer_id=random.choice(vol_ids) if vol_ids else None,
                assessment_date=str(assess_date),
                assessment_type=random.choice([
                    "routine", "follow_up", "annual", "routine", "routine"
                ]),
                height_cm=round(height, 1),
                weight_kg=round(weight, 1),
                bmi=bmi,
                waist_cm=round(random.uniform(68, 105), 1),
                bp_systolic=round(bp_sys, 0),
                bp_diastolic=round(bp_dia, 0),
                pulse_rate=round(random.uniform(62, 98), 0),
                temperature_c=round(random.uniform(36.2, 37.5), 1),
                blood_sugar=round(random.uniform(80, 280), 0) if random.random() < 0.4 else None,
                notes=random.choice([
                    None, None,
                    "ผู้ป่วยให้ความร่วมมือดี",
                    "ควรติดตามน้ำหนักต่อเนื่อง",
                    "แนะนำลดอาหารโซเดียม",
                ]),
                created_by="demo", updated_by="demo",
            ))
            added += 1

        if added % 100 == 0:
            await session.flush()

    await session.commit()
    print(f"  ✅ Health Assessments: {added}")
    return added


async def seed_early_warnings(session, cit_ids: list) -> int:
    from app.modules.early_warning.model import EarlyWarning, CVIScore
    cnt = (await session.execute(
        select(func.count()).select_from(EarlyWarning)
        .where(EarlyWarning.is_deleted == False)
    )).scalar() or 0
    if cnt >= 30:
        print(f"  ℹ️  Early Warnings already seeded ({cnt}), skipping")
        return 0

    alert_templates = [
        ("no_visit", "medium", "ไม่มีการเยี่ยมบ้านในช่วง 90+ วัน",
         "ประชาชนรายนี้ยังไม่ได้รับการเยี่ยมบ้านจาก อสม. นานกว่า 90 วัน"),
        ("homebound_no_caregiver", "high", "ผู้ติดบ้านไม่มีผู้ดูแล",
         "พบผู้ติดบ้านที่ไม่มีผู้ดูแลประจำ ต้องการการเยี่ยมบ้านเร่งด่วน"),
        ("open_referral", "medium", "การส่งต่อค้างนานเกิน 30 วัน",
         "การส่งต่อยังไม่ได้รับการดำเนินการภายใน 30 วัน"),
        ("bedridden_alone", "critical", "ผู้ติดเตียงอยู่คนเดียว",
         "พบผู้ติดเตียงที่อยู่คนเดียวโดยไม่มีผู้ดูแล ต้องการการช่วยเหลือเร่งด่วน"),
        ("no_assessment", "low", "ไม่มีการประเมินสุขภาพ 6 เดือน",
         "ประชาชนรายนี้ไม่ได้รับการประเมินสุขภาพมากกว่า 6 เดือน"),
        ("weight_loss", "medium", "น้ำหนักลดลงผิดปกติ",
         "พบน้ำหนักลดลงมากกว่า 5 กิโลกรัมในช่วง 3 เดือน"),
        ("social_isolation", "high", "ความเสี่ยงการแยกตัวทางสังคม",
         "ประชาชนรายนี้มีความเสี่ยงด้านการแยกตัวทางสังคมสูง"),
    ]
    statuses = ["open", "open", "open", "acknowledged", "resolved"]

    added = 0
    sample = random.sample(cit_ids, min(60, len(cit_ids)))
    for i, cid in enumerate(sample):
        tmpl = alert_templates[i % len(alert_templates)]
        session.add(EarlyWarning(
            citizen_id=cid,
            alert_type=tmpl[0],
            severity=tmpl[1],
            title=tmpl[2],
            detail=tmpl[3],
            status=random.choices(statuses)[0],
            created_by="demo", updated_by="demo",
        ))
        added += 1

    # CVI Scores
    cvi_cnt = (await session.execute(
        select(func.count()).select_from(CVIScore)
    )).scalar() or 0

    cvi_added = 0
    if cvi_cnt < 100:
        existing_cvi = set(
            str(r[0]) for r in
            (await session.execute(select(CVIScore.citizen_id))).all()
        )
        for cid in random.sample(cit_ids, min(200, len(cit_ids))):
            if str(cid) in existing_cvi:
                continue
            score = round(random.uniform(5, 95), 1)
            if score < 25:
                cat = "low"
            elif score < 50:
                cat = "moderate"
            elif score < 75:
                cat = "high"
            else:
                cat = "critical"
            session.add(CVIScore(
                citizen_id=cid,
                score=score, category=cat,
                age_score=round(random.uniform(0, 20), 1),
                social_score=round(random.uniform(0, 30), 1),
                health_score=round(random.uniform(0, 30), 1),
                environment_score=round(random.uniform(0, 20), 1),
                last_calculated=str(date.today()),
                created_by="demo", updated_by="demo",
            ))
            cvi_added += 1

    await session.commit()
    print(f"  ✅ Early Warnings: {added} | CVI Scores: {cvi_added}")
    return added + cvi_added


async def seed_quality_records(session) -> int:
    from app.modules.quality_management.service import (
        QualityIndicator, QualityRecord, DEFAULT_INDICATORS, seed_default_indicators
    )
    cnt = (await session.execute(
        select(func.count()).select_from(QualityRecord)
        .where(QualityRecord.is_deleted == False)
    )).scalar() or 0
    if cnt >= 40:
        print(f"  ℹ️  Quality Records already seeded ({cnt}), skipping")
        return 0

    # Ensure indicators exist
    seed_default_indicators.__globals__["get_sync_db"]  # will raise if not importable
    # Use async approach
    for code, name, cat, target, unit in DEFAULT_INDICATORS:
        existing = (await session.execute(
            select(QualityIndicator).where(QualityIndicator.indicator_code == code)
        )).scalar_one_or_none()
        if not existing:
            session.add(QualityIndicator(
                indicator_code=code, indicator_name=name,
                category=cat, target_value=target, unit=unit,
                created_by="demo", updated_by="demo",
            ))
    await session.flush()

    # Add 6 months of records per indicator
    added = 0
    for code, name, cat, target, unit in DEFAULT_INDICATORS:
        for month in range(1, 7):
            # Realistic trend: starts lower, improves over time
            actual = round(
                target * random.uniform(0.6, 0.7) + (month / 6) * target * random.uniform(0.15, 0.3),
                1
            )
            actual = min(actual, 100.0)
            existing_rec = (await session.execute(
                select(QualityRecord).where(
                    QualityRecord.indicator_id == code,
                    QualityRecord.period_year == 2026,
                    QualityRecord.period_month == month,
                )
            )).scalar_one_or_none()
            if not existing_rec:
                session.add(QualityRecord(
                    indicator_id=code,
                    period_year=2026,
                    period_month=month,
                    actual_value=actual,
                    notes=f"บันทึกผลการดำเนินงานประจำเดือน {month}/2026",
                    created_by="demo", updated_by="demo",
                ))
                added += 1

    await session.commit()
    print(f"  ✅ Quality Records: {added}")
    return added


async def seed_outcomes(session, cit_ids: list) -> int:
    from app.modules.outcomes.service import CaseOutcome
    cnt = (await session.execute(
        select(func.count()).select_from(CaseOutcome)
        .where(CaseOutcome.is_deleted == False)
    )).scalar() or 0
    if cnt >= 30:
        print(f"  ℹ️  Case Outcomes already seeded ({cnt}), skipping")
        return 0

    outcome_templates = [
        ("improved", "BMI 28.5", "BMI 25.2", "closed", "น้ำหนักลดลงหลังปรับพฤติกรรมการบริโภค"),
        ("improved", "BP 160/100", "BP 128/82", "closed", "ควบคุมความดันโลหิตได้ดีขึ้นด้วยยาและการปรับพฤติกรรม"),
        ("stable", "HbA1c 7.8%", "HbA1c 7.5%", "open", "ควบคุมน้ำตาลในเลือดได้ในระดับที่ยอมรับได้"),
        ("deteriorated", "เดินได้ปกติ", "ต้องใช้ไม้เท้า", "open", "ระดับการเคลื่อนไหวลดลง แนะนำกายภาพบำบัด"),
        ("resolved", "ซึมเศร้าเล็กน้อย", "ปกติ", "closed", "อาการดีขึ้นหลังเข้าร่วมกิจกรรมชุมชน"),
        ("ongoing", "น้ำหนักเกิน", "ยังคงเกิน", "open", "อยู่ระหว่างปรับพฤติกรรมการบริโภค"),
        ("improved", "ไม่ออกกำลังกาย", "ออกกำลังกาย 3x/สัปดาห์", "closed", "ปรับพฤติกรรมสุขภาพได้สำเร็จ"),
        ("improved", "สูบบุหรี่", "เลิกสูบบุหรี่", "closed", "เลิกบุหรี่สำเร็จหลังเข้าโปรแกรม"),
    ]

    added = 0
    for i in range(50):
        tmpl = random.choice(outcome_templates)
        session.add(CaseOutcome(
            citizen_id=str(random.choice(cit_ids)) if cit_ids else None,
            case_ref=f"CASE-{i+1:04d}",
            outcome_type=tmpl[0],
            baseline_value=tmpl[1],
            current_value=tmpl[2],
            outcome_status=tmpl[3],
            evaluation_date=_rand_date_str(90),
            notes=tmpl[4],
            created_by="demo", updated_by="demo",
        ))
        added += 1
    await session.commit()
    print(f"  ✅ Case Outcomes: {added}")
    return added


async def seed_risk_scores(session, cit_ids: list) -> int:
    from app.modules.risk_stratification.service import RiskScore
    cnt = (await session.execute(
        select(func.count()).select_from(RiskScore)
        .where(RiskScore.is_deleted == False)
    )).scalar() or 0
    if cnt >= 100:
        print(f"  ℹ️  Risk Scores already seeded ({cnt}), skipping")
        return 0

    existing_ids = set(
        r[0] for r in (await session.execute(select(RiskScore.citizen_id))).all()
    )
    levels = ["low", "moderate", "high", "critical"]
    lw = [35, 35, 20, 10]
    factor_pools = {
        "low": ["Young age", "Healthy lifestyle"],
        "moderate": ["Age 60-69", "One chronic condition"],
        "high": ["Age 70+, Lives alone", "Homebound, Diabetes", "Multiple chronic conditions"],
        "critical": ["Age 80+, Bedridden, No caregiver", "Critical vulnerability, Unsafe housing"],
    }

    added = 0
    for cid in random.sample(cit_ids, min(250, len(cit_ids))):
        if str(cid) in existing_ids:
            continue
        level = random.choices(levels, weights=lw)[0]
        score_ranges = {"low": (5, 24), "moderate": (25, 49), "high": (50, 74), "critical": (75, 100)}
        score = round(random.uniform(*score_ranges[level]), 1)
        session.add(RiskScore(
            citizen_id=str(cid),
            score=score,
            risk_level=level,
            factors=random.choice(factor_pools[level]),
            calculation_date=str(date.today()),
            created_by="demo", updated_by="demo",
        ))
        added += 1
        if added % 50 == 0:
            await session.flush()

    await session.commit()
    print(f"  ✅ Risk Scores: {added}")
    return added


async def seed_scorecards(session) -> int:
    from app.modules.community_scorecards.service import CommunityScorecard, compute_overall_score
    cnt = (await session.execute(
        select(func.count()).select_from(CommunityScorecard)
        .where(CommunityScorecard.is_deleted == False)
    )).scalar() or 0
    if cnt >= 20:
        print(f"  ℹ️  Scorecards already seeded ({cnt}), skipping")
        return 0

    communities = [
        ("ชุมชนดอยสะเก็ด", "สันทราย"), ("ชุมชนสันทราย", "สันทราย"),
        ("ชุมชนหางดง", "หางดง"), ("ชุมชนแม่ริม", "แม่ริม"),
        ("ชุมชนเมืองเชียงใหม่", "เมือง"),
    ]
    added = 0
    for comm_name, district in communities:
        for month in range(1, 7):
            scores = {
                "coverage_rate": round(random.uniform(55, 95), 1),
                "assessment_rate": round(random.uniform(50, 92), 1),
                "home_visit_rate": round(random.uniform(60, 98), 1),
                "referral_completion_rate": round(random.uniform(65, 95), 1),
                "case_closure_rate": round(random.uniform(50, 90), 1),
                "volunteer_activity_rate": round(random.uniform(60, 98), 1),
            }
            sc = CommunityScorecard(
                community_id=comm_name.lower().replace(" ", "_"),
                community_name=comm_name, district=district,
                month=month, year=2026,
                population=random.randint(500, 3000),
                **scores, created_by="demo", updated_by="demo",
            )
            sc.overall_score = compute_overall_score(sc)
            session.add(sc)
            added += 1
    await session.commit()
    print(f"  ✅ Community Scorecards: {added}")
    return added


async def seed_performance_metrics(session) -> int:
    from app.modules.performance_management.service import PerformanceMetric, compute_status
    cnt = (await session.execute(
        select(func.count()).select_from(PerformanceMetric)
        .where(PerformanceMetric.is_deleted == False)
    )).scalar() or 0
    if cnt >= 5:
        print(f"  ℹ️  Performance Metrics already seeded ({cnt}), skipping")
        return 0

    metrics = [
        ("อัตราการเยี่ยมบ้าน", "home_visit_frequency", 85.0, 78.5, "%"),
        ("อัตราการส่งต่อสำเร็จ", "referral_completion", 80.0, 72.0, "%"),
        ("อัตราการประเมินสุขภาพ", "assessment_coverage", 70.0, 68.5, "%"),
        ("กิจกรรมอาสาสมัคร", "volunteer_productivity", 75.0, 82.0, "%"),
        ("อัตราการปิดเคส", "case_closure", 65.0, 58.0, "%"),
        ("ความครอบคลุมสนับสนุนสังคม", "social_support", 60.0, 55.0, "%"),
    ]
    added = 0
    for name, cat, target, current, unit in metrics:
        status = compute_status(current, target)
        session.add(PerformanceMetric(
            metric_name=name, metric_category=cat,
            target=target, current_value=current, unit=unit,
            status=status, period="2026-Q2",
            notes=f"ผลการดำเนินงาน Q2/2026 เทียบกับเป้าหมาย {target}{unit}",
            created_by="demo", updated_by="demo",
        ))
        added += 1
    await session.commit()
    print(f"  ✅ Performance Metrics: {added}")
    return added


# ── Main ──────────────────────────────────────────────────────────────────────

async def main():
    print("=" * 65)
    print("🏥 MKI Platform — Operations & Health Monitoring Demo Data")
    print("=" * 65)

    async with AsyncSessionLocal() as session:
        # Get existing citizens and volunteers
        from app.modules.citizens.model import Citizen
        from app.modules.volunteers.model import Volunteer

        cit_rows = (await session.execute(select(Citizen.id).limit(500))).all()
        cit_ids = [r[0] for r in cit_rows]

        vol_rows = (await session.execute(select(Volunteer.id).limit(100))).all()
        vol_ids = [r[0] for r in vol_rows]

        if not cit_ids:
            print("⚠️  No citizens found. Run demo_data.py first to create base data.")
            return
        print(f"📊 Found {len(cit_ids)} citizens, {len(vol_ids)} volunteers\n")

        # ── OPERATIONS ────────────────────────────────────────────────────────
        print("── OPERATIONS ──────────────────────────────────────────────")
        await seed_tasks(session, cit_ids, vol_ids)
        await seed_followups(session, cit_ids, vol_ids)
        await seed_announcements(session)
        await seed_community_projects(session)
        await seed_notifications(session)

        # ── HEALTH MONITORING ─────────────────────────────────────────────────
        print("\n── HEALTH MONITORING ───────────────────────────────────────")
        await seed_health_profiles(session, cit_ids)
        await seed_health_assessments(session, cit_ids, vol_ids)
        await seed_early_warnings(session, cit_ids)
        await seed_outcomes(session, cit_ids)
        await seed_risk_scores(session, cit_ids)

        # ── QUALITY & PERFORMANCE ─────────────────────────────────────────────
        print("\n── QUALITY & PERFORMANCE ───────────────────────────────────")
        try:
            await seed_quality_records(session)
        except Exception as e:
            print(f"  ⚠️  Quality records: {e}")
        await seed_scorecards(session)
        await seed_performance_metrics(session)

    print("\n" + "=" * 65)
    print("🎉 Operations & Health Monitoring data seeded!")
    print("=" * 65)
    print("\nPages now fully populated:")
    print("  Operations: Tasks, Follow-Ups, Announcements, Projects, Notifications")
    print("  Health:     Health Profiles, Assessments, Early Warning, CVI")
    print("  Quality:    Quality Indicators, Outcomes, Scorecards, Performance")
    print("  Analytics:  Risk Scores, Population Health, Community Health")
    print("\nRun the app and explore all pages:")
    print("  $env:PYTHONPATH='.'; py -3.12 -m streamlit run app/main.py")


if __name__ == "__main__":
    asyncio.run(main())
