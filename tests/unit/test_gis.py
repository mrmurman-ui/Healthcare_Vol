"""Unit tests — GIS map builder."""
import folium
import pytest

from app.modules.gis.service import elderly_heatmap, household_map


class FakeHousehold:
    def __init__(self, code, lat, lon, head=None):
        self.household_code = code
        self.latitude = lat
        self.longitude = lon
        self.head_of_household = head


def test_household_map_returns_folium_map():
    households = [
        FakeHousehold("HH001", 18.788, 98.985, "สมชาย"),
        FakeHousehold("HH002", 18.790, 98.987),
    ]
    m = household_map(households)
    assert isinstance(m, folium.Map)


def test_household_map_empty():
    m = household_map([])
    assert isinstance(m, folium.Map)


def test_household_map_skips_null_coords():
    households = [
        FakeHousehold("HH001", None, None),
        FakeHousehold("HH002", 18.788, 98.985),
    ]
    m = household_map(households)
    assert isinstance(m, folium.Map)


def test_elderly_heatmap_returns_folium_map():
    households = [FakeHousehold("HH001", 18.788, 98.985)]
    m = elderly_heatmap(households)
    assert isinstance(m, folium.Map)


def test_elderly_heatmap_empty():
    m = elderly_heatmap([])
    assert isinstance(m, folium.Map)
