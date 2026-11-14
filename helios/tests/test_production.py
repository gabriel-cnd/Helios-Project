from datetime import date

import pytest

from helios.calculus import production


def test_estimate_irradiance_components_below_horizon():
    ghi, dhi = production._estimate_irradiance_components(elevation_rad=0.0)
    assert ghi == 0.0
    assert dhi == 0.0


def test_estimate_irradiance_components_clear_sky():
    ghi, dhi = production._estimate_irradiance_components(elevation_rad=1.0)
    assert ghi > 0.0
    assert 0.0 <= dhi <= ghi


def test_loss_factor_and_breakdown():
    factor = production._loss_factor(production.DEFAULT_LOSSES)
    assert 0 < factor < 1

    breakdown, final = production._compute_loss_breakdown(
        100.0, production.DEFAULT_LOSSES
    )
    assert len(breakdown) == len(production.DEFAULT_LOSSES)
    assert final < 100.0
    # chaque ligne doit diminuer l'énergie restante
    remaining_vals = [row["remaining_kwh"] for row in breakdown]
    assert remaining_vals == sorted(remaining_vals, reverse=True)


def test_simulate_energy_production_with_stubbed_sun(monkeypatch):
    # position du soleil toujours au-dessus de l'horizon
    monkeypatch.setattr(
        production,
        "get_sun_position",
        lambda *a, **k: {"azimuth": 0.5, "elevation": 0.5},
    )

    # puissance POA constante
    monkeypatch.setattr(
        production,
        "compute_irradiance",
        lambda **kwargs: {"poa_global": 100.0},
    )

    report = production.simulate_energy_production(
        latitude=46.5,
        longitude=6.6,
        tilt=30,
        azimuth=180,
        area=10.0,
        reference_date=date(2024, 6, 21),
    )

    energies = report["energies"]
    # 24 pas horaires, 100 W/m² * 10 m² = 1000 W => 1 kWh par heure => 24 kWh par jour brut
    assert energies["daily"]["raw"] == pytest.approx(24.0, rel=1e-3)
    assert energies["monthly"]["raw"] >= energies["daily"]["raw"]
    assert energies["annual"]["raw"] >= energies["monthly"]["raw"]

    assert 0 < report["net_factor"] <= 1
