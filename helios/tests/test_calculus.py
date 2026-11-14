import math

import pandas as pd

from helios.calculus import geometry, sun
from datetime import datetime

from helios.calculus.production import _derive_irradiance_scale
from helios.data.meteo import find_closest_station


def test_geometry_conversions_and_utils():
    assert math.isclose(geometry.deg2rad(180), math.pi)
    assert math.isclose(geometry.rad2deg(math.pi), 180.0)

    # normalize_angle ramène dans [0, 2pi[
    angle = 7 * math.pi
    assert math.isclose(geometry.normalize_angle(angle), math.pi)

    assert geometry.clamp(10, 0, 5) == 5

    x, y, z = geometry.vector_from_angles(math.pi / 4, math.pi / 6)
    assert math.isclose(math.sqrt(x**2 + y**2 + z**2), 1.0, rel_tol=1e-9)


def test_get_sun_position_uses_pvlib(monkeypatch):
    def fake_get_solarposition(time, latitude, longitude):
        data = {"azimuth": [180.0], "elevation": [45.0]}
        return pd.DataFrame(data)

    monkeypatch.setattr(sun.solarposition, "get_solarposition", fake_get_solarposition)

    pos = sun.get_sun_position(time="ignored", latitude=0, longitude=0)
    assert math.isclose(pos["azimuth"], math.pi)  # 180° -> pi rad
    assert math.isclose(pos["elevation"], math.pi / 4)  # 45° -> pi/4


def test_compute_irradiance_calls_pvlib(monkeypatch):
    captured = {}

    def fake_get_total_irradiance(**kwargs):
        captured.update(kwargs)
        return {"poa_global": 123.0, "poa_direct": 100.0}

    monkeypatch.setattr(
        sun.irradiance, "get_total_irradiance", fake_get_total_irradiance
    )

    result = sun.compute_irradiance(
        azimuth_sun=math.pi / 3,
        elevation_sun=math.pi / 6,
        tilt_panel=30,
        azimuth_panel=180,
        ghi=800,
        dhi=100,
        dni=600,
    )

    assert result["poa_global"] == 123.0
    # Vérifie les conversions passées à pvlib
    assert math.isclose(captured["solar_azimuth"], 60.0)  # rad -> deg
    assert math.isclose(captured["solar_zenith"], 90 - math.degrees(math.pi / 6))


"""Tests unitaires des helpers de calcul et de météo."""


def test_find_closest_station_geneva():
    station = find_closest_station(46.2, 6.1)
    assert station.code == "GVE"


def test_find_closest_station_ticino():
    station = find_closest_station(46.0, 8.95)
    assert station.code == "LUG"


def test_derive_scale_limits_high():
    ts = datetime(2024, 6, 21, 12, 0)
    weather = {"global_radiation": 2000, "timestamp": ts.isoformat()}
    scale = _derive_irradiance_scale(weather, 46.5, 6.6)
    assert 1.0 < scale <= 1.5


def test_derive_scale_limits_low():
    ts = datetime(2024, 1, 10, 12, 0)
    weather = {"global_radiation": 10, "timestamp": ts.isoformat()}
    scale = _derive_irradiance_scale(weather, 46.5, 6.6)
    assert 0.2 <= scale <= 1.0
