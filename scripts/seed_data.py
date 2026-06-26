"""Seed the database with realistic Thai sample data.
Run: python scripts/seed_data.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import random
from datetime import date, timedelta

from faker import Faker

from app.core.database import AsyncSessionLocal
from app.modules.citizens.service import CitizenCreate, CitizenService
from app.modules.home_visits.service import HomeVisitCreate, HomeVisitService
from app.modules.households.service import HouseholdCreate, HouseholdService
from app.modules.referrals.service import ReferralCreate, ReferralService
from app.modules.users.schema import UserCreate
from app.modules.users.service import UserService
from app.modules.volunteers.schema import VolunteerCreate
from app.modules.volunteers.service import VolunteerService
from app.shared.enums import (
    Gender, HousingType, IncomeGroup, ReferralTarget,
    UserRole, VisitType, VolunteerStatus,
)

fake = Faker("th_TH")

PROVINCES = ["เชียงใหม่", "กรุงเทพมหานคร", "ขอนแก่น", "สงขลา"]
DISTRICTS = ["เมือง", "สันทราย", "หางดง", "สันกำแพง"]
CM_LAT, CM_LON = 18.7883, 98.9853


async def seed():
    # ── Admin user ────────────────────────────────────────────────────────────
    async with AsyncSessionLocal() as session:
        try:
            await UserService(session).create(UserCreate(
                email="admin",
                password="ChangeMe123!",
                full_name="Super Admin",
                role=UserRole.SUPER_ADMIN,
            ))
            await session.commit()
            print("✅ Admin user created.")
        except Exception:
            await session.rollback()
            print("ℹ️  Admin user already exists — skipped.")

    # ── Volunteers ────────────────────────────────────────────────────────────
    vol_ids = []
    for i in range(20):
        async with AsyncSessionLocal() as session:
            try:
                v = await VolunteerService(session).create(VolunteerCreate(
                    volunteer_code=f"VOL{i+1:04d}",
                    full_name=fake.name(),
                    phone=fake.phone_number()[:15],
                    province=random.choice(PROVINCES),
                    district=random.choice(DISTRICTS),
                    subdistrict=fake.city_suffix(),
                    village=f"หมู่ {random.randint(1, 15)}",
                    position="อสม.",
                    status=random.choice([VolunteerStatus.ACTIVE, VolunteerStatus.ACTIVE, VolunteerStatus.INACTIVE]),
                ))
                await session.commit()
                vol_ids.append(v.id)
            except Exception:
                await session.rollback()  # duplicate — skip

    print(f"✅ {len(vol_ids)} volunteers created (duplicates skipped).")

    # ── Households ────────────────────────────────────────────────────────────
    hh_ids = []
    for i in range(50):
        async with AsyncSessionLocal() as session:
            try:
                h = await HouseholdService(session).create(HouseholdCreate(
                    household_code=f"HH{i+1:05d}",
                    head_of_household=fake.name(),
                    address=fake.address()[:200],
                    village=f"หมู่ {random.randint(1, 15)}",
                    district=random.choice(DISTRICTS),
                    province="เชียงใหม่",
                    phone=fake.phone_number()[:15],
                    latitude=CM_LAT + random.uniform(-0.1, 0.1),
                    longitude=CM_LON + random.uniform(-0.1, 0.1),
                    income_group=random.choice(list(IncomeGroup)),
                    housing_type=random.choice(list(HousingType)),
                ))
                await session.commit()
                hh_ids.append(h.id)
            except Exception:
                await session.rollback()

    print(f"✅ {len(hh_ids)} households created (duplicates skipped).")

    # ── Citizens ──────────────────────────────────────────────────────────────
    cit_ids = []
    for i in range(200):
        async with AsyncSessionLocal() as session:
            try:
                dob = date.today() - timedelta(days=random.randint(365*5, 365*90))
                age = (date.today() - dob).days // 365
                c = await CitizenService(session).create(CitizenCreate(
                    household_id=random.choice(hh_ids) if hh_ids else None,
                    full_name=fake.name(),
                    gender=random.choice(list(Gender)),
                    date_of_birth=dob,
                    phone=fake.phone_number()[:15],
                    occupation=fake.job()[:100],
                    is_elderly=age >= 60,
                    is_disabled=random.random() < 0.05,
                    is_bedridden=random.random() < 0.02,
                    is_pregnant=random.random() < 0.03,
                    is_living_alone=random.random() < 0.1,
                ))
                await session.commit()
                cit_ids.append(c.id)
            except Exception:
                await session.rollback()

    print(f"✅ {len(cit_ids)} citizens created.")

    # ── Home Visits ───────────────────────────────────────────────────────────
    vis_count = 0
    for _ in range(100):
        async with AsyncSessionLocal() as session:
            try:
                await HomeVisitService(session).create(HomeVisitCreate(
                    citizen_id=random.choice(cit_ids) if cit_ids else None,
                    volunteer_id=random.choice(vol_ids) if vol_ids else None,
                    visit_date=date.today() - timedelta(days=random.randint(0, 180)),
                    visit_type=random.choice(list(VisitType)),
                    observation=fake.sentence(nb_words=15),
                    recommendation=fake.sentence(nb_words=10),
                    latitude=CM_LAT + random.uniform(-0.05, 0.05),
                    longitude=CM_LON + random.uniform(-0.05, 0.05),
                ))
                await session.commit()
                vis_count += 1
            except Exception:
                await session.rollback()

    print(f"✅ {vis_count} home visits created.")

    # ── Referrals ─────────────────────────────────────────────────────────────
    ref_count = 0
    for _ in range(30):
        async with AsyncSessionLocal() as session:
            try:
                await ReferralService(session).create(ReferralCreate(
                    citizen_id=random.choice(cit_ids) if cit_ids else None,
                    volunteer_id=random.choice(vol_ids) if vol_ids else None,
                    referral_date=date.today() - timedelta(days=random.randint(0, 90)),
                    target=random.choice(list(ReferralTarget)),
                    target_name=fake.company()[:100],
                    reason=fake.sentence(nb_words=10),
                ))
                await session.commit()
                ref_count += 1
            except Exception:
                await session.rollback()

    print(f"✅ {ref_count} referrals created.")
    print("\n🎉 Seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed())
