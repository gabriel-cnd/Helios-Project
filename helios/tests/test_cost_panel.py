import importlib
import sys
import types

import pandas as pd
import pytest


def _load_module():
    # stub pour l'import helios.interface.ui absent
    sys.modules["helios.interface.ui"] = types.SimpleNamespace(data=None)
    return importlib.reload(importlib.import_module("helios.economics.cost_panel"))


def test_load_panels_and_surface_needed(tmp_path):
    mod = _load_module()
    csv = tmp_path / "panels.csv"
    pd.DataFrame(
        [
            {"Nom": "P1", "Puissance": 300, "Surface": 1.6, "Prix": 120},
            {"Nom": "P2", "Puissance": 400, "Surface": 1.8, "Prix": 150},
        ]
    ).to_csv(csv, index=False)

    panels = mod.CostPanel().load_panels(str(csv))
    assert "P1" in panels and "P2" in panels

    res = mod.CostPanel.surface_needed(
        installed_power_kw=3, panel_power_w=300, panel_area_m2=1.6
    )
    assert res["required_panels"] >= 1
    assert res["total_area_m2"] > 0

    with pytest.raises(ValueError):
        mod.CostPanel.surface_needed(
            installed_power_kw=1, panel_power_w=0, panel_area_m2=1
        )


def test_find_best_panel(tmp_path):
    mod = _load_module()
    csv = tmp_path / "panels.csv"
    pd.DataFrame(
        [
            {"Nom": "Cheap", "Puissance": 300, "Surface": 1.6, "Prix": 50},
            {"Nom": "Expensive", "Puissance": 300, "Surface": 1.6, "Prix": 500},
        ]
    ).to_csv(csv, index=False)

    panels = mod.CostPanel().load_panels(str(csv))
    best = mod.CostPanel.find_best_panel(installed_power_kw=1, panels=panels)
    assert best["best_panel"] == "Cheap"
