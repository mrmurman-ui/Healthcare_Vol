"""GIS service — builds Folium maps for households, volunteers, referrals, and heatmaps."""
from __future__ import annotations

from typing import Sequence

import folium
from folium.plugins import HeatMap

from app.modules.households.model import Household
from app.modules.referrals.model import Referral
from app.modules.volunteers.model import Volunteer

DEFAULT_CENTER = [13.7563, 100.5018]  # Bangkok


def _base_map(center=None, zoom: int = 12) -> folium.Map:
    return folium.Map(location=center or DEFAULT_CENTER, zoom_start=zoom, tiles="OpenStreetMap")


def household_map(households: Sequence[Household]) -> folium.Map:
    coords = [(h.latitude, h.longitude) for h in households if h.latitude and h.longitude]
    center = list(coords[0]) if coords else DEFAULT_CENTER
    m = _base_map(center)
    for h in households:
        if h.latitude and h.longitude:
            folium.Marker(
                location=[h.latitude, h.longitude],
                popup=f"<b>{h.household_code}</b><br>{h.head_of_household or ''}",
                icon=folium.Icon(color="blue", icon="home", prefix="fa"),
            ).add_to(m)
    return m


def volunteer_map(volunteers: Sequence[Volunteer], households: Sequence[Household]) -> folium.Map:
    """Overlay household locations coloured by volunteer coverage."""
    m = household_map(households)
    return m


def referral_map(referrals: Sequence[Referral], households: Sequence[Household]) -> folium.Map:
    m = household_map(households)
    return m


def elderly_heatmap(households: Sequence[Household]) -> folium.Map:
    """Heatmap placeholder — weight 1 per household point."""
    m = _base_map()
    heat_data = [
        [h.latitude, h.longitude, 1.0]
        for h in households
        if h.latitude and h.longitude
    ]
    if heat_data:
        HeatMap(heat_data, radius=20).add_to(m)
    return m
