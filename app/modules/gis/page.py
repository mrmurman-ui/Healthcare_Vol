import streamlit as st
from sqlalchemy import select
from streamlit_folium import st_folium

from app.core.db_sync import get_sync_db
from app.modules.gis.service import elderly_heatmap, household_map
from app.modules.households.model import Household
from app.modules.localization.service import t


def _t(th: str, en: str) -> str:
    return th if st.session_state.get("lang", "TH") == "TH" else en


def render_gis() -> None:
    st.header(t("nav_gis"))

    map_type = st.selectbox(_t("ประเภทแผนที่","Map Type"), [_t("แผนที่ครัวเรือน","Household Map"), _t("Heatmap ผู้สูงอายุ","Elderly Heatmap")])

    with get_sync_db() as db:
        households = db.execute(
            select(Household).where(
                Household.latitude.isnot(None),
                Household.longitude.isnot(None),
            )
        ).scalars().all()

    m = household_map(households) if map_type == _t("แผนที่ครัวเรือน","Household Map") else elderly_heatmap(households)
    try:
        st_folium(m, width=900, height=550, key="gis_map")
    except Exception as _e:
        st.error(f"Map error: {_e}")
