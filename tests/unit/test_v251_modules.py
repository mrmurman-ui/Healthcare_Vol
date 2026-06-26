"""Tests for V2.51 — Health Profiles, Assessments, CVI, Early Warning."""
from datetime import date
import pytest
import pytest_asyncio

from app.modules.health_profiles.model import HealthProfile
from app.modules.health_assessments.model import HealthAssessment
from app.modules.early_warning.model import EarlyWarning, CVIScore


# ── BMI Calculator ────────────────────────────────────────────────────────────

def test_bmi_calculation():
    from app.modules.health_assessments.service import calculate_bmi
    bmi = calculate_bmi(70, 170)
    assert bmi == 24.2


def test_bmi_zero_height():
    from app.modules.health_assessments.service import calculate_bmi
    assert calculate_bmi(70, 0) is None


def test_bmi_category_normal():
    from app.modules.health_assessments.service import bmi_category
    assert bmi_category(21.0) == "Normal"


def test_bmi_category_obese():
    from app.modules.health_assessments.service import bmi_category
    assert bmi_category(30.0) == "Obese"


def test_bmi_category_underweight():
    from app.modules.health_assessments.service import bmi_category
    assert bmi_category(17.0) == "Underweight"


def test_bmi_category_none():
    from app.modules.health_assessments.service import bmi_category
    assert bmi_category(None) == "—"


# ── CVI Calculator ────────────────────────────────────────────────────────────

class MockCitizen:
    date_of_birth = date(1940, 1, 1)  # ~85 years old


class MockProfile:
    lives_alone_profile = True
    has_caregiver = False
    has_income_problems = True
    has_food_insecurity = False
    has_diabetes = True
    has_hypertension = True
    has_dyslipidemia = False
    has_heart_disease = False
    has_stroke = False
    has_cancer = False
    has_kidney_disease = False
    has_lung_disease = False
    is_homebound = True
    is_bedridden_profile = False
    unsafe_bathroom = True
    slippery_floor = True
    poor_lighting = False
    unsafe_stairs = False
    electrical_hazards = False
    structural_damage = False


def test_cvi_high_risk():
    from app.modules.early_warning.service import calculate_cvi
    result = calculate_cvi(MockCitizen(), MockProfile())
    assert result["score"] > 50
    assert result["category"] in ["high", "critical"]


def test_cvi_no_profile():
    from app.modules.early_warning.service import calculate_cvi

    class YoungCitizen:
        date_of_birth = date(2000, 1, 1)

    result = calculate_cvi(YoungCitizen(), None)
    assert result["score"] < 25
    assert result["category"] == "low"


def test_cvi_score_bounded():
    from app.modules.early_warning.service import calculate_cvi
    result = calculate_cvi(MockCitizen(), MockProfile())
    assert 0 <= result["score"] <= 100


def test_cvi_categories():
    from app.modules.early_warning.service import calculate_cvi
    result = calculate_cvi(MockCitizen(), MockProfile())
    assert result["category"] in ["low", "moderate", "high", "critical"]


# ── Health Profile model tests ────────────────────────────────────────────────

def test_chronic_condition_count():
    from app.modules.health_profiles.service import chronic_condition_count
    profile = HealthProfile(
        citizen_id=None,
        has_diabetes=True,
        has_hypertension=True,
        has_cancer=False,
    )
    assert chronic_condition_count(profile) == 2


# ── Integration tests ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_health_assessment(session):
    import uuid
    citizen_id = uuid.uuid4()
    assessment = HealthAssessment(
        citizen_id=citizen_id,
        assessment_date=str(date.today()),
        assessment_type="routine",
        weight_kg=65.0,
        height_cm=165.0,
        bmi=23.9,
        bp_systolic=120.0,
        bp_diastolic=80.0,
        created_by="test", updated_by="test",
    )
    session.add(assessment)
    await session.flush()
    await session.refresh(assessment)
    assert assessment.id is not None
    assert assessment.bmi == 23.9


@pytest.mark.asyncio
async def test_create_early_warning(session):
    import uuid
    warning = EarlyWarning(
        citizen_id=uuid.uuid4(),
        alert_type="no_visit",
        severity="medium",
        title="No visit in 90 days",
        status="open",
        created_by="system", updated_by="system",
    )
    session.add(warning)
    await session.flush()
    await session.refresh(warning)
    assert warning.id is not None
    assert warning.severity == "medium"
    assert warning.status == "open"


@pytest.mark.asyncio
async def test_warning_status_update(session):
    import uuid
    warning = EarlyWarning(
        citizen_id=uuid.uuid4(),
        alert_type="open_referral",
        severity="high",
        title="Open referral 30+ days",
        status="open",
        created_by="system", updated_by="system",
    )
    session.add(warning)
    await session.flush()
    warning.status = "resolved"
    warning.resolved_by = "admin"
    await session.flush()
    await session.refresh(warning)
    assert warning.status == "resolved"


@pytest.mark.asyncio
async def test_create_cvi_score(session):
    import uuid
    cvi = CVIScore(
        citizen_id=uuid.uuid4(),
        score=72.5,
        category="high",
        age_score=20.0,
        social_score=24.0,
        health_score=20.0,
        environment_score=8.5,
        last_calculated=str(date.today()),
        created_by="system", updated_by="system",
    )
    session.add(cvi)
    await session.flush()
    await session.refresh(cvi)
    assert cvi.score == 72.5
    assert cvi.category == "high"


# ── Assessment type validation ────────────────────────────────────────────────

def test_assessment_types_defined():
    from app.modules.health_assessments.model import ASSESSMENT_TYPES
    assert "routine" in ASSESSMENT_TYPES
    assert "annual" in ASSESSMENT_TYPES
    assert "follow_up" in ASSESSMENT_TYPES


# ── Severity levels ───────────────────────────────────────────────────────────

def test_severity_emoji_map():
    from app.modules.early_warning.service import SEVERITY_EMOJI
    assert "critical" in SEVERITY_EMOJI
    assert "high" in SEVERITY_EMOJI
    assert "🚨" in SEVERITY_EMOJI["critical"]


# ── No diagnosis check ────────────────────────────────────────────────────────

def test_cvi_not_labeled_as_disease_risk():
    """CVI must be labelled as community support priority, not disease risk."""
    from app.modules.early_warning.service import render_cvi
    import inspect
    source = inspect.getsource(render_cvi)
    assert "disease risk" not in source.lower()
    assert "diagnos" not in source.lower()
