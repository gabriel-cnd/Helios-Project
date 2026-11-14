import pandas as pd
import pytest

from helios.economics.cost_ond import OptimalInverter


def test_select_optimal_inverter(tmp_path):
    csv = tmp_path / "ond.csv"
    pd.DataFrame(
        [
            {"Puissance": 10, "Rendement": 0.95, "Coût": 1000, "Fiabilité": 0.9},
            {"Puissance": 12, "Rendement": 0.90, "Coût": 800, "Fiabilité": 0.8},
            {"Puissance": 5, "Rendement": 0.99, "Coût": 500, "Fiabilité": 0.7},
        ]
    ).to_csv(csv, index=False)

    inv = OptimalInverter(csv_path=str(csv))
    project_specs = {"power_kwh": 10}
    result = inv.select_optimal(project_specs, cost_panel_results={})

    assert result["Puissance"] >= 8  # dans la plage 80-120 % de 10
    assert "score" in result


def test_select_optimal_inverter_no_match(tmp_path):
    csv = tmp_path / "ond.csv"
    pd.DataFrame(
        [
            {"Puissance": 1, "Rendement": 0.9, "Coût": 100, "Fiabilité": 0.9},
        ]
    ).to_csv(csv, index=False)

    inv = OptimalInverter(csv_path=str(csv))
    with pytest.raises(ValueError):
        inv.select_optimal({"power_kwh": 20}, cost_panel_results={})
