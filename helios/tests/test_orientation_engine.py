import math

from helios.regul.orientation_engine import OrientationEngine


def _make_config():
    return {
        "pid": {
            "azimuth": {"kp": 1.0, "ki": 0.0, "kd": 0.0},
            "elevation": {"kp": 1.0, "ki": 0.0, "kd": 0.0},
        },
        "mechanical_limits": {
            "azimuth": {"min": 0.0, "max": 180.0},
            "elevation": {"min": 0.0, "max": 90.0},
        },
        "latitude": 46.5,
        "longitude": 6.6,
    }


def test_compute_targets(monkeypatch):
    cfg = _make_config()

    monkeypatch.setattr(
        "helios.regul.orientation_engine.get_sun_position",
        lambda *a, **k: {"azimuth": math.pi / 2, "elevation": math.pi / 6},  # 90°, 30°
    )

    engine = OrientationEngine(config=cfg)
    az, tilt = engine.compute_targets(time=None)
    assert math.isclose(az, 90.0)
    assert math.isclose(tilt, 60.0)  # 90 - elevation


def test_apply_limits_and_update(monkeypatch):
    cfg = _make_config()
    # soleil avec forte élévation pour tester clamp tilt
    monkeypatch.setattr(
        "helios.regul.orientation_engine.get_sun_position",
        lambda *a, **k: {
            "azimuth": math.pi,
            "elevation": math.radians(80),
        },  # az=180°, el=80°
    )

    engine = OrientationEngine(config=cfg)
    state = engine.update(time=None, dt=1.0)

    # azimut doit être 180 max, tilt 10° (90-80)
    assert state["target_azimuth"] == 180.0
    assert state["target_tilt"] == 10.0
    assert 0.0 <= state["current_azimuth"] <= 180.0
    assert 0.0 <= state["current_tilt"] <= 90.0
