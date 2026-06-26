"""Tests for V2.53 — Quality, Outcomes, Risk, Scorecards, Performance, Capacity."""
from datetime import date
import pytest


# ── Risk Stratification ───────────────────────────────────────────────────────

class MockCitizen:
    date_of_birth = date(1940, 1, 1)

class MockProfile:
    lives_alone_profile = True
    has_caregiver = False
    is_homebound = True
    is_bedridden_profile = False
    has_social_isolation = True
    has_diabetes = True
    has_hypertension = True
    has_dyslipidemia = False
    has_heart_disease = False
    has_stroke = False
    has_cancer = False
    has_kidney_disease = False
    has_lung_disease = False
    unsafe_bathroom = True
    slippery_floor = True
    poor_lighting = False
    unsafe_stairs = False
    has_income_problems = True

class YoungHealthyCitizen:
    date_of_birth = date(2000, 1, 1)


def test_risk_high_score():
    from app.modules.risk_stratification.service import calculate_risk
    result = calculate_risk(MockCitizen(), MockProfile())
    assert result["score"] > 50
    assert result["risk_level"] in ["high", "critical"]


def test_risk_low_score():
    from app.modules.risk_stratification.service import calculate_risk
    result = calculate_risk(YoungHealthyCitizen(), None)
    assert result["score"] < 25
    assert result["risk_level"] == "low"


def test_risk_score_bounded():
    from app.modules.risk_stratification.service import calculate_risk
    result = calculate_risk(MockCitizen(), MockProfile())
    assert 0 <= result["score"] <= 100


def test_risk_levels_valid():
    from app.modules.risk_stratification.service import RISK_LEVELS
    assert "low" in RISK_LEVELS
    assert "critical" in RISK_LEVELS


def test_risk_labels_not_medical():
    from app.modules.risk_stratification.service import RISK_LABELS
    for label in RISK_LABELS.values():
        assert "disease" not in label.lower()
        assert "diagnos" not in label.lower()


# ── Population Health Forecast ────────────────────────────────────────────────

def test_forecast_linear():
    from app.modules.population_health.service import simple_forecast
    result = simple_forecast([10, 20, 30], 3)
    assert len(result) == 3
    assert result[0] == pytest.approx(40, abs=2)


def test_forecast_single_value():
    from app.modules.population_health.service import simple_forecast
    result = simple_forecast([50], 3)
    assert len(result) == 3
    assert all(r == 50 for r in result)


def test_forecast_not_clinical():
    from app.modules.population_health.service import render_population_health
    import inspect
    source = inspect.getsource(render_population_health)
    assert "diagnos" not in source.lower()
    assert "treatment" not in source.lower()


# ── Scorecard ─────────────────────────────────────────────────────────────────

def test_scorecard_overall_score():
    from app.modules.community_scorecards.service import CommunityScorecard, compute_overall_score
    sc = CommunityScorecard(
        community_id="test", community_name="Test Community",
        month=1, year=2026,
        coverage_rate=80.0, assessment_rate=70.0, home_visit_rate=75.0,
        referral_completion_rate=85.0, case_closure_rate=60.0, volunteer_activity_rate=90.0,
        created_by="test", updated_by="test",
    )
    score = compute_overall_score(sc)
    assert 60 <= score <= 90


def test_scorecard_zero_rates():
    from app.modules.community_scorecards.service import CommunityScorecard, compute_overall_score
    sc = CommunityScorecard(
        community_id="zero", community_name="Zero Community",
        month=1, year=2026,
        coverage_rate=0.0, assessment_rate=0.0, home_visit_rate=0.0,
        created_by="test", updated_by="test",
    )
    score = compute_overall_score(sc)
    assert score == 0.0


# ── Performance Management ────────────────────────────────────────────────────

def test_compute_status_achieved():
    from app.modules.performance_management.service import compute_status
    assert compute_status(100, 80) == "achieved"


def test_compute_status_on_track():
    from app.modules.performance_management.service import compute_status
    assert compute_status(76, 80) == "on_track"


def test_compute_status_at_risk():
    from app.modules.performance_management.service import compute_status
    assert compute_status(60, 80) == "at_risk"


def test_compute_status_off_track():
    from app.modules.performance_management.service import compute_status
    assert compute_status(40, 80) == "off_track"


# ── Quality Indicators ────────────────────────────────────────────────────────

def test_default_indicators_exist():
    from app.modules.quality_management.service import DEFAULT_INDICATORS
    assert len(DEFAULT_INDICATORS) >= 8
    codes = [d[0] for d in DEFAULT_INDICATORS]
    assert "QI001" in codes
    assert "QI008" in codes


def test_indicator_categories():
    from app.modules.quality_management.service import INDICATOR_CATEGORIES
    assert "coverage" in INDICATOR_CATEGORIES
    assert "assessment" in INDICATOR_CATEGORIES
    assert "referral" in INDICATOR_CATEGORIES


# ── Outcome Types ─────────────────────────────────────────────────────────────

def test_outcome_types():
    from app.modules.outcomes.service import OUTCOME_TYPES
    assert "improved" in OUTCOME_TYPES
    assert "deteriorated" in OUTCOME_TYPES
    assert "resolved" in OUTCOME_TYPES
    assert "ongoing" in OUTCOME_TYPES


# ── Integration: Risk Score ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_risk_score(session):
    from app.modules.risk_stratification.service import RiskScore
    rs = RiskScore(
        citizen_id="test-citizen-001",
        score=65.5,
        risk_level="high",
        factors="Age 80+, Lives alone, Homebound",
        calculation_date=str(date.today()),
        created_by="system", updated_by="system",
    )
    session.add(rs)
    await session.flush()
    await session.refresh(rs)
    assert rs.id is not None
    assert rs.score == 65.5
    assert rs.risk_level == "high"


@pytest.mark.asyncio
async def test_create_quality_indicator(session):
    from app.modules.quality_management.service import QualityIndicator
    qi = QualityIndicator(
        indicator_code="QI_TEST",
        indicator_name="Test Coverage Rate",
        category="coverage",
        target_value=80.0,
        unit="%",
        created_by="system", updated_by="system",
    )
    session.add(qi)
    await session.flush()
    await session.refresh(qi)
    assert qi.id is not None
    assert qi.target_value == 80.0


@pytest.mark.asyncio
async def test_create_case_outcome(session):
    from app.modules.outcomes.service import CaseOutcome
    outcome = CaseOutcome(
        case_ref="CASE-001",
        outcome_type="improved",
        baseline_value="BMI 28",
        current_value="BMI 25",
        outcome_status="closed",
        evaluation_date=str(date.today()),
        created_by="system", updated_by="system",
    )
    session.add(outcome)
    await session.flush()
    await session.refresh(outcome)
    assert outcome.id is not None
    assert outcome.outcome_type == "improved"


@pytest.mark.asyncio
async def test_create_performance_metric(session):
    from app.modules.performance_management.service import PerformanceMetric
    metric = PerformanceMetric(
        metric_name="Home Visit Rate",
        metric_category="home_visit_frequency",
        target=85.0,
        current_value=78.0,
        unit="%",
        status="at_risk",
        created_by="system", updated_by="system",
    )
    session.add(metric)
    await session.flush()
    await session.refresh(metric)
    assert metric.id is not None
    assert metric.status == "at_risk"
