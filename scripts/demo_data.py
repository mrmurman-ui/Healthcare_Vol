# -*- coding: utf-8 -*-
import sys, io
# Force UTF-8 output on Windows (cp1252 can't encode Thai/emoji)
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
"""
Demo Data Generator — ข้อมูลเสมือนจริงสำหรับระบบสุขภาพชุมชน MKI
ครอบคลุมทุกโมดูล: ชุมชนเชียงใหม่ / เชียงดาว / ลำพูน

Run: py -3.12 scripts/demo_data.py

Date Format Note:
  All dates stored as ISO (YYYY-MM-DD, ค.ศ./AD).
  App displays as DD/MM/YYYY พ.ศ. (BE = AD + 543) in Thai mode.
  e.g. 2026-06-15 → แสดงเป็น 15/06/2569
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import random
from datetime import date, datetime, timedelta, UTC
from faker import Faker

from app.core.database import AsyncSessionLocal
from app.modules.announcements.service import Announcement
from app.modules.citizens.service import CitizenCreate, CitizenService
from app.modules.community_projects.service import CommunityProject
from app.modules.community_scorecards.service import CommunityScorecard
from app.modules.early_warning.model import CVIScore, EarlyWarning
from app.modules.followups.model import Followup
from app.modules.health_assessments.model import HealthAssessment
from app.modules.health_assessments.service import calculate_bmi
from app.modules.health_profiles.model import HealthProfile
from app.modules.home_visits.service import HomeVisitCreate, HomeVisitService
from app.modules.households.service import HouseholdCreate, HouseholdService
from app.modules.notifications.service import Notification
from app.modules.outcomes.service import CaseOutcome
from app.modules.performance_management.service import PerformanceMetric
from app.modules.quality_management.service import QualityIndicator, QualityRecord, DEFAULT_INDICATORS
from app.modules.referrals.service import ReferralCreate, ReferralService
from app.modules.risk_stratification.service import RiskScore
from app.modules.tasks.model import Task
from app.modules.users.schema import UserCreate
from app.modules.users.service import UserService
from app.modules.volunteers.schema import VolunteerCreate
from app.modules.volunteers.service import VolunteerService
from app.shared.enums import (
    Gender, HousingType, IncomeGroup, ReferralStatus, ReferralTarget,
    UserRole, VisitType, VolunteerStatus,
)

fake = Faker("th_TH")

# ── พื้นที่จริง: เชียงใหม่ และลำพูน ──────────────────────────────────────────
CM_LAT, CM_LON = 18.7883, 98.9853   # ใจกลางเมืองเชียงใหม่

PROVINCES  = ["เชียงใหม่", "เชียงใหม่", "เชียงใหม่", "ลำพูน"]

DISTRICTS  = ["เมืองเชียงใหม่", "สันทราย", "หางดง", "สันกำแพง", "แม่ริม",
              "ดอยสะเก็ด", "สันป่าตอง", "เมืองลำพูน"]

SUBDISTS   = ["ช้างเผือก", "สุเทพ", "หนองหอย", "พระสิงห์", "ศรีภูมิ",
              "ป่าแดด", "หายยา", "วัดเกต", "ท่าศาลา", "สันทราย"]

# ชุมชนที่มีอยู่จริงในเชียงใหม่
COMMUNITIES = [
    "ชุมชนวัดเกต",
    "ชุมชนช้างเผือก",
    "ชุมชนหายยา",
    "ชุมชนสันทรายหลวง",
    "ชุมชนป่าแดด",
    "ชุมชนท่าศาลา",
    "ชุมชนสุเทพ",
    "ชุมชนหนองหอย",
]

OCCUPATIONS = ["เกษตรกร", "ค้าขาย", "รับจ้าง", "ข้าราชการ/เกษียณ",
               "แม่บ้าน", "เกษียณอายุ", "ธุรกิจส่วนตัว", "ประมง"]

# ── ชื่อโรงพยาบาลจริงในเชียงใหม่ ─────────────────────────────────────────────
HOSPITALS = [
    "โรงพยาบาลมหาราชนครเชียงใหม่",
    "โรงพยาบาลนครพิงค์",
    "โรงพยาบาลเชียงใหม่ราม",
    "โรงพยาบาลลานนา",
    "โรงพยาบาลแมคคอร์มิค",
    "โรงพยาบาลเชียงใหม่ใกล้หมอ",
    "โรงพยาบาลสันทราย",
    "โรงพยาบาลหางดง",
    "โรงพยาบาลดอยสะเก็ด",
    "โรงพยาบาลลำพูน",
]

# ── ศูนย์สุขภาพชุมชน / รพ.สต. จริงในเชียงใหม่ ───────────────────────────────
HEALTH_CENTERS = [
    "รพ.สต.บ้านสันทรายหลวง",
    "รพ.สต.บ้านหนองหอย",
    "รพ.สต.วัดเกต",
    "รพ.สต.บ้านป่าแดด",
    "ศูนย์สุขภาพชุมชนช้างเผือก",
    "ศูนย์บริการสาธารณสุข 1 (หายยา)",
    "ศูนย์บริการสาธารณสุข 2 (ท่าวังตาล)",
    "ศูนย์บริการสาธารณสุขเทศบาลนครเชียงใหม่",
    "คลินิกชุมชนอบอุ่น สันทราย",
    "คลินิกชุมชนอบอุ่น หางดง",
]

# ── องค์กรปกครองส่วนท้องถิ่น / ศูนย์อนามัยจริง ─────────────────────────────
MUNICIPALITIES = [
    "เทศบาลนครเชียงใหม่",
    "เทศบาลเมืองแม่เหียะ",
    "เทศบาลตำบลสันทรายหลวง",
    "เทศบาลตำบลหางดง",
    "เทศบาลตำบลสันกำแพง",
    "อบต.ดอนแก้ว",
    "อบต.ท่าวังตาล",
    "ศูนย์อนามัยเขตที่ 1 เชียงใหม่",
    "สำนักงานสาธารณสุขอำเภอเมืองเชียงใหม่",
    "สำนักงานสาธารณสุขอำเภอสันทราย",
]

# ── มูลนิธิ / NGO จริงในไทย ──────────────────────────────────────────────────
NGOS = [
    "มูลนิธิปอเต็กตึ้ง",
    "มูลนิธิกระจกเงา",
    "มูลนิธิสายไหมต้องรอด",
    "มูลนิธิเด็ก",
    "มูลนิธิสุขภาพไทย",
    "มูลนิธิบ้านพระพร",
    "มูลนิธิบูรณะชนบท",
    "มูลนิธิศุภนิมิตแห่งประเทศไทย",
    "สภากาชาดไทย สาขาเชียงใหม่",
    "มูลนิธิรักษ์ไทย",
]

# ── บ้านพักผู้สูงอายุ / ศูนย์ดูแลผู้สูงวัยจริง ──────────────────────────────
ELDERCARE = [
    "บ้านพักผู้สูงอายุบ้านเย็นใจ เชียงใหม่",
    "ศูนย์ดูแลผู้สูงอายุกองทัพธรรม",
    "สถานสงเคราะห์คนชราบ้านธรรมปกรณ์ เชียงใหม่",
    "ศูนย์ดูแลผู้สูงอายุชมรมผู้สูงวัยสันทราย",
    "บ้านพักผู้สูงวัยเมืองเชียงใหม่",
    "ศูนย์ส่งเสริมสุขภาพผู้สูงอายุ อ.หางดง",
]

# ── หมายเหตุการเยี่ยมบ้านที่สมจริง ─────────────────────────────────────────
VISIT_NOTES = [
    "ผู้สูงอายุมีสุขภาพแข็งแรง รับประทานยาตามแพทย์สั่งสม่ำเสมอ",
    "แนะนำให้ออกกำลังกายเบาๆ เช่น เดินเบาะๆ รอบบ้านวันละ 30 นาที",
    "ติดตามการควบคุมอาหาร เน้นลดน้ำตาลและเกลือสำหรับผู้ป่วยเบาหวานและความดัน",
    "อาการดีขึ้นชัดเจนหลังจากปรับยาตามคำแนะนำแพทย์ ครอบครัวให้ความร่วมมือดี",
    "พบความเสี่ยงด้านสุขภาพ แนะนำให้พบแพทย์ที่โรงพยาบาลนครพิงค์ภายใน 2 สัปดาห์",
    "ครอบครัวดูแลใกล้ชิด บุตรสาวอยู่บ้านช่วยดูแลผู้สูงอายุเต็มเวลา",
    "ผู้ป่วยมีแผลกดทับระยะเริ่มต้น ได้แนะนำการพลิกตัวทุก 2 ชั่วโมง",
    "ตรวจวัดความดันโลหิต 130/80 mmHg อยู่ในเกณฑ์ดี",
    "ผู้ป่วยเบาหวานมีระดับน้ำตาลในเลือด 180 mg/dL เตือนเรื่องการควบคุมอาหาร",
    "บ้านมีสภาพแวดล้อมปลอดภัย ไม่พบปัจจัยเสี่ยงการหกล้ม",
    "แนะนำให้เข้าร่วมชมรมผู้สูงอายุที่ศูนย์บริการสาธารณสุขใกล้บ้าน",
    "ผู้ป่วยโดดเดี่ยว ลูกทำงานต่างจังหวัด แนะนำให้ติดต่อสายด่วนผู้สูงอายุ 1479",
]

VISIT_RECOMMENDATIONS = [
    "แนะนำให้พบแพทย์ตามนัดและรับประทานยาสม่ำเสมอ",
    "ควรออกกำลังกายเบาๆ วันละ 30 นาที และควบคุมอาหาร",
    "นัดติดตามการเยี่ยมบ้านครั้งต่อไปในอีก 30 วัน",
    "แนะนำให้ส่งตัวพบแพทย์เฉพาะทางโรคหัวใจ",
    "ประสานงานกับมูลนิธิปอเต็กตึ้งเพื่อขอรับความช่วยเหลือ",
    "ติดตามสุขภาพจิตและจัดหาผู้ดูแลเพิ่มเติม",
]

REFERRAL_REASONS = [
    "อาการความดันโลหิตสูงไม่สามารถควบคุมได้ด้วยยา ส่งตรวจเพิ่มเติม",
    "ผู้ป่วยเบาหวานมีแผลที่เท้าต้องการการรักษาเฉพาะทาง",
    "ผู้สูงอายุมีอาการสมองเสื่อมเพิ่มขึ้น ต้องการการประเมินทางจิตเวช",
    "ผู้ป่วยโรคหัวใจมีอาการเจ็บหน้าอก ต้องการตรวจ EKG ด่วน",
    "ติดตามผลการรักษาหลังออกจากโรงพยาบาล ต้องการการดูแลต่อเนื่อง",
    "ขอรับสวัสดิการเงินอุดหนุนผู้สูงอายุที่มีภาวะพึ่งพิง",
    "ผู้พิการต้องการอุปกรณ์เสริมสุขภาพและรถเข็น",
    "ขอความช่วยเหลือด้านอาหารและปัจจัยยังชีพจากมูลนิธิ",
    "ผู้ป่วยมีภาวะซึมเศร้า ต้องการคำแนะนำจากนักจิตวิทยา",
    "ส่งตรวจสุขภาพประจำปีและรับวัคซีนไข้หวัดใหญ่",
]

TASK_TITLES = [
    "เยี่ยมบ้านผู้สูงอายุกลุ่มเสี่ยงสูง ชุมชนวัดเกต",
    "ติดตามผู้ป่วยเบาหวานที่ขาดยา 3 สัปดาห์",
    "ส่งเอกสารสิทธิ์สวัสดิการผู้สูงอายุ 80 ปีขึ้นไป",
    "ประเมินสุขภาพประจำปีผู้สูงอายุ อสม.หมู่ 5",
    "ประชุมอสม.ประจำเดือนมิถุนายน 2569",
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
]

FOLLOWUP_RULES = [
    "ไม่มีการเยี่ยมบ้านเกิน 90 วัน",
    "การส่งต่อยังไม่ได้รับการดำเนินการ 30+ วัน",
    "ผู้ป่วยขาดยาเกิน 2 สัปดาห์",
    "ผู้สูงอายุติดบ้านไม่มีผู้ดูแล",
    "อสม.ไม่ได้รายงานผลการเยี่ยมบ้าน",
]

ALERT_TITLES = [
    "ผู้สูงอายุไม่ได้รับการเยี่ยมบ้านเกิน 90 วัน",
    "ผู้สูงอายุอยู่คนเดียวไม่มีผู้ดูแล",
    "การส่งต่อไปโรงพยาบาลค้างนานเกิน 30 วัน",
    "ผู้ป่วยติดเตียงต้องการความช่วยเหลือเร่งด่วน",
    "ผู้ป่วยเบาหวานมีน้ำตาลในเลือดสูงผิดปกติ",
    "ผู้พิการขาดอุปกรณ์ช่วยเหลือพื้นฐาน",
]

RISK_FACTORS = [
    "อายุ 75+ ปี อาศัยอยู่คนเดียว ไม่มีผู้ดูแล",
    "ติดบ้าน ไม่มีผู้ดูแล เป็นเบาหวาน+ความดันโลหิตสูง",
    "อายุ 80+ ปี ติดเตียง โรคหัวใจ ไม่มีญาติใกล้ชิด",
    "โดดเดี่ยวทางสังคม มีปัญหาด้านรายได้ ขาดอาหาร",
    "มีโรคเรื้อรังหลายโรค ไม่รับประทานยาตามแพทย์สั่ง",
    "ผู้ดูแลมีภาวะเครียด เสี่ยงต่อการถูกทอดทิ้ง",
    "บ้านมีสภาพแวดล้อมเสี่ยง พื้นลื่น ห้องน้ำไม่ปลอดภัย",
]


def _rand_date(days_back: int = 365) -> date:
    return date.today() - timedelta(days=random.randint(0, days_back))


def _rand_gps() -> tuple[float, float]:
    return (CM_LAT + random.uniform(-0.15, 0.15),
            CM_LON + random.uniform(-0.15, 0.15))


def _rand_referral_target_name(target: ReferralTarget) -> str:
    """Return a realistic Thai name for the referral target type."""
    if target == ReferralTarget.HOSPITAL:
        return random.choice(HOSPITALS)
    elif target == ReferralTarget.HEALTH_CENTER:
        return random.choice(HEALTH_CENTERS)
    elif target == ReferralTarget.MUNICIPALITY:
        return random.choice(MUNICIPALITIES)
    elif target == ReferralTarget.NGO:
        return random.choice(NGOS)
    else:
        return random.choice(HEALTH_CENTERS)


# ── Real volunteer names from Chiang Mai ─────────────────────────────────────
VOLUNTEER_NAMES = [
    "นางสาวสุนีย์ วงศ์คำ", "นายประสิทธิ์ แก้วมณี", "นางรัตนา ใจดี",
    "นายสมบูรณ์ ศรีวิชัย", "นางดวงจันทร์ ปัญญา", "นายวิเชียร คำมูล",
    "นางสาวพิมพ์ใจ ดวงดี", "นายอนันต์ สุขสวาท", "นางอรุณี แสนสุข",
    "นายมานะ ทองดี", "นางสาวกาญจนา รุ่งเรือง", "นายธวัชชัย คำเงิน",
    "นางสาวอำพร ใจงาม", "นายสุพจน์ จันทร์แก้ว", "นางมาลี วงศ์จันทร์",
    "นายสายัณห์ ดาวแสง", "นางสาวอัมพา ชัยวงศ์", "นายปรีชา ขันแก้ว",
    "นางสาวศิริพร มังกร", "นายนิรันดร์ ป้อมคำ", "นางอุไร สุขสวัสดิ์",
    "นายประเสริฐ ชัยภูมิ", "นางสาวณัฐฐา แสงสว่าง", "นายวรพจน์ พรหมสุวรรณ",
    "นางจิตรา คำใจ", "นายสมศักดิ์ วิชัยรัตน์", "นางสาวลัดดา สีดา",
    "นายบุญมี แก้วพิทักษ์", "นางสาวทิพย์วรรณ คำหล้า", "นายอาทิตย์ กาวิละ",
]


async def seed_users(session) -> list:
    """Seed demo users with realistic Thai names."""
    svc = UserService(session)
    users = [
        UserCreate(email="admin",          password="ChangeMe123!", full_name="นายอภิชาต ศิริมงคล",     role=UserRole.SUPER_ADMIN),
        UserCreate(email="province.admin", password="Demo1234!",    full_name="นายสมชาย ตันตราภรณ์",   role=UserRole.PROVINCE_ADMIN,  province="เชียงใหม่"),
        UserCreate(email="district.admin", password="Demo1234!",    full_name="นางสาวรัตนา พงษ์พันธ์", role=UserRole.DISTRICT_ADMIN,  district="เมืองเชียงใหม่"),
        UserCreate(email="vol.coord",      password="Demo1234!",    full_name="นางวิไลพร คำวงศ์",       role=UserRole.VOLUNTEER),
        UserCreate(email="viewer",         password="Demo1234!",    full_name="นายกิตติศักดิ์ สมใจ",   role=UserRole.VIEWER),
    ]
    created = []
    for u in users:
        try:
            user = await svc.create(u, actor="demo")
            created.append(user)
            print(f"  [OK] User: {u.email} ({u.full_name})")
        except ValueError:
            print(f"  [SKIP] User exists: {u.email}")
    await session.commit()
    return created


async def seed_volunteers(session) -> list:
    """Seed 30 อสม. volunteers with real Chiang Mai positions."""
    from sqlalchemy import select as _sel
    from app.modules.volunteers.model import Volunteer as _Vol
    svc = VolunteerService(session)
    vol_ids = []
    existing = (await session.execute(_sel(_Vol).limit(30))).scalars().all()
    if existing:
        print(f"  [SKIP] Volunteers already exist ({len(existing)})")
        return [v.id for v in existing]

    positions = ["อสม.ประจำหมู่บ้าน", "อสม.ผู้นำชุมชน", "อสม.ชำนาญการ",
                 "อสม.ดีเด่น", "อสม.อาวุโส", "อสม.ดูแลผู้สูงอายุ"]
    phones = [
        "052-001-2345", "081-234-5678", "082-345-6789", "083-456-7890",
        "084-567-8901", "085-678-9012", "086-789-0123", "087-890-1234",
        "088-901-2345", "089-012-3456", "091-123-4567", "092-234-5678",
        "093-345-6789", "094-456-7890", "095-567-8901", "096-678-9012",
        "097-789-0123", "098-890-1234", "099-901-2345", "061-012-3456",
        "062-123-4567", "063-234-5678", "064-345-6789", "065-456-7890",
        "066-567-8901", "067-678-9012", "068-789-0123", "069-890-1234",
        "076-901-2345", "077-012-3456",
    ]

    for i, name in enumerate(VOLUNTEER_NAMES[:30]):
        district = random.choice(DISTRICTS)
        subdistrict = random.choice(SUBDISTS)
        try:
            v = await svc.create(VolunteerCreate(
                volunteer_code=f"อสม.{district[:4]}-{i+1:04d}",
                full_name=name,
                phone=phones[i],
                province=random.choice(PROVINCES),
                district=district,
                subdistrict=subdistrict,
                village=f"หมู่ {random.randint(1, 15)}",
                position=random.choice(positions),
                status=random.choices(
                    [VolunteerStatus.ACTIVE, VolunteerStatus.INACTIVE],
                    weights=[90, 10]
                )[0],
            ), actor="demo")
            vol_ids.append(v.id)
        except Exception:
            pass
    await session.commit()
    print(f"  [OK] Volunteers (VHV): {len(vol_ids)}")
    return vol_ids


async def seed_households(session) -> list:
    """Seed 80 households with real Chiang Mai addresses."""
    from sqlalchemy import select as _sel
    from app.modules.households.model import Household as _HH
    svc = HouseholdService(session)
    hh_ids = []
    existing = (await session.execute(_sel(_HH).limit(80))).scalars().all()
    if existing:
        print(f"  [SKIP] Households already exist ({len(existing)})")
        return [h.id for h in existing]

    # ที่อยู่จริงในเชียงใหม่
    real_streets = [
        "ถ.นิมมานเหมินทร์", "ถ.สุเทพ", "ถ.ห้วยแก้ว", "ถ.เชียงใหม่-ลำปาง",
        "ถ.โชตนา", "ถ.มหิดล", "ถ.วงแหวนรอบกลาง", "ถ.ท่าแพ",
        "ถ.ช้างคลาน", "ถ.เจริญเมือง", "ถ.ราชมรรคา", "ถ.บุญเกิด",
        "ซ.ช้างม่อย", "ซ.ทุ่งโฮเต็ล", "ซ.สนามบิน", "ถ.สันกำแพง",
    ]

    family_names = [
        "วงศ์คำ", "แก้วมณี", "ศรีวิชัย", "คำมูล", "ใจดี",
        "ปัญญา", "สุขสวาท", "ทองดี", "รุ่งเรือง", "คำเงิน",
        "จันทร์แก้ว", "วงศ์จันทร์", "ชัยวงศ์", "ขันแก้ว", "พรหมสุวรรณ",
        "คำใจ", "วิชัยรัตน์", "สีดา", "แก้วพิทักษ์", "กาวิละ",
    ]

    for i in range(80):
        lat, lon = _rand_gps()
        district = random.choice(DISTRICTS)
        community = random.choice(COMMUNITIES)
        street = random.choice(real_streets)
        family = random.choice(family_names)
        house_num = random.randint(1, 999)
        moo = random.randint(1, 15)
        gender_prefix = random.choice(["นาย", "นาง", "นางสาว"])
        first_names = ["สมบัติ", "วิชัย", "รัตนา", "ประสิทธิ์", "มาลี",
                       "สุนีย์", "อำพร", "มานะ", "กาญจนา", "บุญมี"]
        head = f"{gender_prefix}{random.choice(first_names)} {family}"
        try:
            h = await svc.create(HouseholdCreate(
                household_code=f"HH-{district[:3]}-{i+1:05d}",
                head_of_household=head,
                address=f"{house_num} {street} หมู่ {moo} ต.{random.choice(SUBDISTS)} อ.{district}",
                village=f"หมู่ {moo}",
                community=community,
                district=district,
                province="เชียงใหม่",
                phone=f"0{random.randint(81,99)}-{random.randint(100,999)}-{random.randint(1000,9999)}",
                latitude=lat, longitude=lon,
                income_group=random.choice(list(IncomeGroup)),
                housing_type=random.choice(list(HousingType)),
            ), actor="demo")
            hh_ids.append(h.id)
        except Exception:
            pass
    await session.commit()
    print(f"  [OK] Households: {len(hh_ids)}")
    return hh_ids


async def seed_citizens(session, hh_ids) -> list:
    """Seed 300 citizens with realistic Thai names and demographics."""
    from sqlalchemy import select as _sel
    from app.modules.citizens.model import Citizen as _Cit
    svc = CitizenService(session)
    cit_ids = []
    existing = (await session.execute(_sel(_Cit).limit(300))).scalars().all()
    if existing:
        print(f"  [SKIP] Citizens already exist ({len(existing)})")
        return [c.id for c in existing]

    male_first = ["สมชาย", "วิชัย", "ประสิทธิ์", "สมบูรณ์", "อนันต์",
                  "มานะ", "สายัณห์", "ปรีชา", "วรพจน์", "สมศักดิ์",
                  "บุญมี", "อาทิตย์", "นิรันดร์", "สุพจน์", "ธวัชชัย",
                  "เกรียงไกร", "ณรงค์", "สุรชัย", "ภาณุ", "จิรพงศ์"]
    female_first = ["สุนีย์", "รัตนา", "ดวงจันทร์", "พิมพ์ใจ", "อรุณี",
                    "กาญจนา", "อำพร", "มาลี", "อัมพา", "ศิริพร",
                    "อุไร", "ณัฐฐา", "จิตรา", "ลัดดา", "ทิพย์วรรณ",
                    "สุภาพร", "นิภา", "วราภรณ์", "นันทนา", "ประไพ"]
    last_names = [
        "วงศ์คำ", "แก้วมณี", "ศรีวิชัย", "คำมูล", "ใจดี", "ปัญญา",
        "สุขสวาท", "ทองดี", "รุ่งเรือง", "คำเงิน", "จันทร์แก้ว",
        "วงศ์จันทร์", "ชัยวงศ์", "ขันแก้ว", "พรหมสุวรรณ", "คำใจ",
        "วิชัยรัตน์", "สีดา", "แก้วพิทักษ์", "กาวิละ", "ตันตราภรณ์",
        "พงษ์พันธ์", "คำวงศ์", "ศิริมงคล", "ดวงดี", "แสนสุข",
        "ชัยภูมิ", "แสงสว่าง", "คำหล้า", "ป้อมคำ",
    ]

    for i in range(300):
        dob = date.today() - timedelta(days=random.randint(365*3, 365*92))
        age = (date.today() - dob).days // 365
        elderly = age >= 60
        gender = random.choice([Gender.MALE, Gender.FEMALE, Gender.FEMALE])  # more female elderly
        if gender == Gender.MALE:
            first = random.choice(male_first)
            prefix = "นาย"
        else:
            first = random.choice(female_first)
            prefix = "นาง" if age > 25 else "นางสาว"
        full_name = f"{prefix}{first} {random.choice(last_names)}"
        try:
            c = await svc.create(CitizenCreate(
                household_id=random.choice(hh_ids) if hh_ids else None,
                full_name=full_name,
                gender=gender,
                date_of_birth=dob,
                phone=f"0{random.randint(81,99)}-{random.randint(100,999)}-{random.randint(1000,9999)}" if random.random() < 0.7 else None,
                occupation=random.choice(OCCUPATIONS),
                is_elderly=elderly,
                is_disabled=random.random() < 0.07,
                is_bedridden=random.random() < 0.025,
                is_pregnant=(gender == Gender.FEMALE and age < 45 and random.random() < 0.04),
                is_living_alone=elderly and random.random() < 0.28,
            ), actor="demo")
            cit_ids.append(c.id)
        except Exception:
            pass
    await session.commit()
    print(f"  [OK] Citizens: {len(cit_ids)}")
    return cit_ids


async def seed_health_profiles(session, cit_ids) -> None:
    """Seed health profiles reflecting real Thai chronic disease prevalence."""
    sample = random.sample(cit_ids, min(200, len(cit_ids)))
    count = 0
    for cid in sample:
        try:
            profile = HealthProfile(
                citizen_id=cid,
                blood_type=random.choice(["O+", "A+", "B+", "AB+", "O-", None]),
                # Thai prevalence: DM ~9%, HT ~24%, dyslipidemia ~35%
                has_diabetes=random.random() < 0.22,
                has_hypertension=random.random() < 0.30,
                has_dyslipidemia=random.random() < 0.25,
                has_heart_disease=random.random() < 0.10,
                has_stroke=random.random() < 0.05,
                has_cancer=random.random() < 0.04,
                has_kidney_disease=random.random() < 0.08,
                has_lung_disease=random.random() < 0.06,
                walks_independently=random.random() < 0.82,
                uses_cane=random.random() < 0.12,
                uses_wheelchair=random.random() < 0.04,
                is_homebound=random.random() < 0.09,
                is_bedridden_profile=random.random() < 0.03,
                lives_alone_profile=random.random() < 0.18,
                has_caregiver=random.random() < 0.45,
                has_income_problems=random.random() < 0.22,
                has_food_insecurity=random.random() < 0.12,
                has_social_isolation=random.random() < 0.15,
                unsafe_bathroom=random.random() < 0.18,
                slippery_floor=random.random() < 0.20,
                poor_lighting=random.random() < 0.12,
                needs_home_visit=random.random() < 0.38,
                needs_transportation=random.random() < 0.22,
                needs_welfare_assistance=random.random() < 0.18,
                needs_social_support=random.random() < 0.20,
                created_by="demo", updated_by="demo",
            )
            session.add(profile)
            count += 1
        except Exception:
            pass
    await session.commit()
    print(f"  [OK] Health Profiles: {count}")


async def seed_health_assessments(session, cit_ids, vol_ids) -> None:
    """Seed health assessments with realistic Thai biometrics."""
    count = 0
    sample = random.sample(cit_ids, min(180, len(cit_ids)))
    for cid in sample:
        n = random.randint(1, 4)
        for j in range(n):
            assess_date = _rand_date(365)
            # Thai average height/weight
            height = random.gauss(160, 8)   # Thai avg ~163cm
            weight = random.gauss(62, 12)
            height = max(145, min(185, height))
            weight = max(40, min(110, weight))
            bmi = calculate_bmi(weight, height)
            try:
                session.add(HealthAssessment(
                    citizen_id=cid,
                    volunteer_id=random.choice(vol_ids) if vol_ids else None,
                    assessment_date=str(assess_date),
                    assessment_type=random.choice(["routine", "follow_up", "annual", "home_visit"]),
                    height_cm=round(height, 1),
                    weight_kg=round(weight, 1),
                    bmi=bmi,
                    waist_cm=round(random.gauss(82, 12), 1),
                    bp_systolic=round(random.gauss(128, 18), 0),
                    bp_diastolic=round(random.gauss(78, 12), 0),
                    pulse_rate=round(random.gauss(76, 12), 0),
                    temperature_c=round(random.gauss(36.8, 0.4), 1),
                    created_by="demo", updated_by="demo",
                ))
                count += 1
            except Exception:
                pass
    await session.commit()
    print(f"  [OK] Health Assessments: {count}")


async def seed_home_visits(session, cit_ids, vol_ids) -> None:
    """Seed 400 home visits with realistic notes."""
    svc = HomeVisitService(session)
    count = 0
    for _ in range(400):
        lat, lon = _rand_gps()
        try:
            await svc.create(HomeVisitCreate(
                citizen_id=random.choice(cit_ids) if cit_ids else None,
                volunteer_id=random.choice(vol_ids) if vol_ids else None,
                visit_date=_rand_date(365),
                visit_type=random.choices(
                    list(VisitType), weights=[50, 30, 10, 10]
                )[0],
                observation=random.choice(VISIT_NOTES),
                recommendation=random.choice(VISIT_RECOMMENDATIONS),
                latitude=lat, longitude=lon,
            ), actor="demo")
            count += 1
        except Exception:
            pass
    await session.commit()
    print(f"  [OK] Home Visits: {count}")


async def seed_referrals(session, cit_ids, vol_ids) -> None:
    """Seed 100 referrals to real Thai health facilities and NGOs."""
    svc = ReferralService(session)
    targets = [
        ReferralTarget.HOSPITAL,
        ReferralTarget.HOSPITAL,
        ReferralTarget.HEALTH_CENTER,
        ReferralTarget.HEALTH_CENTER,
        ReferralTarget.MUNICIPALITY,
        ReferralTarget.NGO,
    ]
    statuses = [ReferralStatus.PENDING, ReferralStatus.IN_PROGRESS,
                ReferralStatus.COMPLETED, ReferralStatus.CANCELLED]
    weights  = [28, 22, 40, 10]
    count = 0
    for _ in range(100):
        ref_date = _rand_date(180)
        target   = random.choice(targets)
        status   = random.choices(statuses, weights=weights)[0]
        try:
            ref = await svc.create(ReferralCreate(
                citizen_id=random.choice(cit_ids) if cit_ids else None,
                volunteer_id=random.choice(vol_ids) if vol_ids else None,
                referral_date=ref_date,
                target=target,
                target_name=_rand_referral_target_name(target),
                reason=random.choice(REFERRAL_REASONS),
                status=status,
            ), actor="demo")
            if status == ReferralStatus.COMPLETED:
                ref.outcome = random.choice([
                    "ได้รับการรักษาครบถ้วนและกลับบ้านแล้ว",
                    "ได้รับยาและนัดติดตามผล 1 เดือน",
                    "ผ่าตัดสำเร็จ อยู่ระหว่างฟื้นฟู",
                    "ได้รับสิทธิ์สวัสดิการเรียบร้อย",
                ])
            elif status == ReferralStatus.CANCELLED:
                ref.outcome = random.choice([
                    "ผู้ป่วยปฏิเสธการส่งต่อ",
                    "ญาติพาไปโรงพยาบาลเองก่อน",
                    "อาการดีขึ้นก่อนถึงวันนัด",
                ])
            count += 1
        except Exception:
            pass
    await session.commit()
    print(f"  [OK] Referrals: {count}")


async def seed_tasks(session, cit_ids) -> None:
    """Seed 60 realistic อสม. tasks."""
    from sqlalchemy import select as _sel, func as _func
    cnt = (await session.execute(_sel(_func.count()).select_from(Task))).scalar() or 0
    if cnt > 0:
        print(f"  [SKIP] Tasks already exist ({cnt})")
        return
    priorities = ["low", "medium", "high", "critical"]
    p_weights  = [15, 45, 28, 12]
    statuses   = ["new", "assigned", "in_progress", "completed", "overdue"]
    s_weights  = [12, 18, 28, 32, 10]
    count = 0
    for i in range(60):
        due_date = date.today() + timedelta(days=random.randint(-10, 30))
        community = random.choice(COMMUNITIES)
        title = random.choice(TASK_TITLES).replace("ชุมชนวัดเกต", community)
        try:
            session.add(Task(
                task_code=f"TASK-{date.today().year}-{i+1:05d}",
                title=title,
                task_type=random.choice(["home_visit", "referral_followup",
                                          "citizen_followup", "community_survey"]),
                priority=random.choices(priorities, weights=p_weights)[0],
                status=random.choices(statuses, weights=s_weights)[0],
                due_date=str(due_date),
                citizen_id=random.choice(cit_ids) if cit_ids and random.random() < 0.6 else None,
                created_by="demo", updated_by="demo",
            ))
            count += 1
        except Exception:
            pass
    await session.commit()
    print(f"  [OK] Tasks: {count}")


async def seed_followups(session, cit_ids) -> None:
    """Seed 50 follow-up records."""
    types = ["citizen_not_visited", "referral_unresolved", "volunteer_inactive"]
    statuses = ["pending", "in_progress", "completed"]
    count = 0
    for i in range(50):
        try:
            session.add(Followup(
                citizen_id=random.choice(cit_ids) if cit_ids else None,
                followup_type=random.choice(types),
                followup_date=str(_rand_date(60)),
                status=random.choice(statuses),
                rule_triggered=random.choice(FOLLOWUP_RULES),
                created_by="demo", updated_by="demo",
            ))
            count += 1
        except Exception:
            pass
    await session.commit()
    print(f"  [OK] Follow-Ups: {count}")


async def seed_early_warnings(session, cit_ids) -> None:
    """Seed 60 early warnings and CVI scores."""
    alert_types = ["no_visit", "homebound_no_caregiver", "open_referral"]
    severities  = ["low", "medium", "high", "critical"]
    s_weights   = [25, 38, 25, 12]
    statuses    = ["open", "acknowledged", "resolved"]
    st_weights  = [48, 30, 22]
    count = 0
    for i in range(60):
        try:
            session.add(EarlyWarning(
                citizen_id=random.choice(cit_ids) if cit_ids else None,
                alert_type=random.choice(alert_types),
                severity=random.choices(severities, weights=s_weights)[0],
                title=random.choice(ALERT_TITLES),
                status=random.choices(statuses, weights=st_weights)[0],
                created_by="demo", updated_by="demo",
            ))
            count += 1
        except Exception:
            pass

    # CVI Scores
    cvi_count = 0
    for cid in random.sample(cit_ids, min(180, len(cit_ids))):
        score = round(random.uniform(5, 95), 1)
        if score < 25:   cat = "low"
        elif score < 50: cat = "moderate"
        elif score < 75: cat = "high"
        else:            cat = "critical"
        try:
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
            cvi_count += 1
        except Exception:
            pass
    await session.commit()
    print(f"  [OK] Early Warnings: {count} | CVI Scores: {cvi_count}")


async def seed_announcements(session) -> None:
    """Seed realistic Thai public health announcements."""
    from sqlalchemy import select as _sel, func as _func
    cnt = (await session.execute(_sel(_func.count()).select_from(Announcement))).scalar() or 0
    if cnt > 0:
        print(f"  [SKIP] Announcements already exist ({cnt})")
        return
    ann_data = [
        (
            "รณรงค์ตรวจสุขภาพประจำปี 2569 — สำนักงานสาธารณสุขจังหวัดเชียงใหม่",
            "กรุณาเข้ารับการตรวจสุขภาพประจำปีที่โรงพยาบาลนครพิงค์ โรงพยาบาลมหาราชนครเชียงใหม่ หรือ รพ.สต. ใกล้บ้าน ตั้งแต่วันที่ 1 มิถุนายน – 31 สิงหาคม 2569",
            "health_campaign",
        ),
        (
            "ขอเชิญอสม.เข้าร่วมประชุมประจำเดือนมิถุนายน 2569",
            "สำนักงานสาธารณสุขอำเภอเมืองเชียงใหม่ ขอเชิญ อสม. ทุกท่านเข้าร่วมประชุมในวันที่ 10 มิถุนายน 2569 เวลา 09.00 น. ณ ห้องประชุมศูนย์อนามัยเขตที่ 1 เชียงใหม่",
            "volunteer_notice",
        ),
        (
            "เตือนภัยโรคไข้เลือดออก ฤดูฝน 2569",
            "พบผู้ป่วยไข้เลือดออกเพิ่มขึ้น กรุณาทำลายแหล่งเพาะพันธุ์ยุง ทั้งในบ้านและรอบบ้าน หากมีไข้สูงเกิน 3 วัน ให้รีบพบแพทย์ที่โรงพยาบาลใกล้บ้าน สายด่วนสาธารณสุข 1422",
            "community_news",
        ),
        (
            "โครงการวัคซีนไข้หวัดใหญ่ฟรีผู้สูงอายุ 2569 — สภากาชาดไทย สาขาเชียงใหม่",
            "ผู้สูงอายุ 60 ปีขึ้นไป สามารถรับวัคซีนไข้หวัดใหญ่ฟรีได้ที่ รพ.สต. ทุกแห่ง และศูนย์บริการสาธารณสุขเทศบาลนครเชียงใหม่ ตั้งแต่บัดนี้ถึงสิ้นเดือนกันยายน 2569",
            "health_campaign",
        ),
        (
            "มูลนิธิกระจกเงา เปิดรับผู้สูงอายุยากไร้ขอรับความช่วยเหลือ",
            "มูลนิธิกระจกเงา ร่วมกับมูลนิธิปอเต็กตึ้ง เปิดรับผู้สูงอายุและผู้พิการที่มีฐานะยากจนในพื้นที่เชียงใหม่ขอรับความช่วยเหลือด้านอาหารและยา ติดต่อ 02-374-2678",
            "community_news",
        ),
        (
            "แจ้งเตือนฉุกเฉิน: พบผู้ป่วยปอดอักเสบคลัสเตอร์ในอำเภอสันทราย",
            "สำนักงานสาธารณสุขจังหวัดเชียงใหม่ขอให้อสม.ในพื้นที่อำเภอสันทรายสำรวจและรายงานผู้ป่วยไข้สูง ไอ หายใจลำบาก ทันที โทร 1422 หรือสายด่วนสสจ.เชียงใหม่ 053-211-048",
            "emergency_alert",
        ),
        (
            "เปิดรับสมัครอสม.ใหม่ ประจำปี 2569",
            "สำนักงานสาธารณสุขอำเภอหางดง เปิดรับสมัครอาสาสมัครสาธารณสุขประจำหมู่บ้าน (อสม.) รุ่นใหม่ อายุ 18–60 ปี สุขภาพแข็งแรง มีภูมิลำเนาในพื้นที่ สมัครได้ที่ รพ.สต. ใกล้บ้าน",
            "volunteer_notice",
        ),
    ]
    count = 0
    for title, content, atype in ann_data:
        try:
            session.add(Announcement(
                title=title, content=content,
                announcement_type=atype,
                start_date=str(date.today() - timedelta(days=random.randint(0, 30))),
                end_date=str(date.today() + timedelta(days=random.randint(14, 90))),
                target_province="เชียงใหม่",
                is_active=True,
                created_by="demo", updated_by="demo",
            ))
            count += 1
        except Exception:
            pass
    await session.commit()
    print(f"  [OK] Announcements: {count}")


async def seed_community_projects(session) -> None:
    """Seed realistic community health projects in Chiang Mai."""
    projects = [
        ("PROJ2569-001", "ชมรมผู้สูงอายุสุขใจ ชุมชนวัดเกต", "elderly_club", "active", 58000),
        ("PROJ2569-002", "โครงการออกกำลังกายเพื่อผู้สูงอายุ อ.สันทราย", "exercise_program", "active", 35000),
        ("PROJ2569-003", "ปรับสภาพแวดล้อมบ้านผู้พิการ ร่วมกับมูลนิธิศุภนิมิต", "home_modification", "completed", 128000),
        ("PROJ2569-004", "สำรวจสุขภาพชุมชนช้างเผือก ครอบคลุม 350 ครัวเรือน", "community_survey", "planning", 22000),
        ("PROJ2569-005", "อบรมอสม.ชำนาญการดูแลผู้สูงอายุ รุ่นที่ 3", "health_activity", "active", 48000),
        ("PROJ2569-006", "สวนสมุนไพรสุขภาพชุมชนหางดง", "other", "planning", 85000),
        ("PROJ2569-007", "โครงการอาหารปลอดภัยผู้สูงอายุ ร่วมกับเทศบาลนครเชียงใหม่", "health_activity", "completed", 42000),
        ("PROJ2569-008", "คลินิกเคลื่อนที่ดูแลผู้ป่วยติดเตียง อ.เมืองเชียงใหม่", "health_activity", "active", 168000),
        ("PROJ2569-009", "โครงการป้องกันการหกล้มผู้สูงอายุ ร่วมกับโรงพยาบาลนครพิงค์", "health_activity", "active", 75000),
        ("PROJ2569-010", "แจกอุปกรณ์ช่วยเหลือผู้พิการ ร่วมกับมูลนิธิปอเต็กตึ้ง", "home_modification", "active", 95000),
    ]
    owners = [
        "นางวิไลพร คำวงศ์", "นายสมชาย ตันตราภรณ์", "นางสาวรัตนา พงษ์พันธ์",
        "นายมานะ ทองดี", "นางสุนีย์ วงศ์คำ", "นายประสิทธิ์ แก้วมณี",
    ]
    count = 0
    for code, name, ptype, status, budget in projects:
        try:
            session.add(CommunityProject(
                project_code=code, project_name=name,
                project_type=ptype, status=status, budget=budget,
                start_date=str(_rand_date(180)),
                end_date=str(date.today() + timedelta(days=random.randint(30, 180))),
                owner=random.choice(owners),
                province="เชียงใหม่",
                district=random.choice(DISTRICTS),
                created_by="demo", updated_by="demo",
            ))
            count += 1
        except Exception:
            pass
    await session.commit()
    print(f"  [OK] Community Projects: {count}")


async def seed_quality_indicators(session) -> None:
    """Seed quality indicators with 6 months of realistic records."""
    count_ind = 0
    for code, name, cat, target, unit in DEFAULT_INDICATORS:
        try:
            from sqlalchemy import select
            existing = (await session.execute(
                select(QualityIndicator).where(QualityIndicator.indicator_code == code)
            )).scalar_one_or_none()
            if not existing:
                ind = QualityIndicator(
                    indicator_code=code, indicator_name=name,
                    category=cat, target_value=target, unit=unit,
                    created_by="demo", updated_by="demo",
                )
                session.add(ind)
                await session.flush()
            # 6 months of records with realistic variation
            for m in range(1, 7):
                actual = round(random.uniform(target * 0.65, min(target * 1.05, 100)), 1)
                session.add(QualityRecord(
                    indicator_id=code,
                    period_year=2026,
                    period_month=m,
                    actual_value=actual,
                    created_by="demo", updated_by="demo",
                ))
            count_ind += 1
        except Exception:
            pass
    await session.commit()
    print(f"  [OK] Quality Indicators + Records: {count_ind}")


async def seed_scorecards(session) -> None:
    """Seed community scorecards for real Chiang Mai communities."""
    count = 0
    for comm in COMMUNITIES:
        for month in range(1, 7):
            scores = {
                "coverage_rate": round(random.uniform(60, 95), 1),
                "assessment_rate": round(random.uniform(55, 92), 1),
                "home_visit_rate": round(random.uniform(62, 98), 1),
                "referral_completion_rate": round(random.uniform(60, 95), 1),
                "case_closure_rate": round(random.uniform(55, 90), 1),
                "volunteer_activity_rate": round(random.uniform(65, 98), 1),
            }
            overall = round(sum(scores.values()) / len(scores), 1)
            district = random.choice(DISTRICTS)
            try:
                session.add(CommunityScorecard(
                    community_id=comm.replace(" ", "_"),
                    community_name=comm,
                    district=district,
                    month=month, year=2026,
                    population=random.randint(800, 3500),
                    overall_score=overall,
                    **scores,
                    created_by="demo", updated_by="demo",
                ))
                count += 1
            except Exception:
                pass
    await session.commit()
    print(f"  [OK] Community Scorecards: {count}")


async def seed_performance_metrics(session) -> None:
    """Seed KPI performance metrics for 2569 Q2."""
    metrics = [
        ("อัตราการเยี่ยมบ้านผู้สูงอายุ", "home_visit_frequency", 85.0, 79.5, "%"),
        ("อัตราการส่งต่อสำเร็จ", "referral_completion", 80.0, 73.2, "%"),
        ("อัตราการประเมินสุขภาพ", "assessment_coverage", 70.0, 68.8, "%"),
        ("กิจกรรมอสม.ประจำเดือน", "volunteer_productivity", 75.0, 84.0, "%"),
        ("อัตราการปิดเคส", "case_closure", 65.0, 59.5, "%"),
        ("ความครอบคลุมสนับสนุนสังคม", "social_support", 60.0, 56.2, "%"),
        ("อัตราการเยี่ยมผู้ป่วยติดเตียง", "home_visit_frequency", 95.0, 88.0, "%"),
        ("อัตราการรับวัคซีนไข้หวัดใหญ่", "campaign_coverage", 70.0, 62.5, "%"),
    ]
    count = 0
    for name, cat, target, current, unit in metrics:
        from app.modules.performance_management.service import compute_status
        status = compute_status(current, target)
        try:
            session.add(PerformanceMetric(
                metric_name=name, metric_category=cat,
                target=target, current_value=current, unit=unit,
                status=status, period="2569-Q2",
                created_by="demo", updated_by="demo",
            ))
            count += 1
        except Exception:
            pass
    await session.commit()
    print(f"  [OK] Performance Metrics: {count}")


async def seed_outcomes(session, cit_ids) -> None:
    """Seed realistic case outcomes."""
    outcome_types = ["improved", "stable", "deteriorated", "resolved", "ongoing"]
    weights = [30, 25, 10, 20, 15]
    baseline_templates = [
        "ความดันโลหิต 160/100 mmHg", "น้ำตาลในเลือด 220 mg/dL",
        "BMI 31.5 (อ้วนระดับ 1)", "ไม่สามารถช่วยเหลือตัวเองได้",
        "ซึมเศร้าระดับปานกลาง (PHQ-9 = 12)",
    ]
    current_templates = [
        "ความดันโลหิต 130/82 mmHg (ดีขึ้น)", "น้ำตาลในเลือด 140 mg/dL (ดีขึ้น)",
        "BMI 28.2 (ลดลง)", "สามารถเดินได้ด้วยไม้เท้า",
        "ซึมเศร้าระดับน้อย (PHQ-9 = 6)",
    ]
    count = 0
    for i in range(60):
        otype = random.choices(outcome_types, weights=weights)[0]
        idx = random.randint(0, len(baseline_templates) - 1)
        try:
            session.add(CaseOutcome(
                citizen_id=str(random.choice(cit_ids)) if cit_ids else None,
                case_ref=f"CASE-2569-{i+1:04d}",
                outcome_type=otype,
                baseline_value=baseline_templates[idx],
                current_value=current_templates[idx],
                outcome_status="closed" if otype in ("resolved", "improved") else "open",
                evaluation_date=str(_rand_date(90)),
                notes=random.choice([
                    "ติดตามผลการรักษาตามแผน อาการดีขึ้นต่อเนื่อง",
                    "ส่งต่อโรงพยาบาลนครพิงค์เพื่อตรวจเพิ่มเติม",
                    "ปรับเปลี่ยนพฤติกรรมสุขภาพตามคำแนะนำ",
                    "ได้รับความช่วยเหลือจากมูลนิธิปอเต็กตึ้ง",
                ]),
                created_by="demo", updated_by="demo",
            ))
            count += 1
        except Exception:
            pass
    await session.commit()
    print(f"  [OK] Case Outcomes: {count}")


async def seed_risk_scores(session, cit_ids) -> None:
    """Seed risk stratification scores."""
    levels = ["low", "moderate", "high", "critical"]
    l_weights = [35, 35, 20, 10]
    count = 0
    for cid in random.sample(cit_ids, min(220, len(cit_ids))):
        level = random.choices(levels, weights=l_weights)[0]
        score = {
            "low": random.uniform(5, 24),
            "moderate": random.uniform(25, 49),
            "high": random.uniform(50, 74),
            "critical": random.uniform(75, 100),
        }[level]
        try:
            session.add(RiskScore(
                citizen_id=str(cid),
                score=round(score, 1),
                risk_level=level,
                factors=random.choice(RISK_FACTORS),
                calculation_date=str(date.today()),
                created_by="demo", updated_by="demo",
            ))
            count += 1
        except Exception:
            pass
    await session.commit()
    print(f"  [OK] Risk Scores: {count}")


async def seed_notifications(session) -> None:
    """Seed realistic in-app notifications."""
    from sqlalchemy import select as sa_select
    from app.modules.users.model import User as UserModel
    notif_data = [
        ("new_task", "มีงานเยี่ยมบ้านใหม่", "กรุณาตรวจสอบงานเยี่ยมบ้านผู้สูงอายุกลุ่มเสี่ยงที่ได้รับมอบหมาย"),
        ("overdue_task", "งานเกินกำหนด 5 รายการ", "มีงานเยี่ยมบ้านที่เกินกำหนดส่งรายงาน กรุณาอัพเดทสถานะ"),
        ("followup_reminder", "แจ้งเตือนการติดตาม 12 ราย", "ผู้สูงอายุที่ไม่ได้รับการเยี่ยมบ้านเกิน 90 วัน รอการติดตาม"),
        ("referral_reminder", "การส่งต่อโรงพยาบาลค้างนาน", "การส่งต่อไปโรงพยาบาลนครพิงค์ 3 รายการ ยังไม่ได้รับการดำเนินการ"),
        ("new_announcement", "ประกาศใหม่จากสสจ.เชียงใหม่", "รณรงค์ตรวจสุขภาพประจำปี 2569 เริ่มแล้ว"),
    ]
    try:
        users = (await session.execute(sa_select(UserModel).limit(5))).scalars().all()
        count = 0
        for user in users:
            for ntype, title, msg in notif_data:
                session.add(Notification(
                    user_id=user.id, type=ntype,
                    title=title, message=msg,
                    is_read=random.random() < 0.4,
                    created_by="demo", updated_by="demo",
                ))
                count += 1
        await session.commit()
        print(f"  [OK] Notifications: {count}")
    except Exception as e:
        print(f"  [WARN] Notifications skipped: {e}")



async def seed_campaigns(session) -> None:
    """Seed realistic health campaigns for Chiang Mai."""
    from sqlalchemy import select as _sel, text as _text
    # Ensure table exists
    await session.execute(_text("""
        CREATE TABLE IF NOT EXISTS health_campaigns (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            campaign_code VARCHAR(50) UNIQUE NOT NULL,
            campaign_name VARCHAR(300) NOT NULL,
            campaign_type VARCHAR(50) DEFAULT 'health_screening',
            description TEXT, target_group VARCHAR(100),
            start_date VARCHAR(20), end_date VARCHAR(20),
            province VARCHAR(100), district VARCHAR(100),
            venue VARCHAR(300), budget FLOAT,
            target_count INTEGER, actual_count INTEGER,
            status VARCHAR(20) DEFAULT 'planning',
            organizer VARCHAR(200), notes TEXT,
            is_deleted BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT NOW(), updated_at TIMESTAMP DEFAULT NOW(),
            created_by VARCHAR(100), updated_by VARCHAR(100)
        )
    """))
    campaigns = [
        ("CAMP-2569-001","รณรงค์ตรวจสุขภาพประจำปี 2569","health_screening","elderly","active","2026-04-01","2026-08-31","โรงพยาบาลมหาราชนครเชียงใหม่",2500,2180,75000),
        ("CAMP-2569-002","ฉีดวัคซีนไข้หวัดใหญ่ผู้สูงอายุ","vaccination","elderly","completed","2026-03-01","2026-05-31","รพ.สต.บ้านสันทรายหลวง",800,762,28000),
        ("CAMP-2569-003","ให้ความรู้โรคเบาหวาน-ความดัน","health_education","chronic_disease","active","2026-05-01","2026-07-31","ศูนย์บริการสาธารณสุข 1 (หายยา)",400,215,12000),
        ("CAMP-2569-004","ออกกำลังกายเพื่อสุขภาพผู้สูงอายุ","exercise","elderly","active","2026-01-01","2026-12-31","สวนสาธารณะหนองบวกหาด",300,280,45000),
        ("CAMP-2569-005","ตรวจสุขภาพฟันเด็กประถม","dental_health","children","completed","2026-02-01","2026-03-31","โรงเรียนสันทรายวิทยาคม",500,488,18000),
        ("CAMP-2569-006","อนามัยแม่และเด็ก","maternal_health","pregnant","active","2026-04-01","2026-09-30","รพ.สต.บ้านหนองหอย",120,98,22000),
        ("CAMP-2569-007","ป้องกันไข้เลือดออกชุมชน","disease_prevention","all","active","2026-05-01","2026-08-31","ชุมชนวัดเกต",1500,320,8000),
        ("CAMP-2569-008","สุขภาพจิตผู้สูงอายุและผู้ดูแล","mental_health","elderly","planning","2026-07-01","2026-09-30","ศูนย์ดูแลผู้สูงอายุกองทัพธรรม",200,0,35000),
    ]
    count = 0
    for code,name,ctype,tgroup,status,start,end,venue,target,actual,budget in campaigns:
        try:
            await session.execute(_text("""
                INSERT INTO health_campaigns
                    (id,campaign_code,campaign_name,campaign_type,target_group,
                     status,start_date,end_date,venue,target_count,actual_count,
                     budget,province,district,organizer,is_deleted,
                     created_at,updated_at,created_by,updated_by)
                VALUES
                    (gen_random_uuid(),:code,:name,:ctype,:tgroup,
                     :status,:start,:end,:venue,:target,:actual,
                     :budget,'เชียงใหม่','เมืองเชียงใหม่','สำนักงานสาธารณสุขจังหวัดเชียงใหม่',
                     false,NOW(),NOW(),'demo','demo')
                ON CONFLICT (campaign_code) DO NOTHING
            """), dict(code=code,name=name,ctype=ctype,tgroup=tgroup,
                       status=status,start=start,end=end,venue=venue,
                       target=target,actual=actual,budget=budget))
            count += 1
        except Exception:
            pass
    await session.commit()
    print(f"  [OK] Campaigns: {count}")

async def main():
    print("=" * 65)
    print("[MKI] MKI Community Health Platform - Demo Data Generator (2569)")
    print("   Chiang Mai / San Sai / Hang Dong / Lamphun")
    print("=" * 65)

    async with AsyncSessionLocal() as session:
        from sqlalchemy import select as _sel, func as _func
        from app.modules.citizens.model import Citizen as _Cit
        existing_count = (await session.execute(_sel(_func.count()).select_from(_Cit))).scalar() or 0
        if existing_count > 0:
            print(f"\n[WARN] Database already has {existing_count} citizens.")
            print("   To reload: clear data first or use System Health -> Reset Demo Data")
            print("\n[OK] Check complete - existing data preserved.")
            return

        print("\n[1/15] Users...")
        await seed_users(session)
        print("\n[2/15] Volunteers (VHV)...")
        vol_ids = await seed_volunteers(session)
        print("\n[3/15] Households...")
        hh_ids = await seed_households(session)
        print("\n[4/15] Citizens...")
        cit_ids = await seed_citizens(session, hh_ids)
        print("\n[5/15] Health Profiles...")
        await seed_health_profiles(session, cit_ids)
        print("\n[6/15] Health Assessments...")
        await seed_health_assessments(session, cit_ids, vol_ids)
        print("\n[7/15] Home Visits...")
        await seed_home_visits(session, cit_ids, vol_ids)
        print("\n[8/15] Referrals...")
        await seed_referrals(session, cit_ids, vol_ids)
        print("\n[9/15] Tasks...")
        await seed_tasks(session, cit_ids)
        print("\n[10/15] Follow-Ups...")
        await seed_followups(session, cit_ids)
        print("\n[11/15] Early Warnings & CVI...")
        await seed_early_warnings(session, cit_ids)
        print("\n[12/15] Announcements...")
        await seed_announcements(session)
        print("\n[13/15] Community Projects...")
        await seed_community_projects(session)
        print("\n[14/15] Quality Indicators...")
        await seed_quality_indicators(session)
        print("\n[14b] Scorecards...")
        await seed_scorecards(session)
        print("\n[14c] Performance Metrics...")
        await seed_performance_metrics(session)
        print("\n[14d] Case Outcomes...")
        await seed_outcomes(session, cit_ids)
        print("\n[14e] Risk Scores...")
        await seed_risk_scores(session, cit_ids)
        print("\n[14f] Notifications...")
        await seed_notifications(session)
        print("\n[15/15] Campaigns...")
        await seed_campaigns(session)

    print("\n" + "=" * 65)
    print("[DONE] Demo data loaded successfully!")
    print("=" * 65)
    print("\nLogin credentials:")
    print("  admin          / ChangeMe123!  (Super Admin)")
    print("  province.admin / Demo1234!     (Province Admin)")
    print("  district.admin / Demo1234!     (District Admin)")
    print("  vol.coord      / Demo1234!     (Volunteer)")
    print("  viewer         / Demo1234!     (Viewer)")
    print("\nOpen browser: http://127.0.0.1:8501")


if __name__ == "__main__":
    asyncio.run(main())
