import pandas as pd
from typing import Dict


def find_optimal_battery(
    pv_power_kw: float,
    daily_consumption_kwh: float,
    onduleur_cost: float,
    panel_cost: float,
    batteries_data_path: str = "comparatif_batteries.csv",
) -> Dict:
    """
    Trouve la batterie la plus optimale pour une installation PV spécifiée.

    Args:
        pv_power_kw: Puissance PV en kW
        daily_consumption_kwh: Consommation quotidienne en kWh
        onduleur_cost: Coût de l'onduleur (€)
        panel_cost: Coût total des panneaux (€)
        batteries_data_path: Chemin vers le fichier de comparatif batteries

    Returns:
        Dict contenant la batterie optimale et ses caractéristiques
    """

    # Charger les données des batteries
    batteries_df = pd.read_csv(batteries_data_path)

    # Calculer la capacité nécessaire (avec marge de 20%)
    required_capacity = daily_consumption_kwh * 1.2

    # Filtrer les batteries compatibles
    compatible_batteries = batteries_df[
        batteries_df["capacity_kwh"] >= required_capacity
    ].copy()

    if compatible_batteries.empty:
        return {"error": "Aucune batterie compatible trouvée"}

    # Calculer le coût total par batterie
    compatible_batteries["total_cost"] = (
        onduleur_cost + panel_cost + compatible_batteries["price_eur"]
    )

    # Calculer le coût par kWh stocké
    compatible_batteries["cost_per_kwh"] = (
        compatible_batteries["total_cost"] / compatible_batteries["capacity_kwh"]
    )

    # Trouver la batterie optimale (meilleur rapport coût/performance)
    optimal_idx = compatible_batteries["cost_per_kwh"].idxmin()
    optimal_battery = compatible_batteries.loc[optimal_idx]

    return {
        "battery_model": optimal_battery["model"],
        "capacity_kwh": optimal_battery["capacity_kwh"],
        "price_eur": optimal_battery["price_eur"],
        "total_installation_cost": optimal_battery["total_cost"],
        "cost_per_kwh": round(optimal_battery["cost_per_kwh"], 2),
        "efficiency": optimal_battery.get("efficiency_percent", "N/A"),
        "warranty_years": optimal_battery.get("warranty_years", "N/A"),
    }
