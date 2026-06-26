"""Unit tests — localization service."""
from unittest.mock import MagicMock, patch

import pytest

from app.modules.localization.service import TRANSLATIONS, set_locale, t


@pytest.fixture(autouse=True)
def mock_session_state():
    """Patch st.session_state so tests can run without Streamlit."""
    state = {}
    with patch("app.modules.localization.service.st") as mock_st:
        mock_st.session_state = state
        yield state


def test_default_locale_is_thai(mock_session_state):
    assert t("save") == TRANSLATIONS["th"]["save"]


def test_english_locale(mock_session_state):
    mock_session_state["locale"] = "en"
    assert t("save") == "Save"


def test_thai_locale(mock_session_state):
    mock_session_state["locale"] = "th"
    assert t("save") == "บันทึก"


def test_missing_key_returns_key(mock_session_state):
    mock_session_state["locale"] = "th"
    assert t("nonexistent_key_xyz") == "nonexistent_key_xyz"


def test_all_thai_keys_have_english_equivalent():
    for key in TRANSLATIONS["th"]:
        assert key in TRANSLATIONS["en"], f"Missing English translation for key: {key}"


def test_set_locale(mock_session_state):
    set_locale("en")
    assert mock_session_state["locale"] == "en"
