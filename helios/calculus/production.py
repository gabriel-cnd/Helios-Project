"""Utility helpers pour la simulation de production énergétique.

Le module propose un calcul *très* simplifié de l'énergie produite à
partir de la géométrie du champ PV et de la position solaire déjà
disponible dans :mod:`helios.calculus.sun`.

Objectifs couverts :
    * Intégration horaire d'une journée, d'un mois et d'une année.
    * Application de pertes système typiques (inverter, câbles, etc.).
    * Fourniture d'un tableau de pertes façon PVsyst.

Ce module n'a pas vocation à remplacer une chaîne de calcul PV complète
mais fournit un ordre de grandeur instantané directement exploitable
dans l'interface graphique.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Iterable, List, Optional

import numpy as np

from helios.calculus.sun import compute_irradiance, get_sun_position


@dataclass(slots=True)
class LossItem:
    """Représente un poste de pertes fractionnel."""

    name: str
    fraction: float  # 0.02 -> 2 %

    def as_percent(self) -> float:
        return max(0.0, self.fraction) * 100.0


# Valeurs issues d'un diagramme de pertes typique PVsyst.
DEFAULT_LOSSES: List[LossItem] = [
    LossItem("Encrassement (soiling)", 0.02),
    LossItem("Mismatch modules", 0.015),
    LossItem("Pertes câbles DC", 0.02),
    LossItem("Pertes câbles AC", 0.01),
    LossItem("Température modules", 0.08),
    LossItem("Rendement onduleur", 0.04),
]


def _hourly_datetimes(
    start: datetime, end: datetime, step_hours: int = 1
) -> Iterable[datetime]:
    """Génère les pas horaires entre *start* (inclus) et *end* (exclus)."""

    step = timedelta(hours=step_hours)
    current = start
    while current < end:
        yield current
        current += step


def _estimate_irradiance_components(elevation_rad: float) -> tuple[float, float]:
    """Estime une GHI/DHI claire à partir de l'élévation solaire."""

    if elevation_rad <= 0.0:
        return 0.0, 0.0

    sin_el = float(np.sin(elevation_rad))
    ghi = max(0.0, 1000.0 * sin_el)
    # On suppose 20 % de diffus, borné afin d'éviter un dépassement.
    dhi = min(ghi * 0.6, ghi * 0.2 + 30.0)
    return ghi, dhi


def _integrate_energy(
    latitude: float,
    longitude: float,
    tilt: float,
    azimuth: float,
    area: float,
    start: datetime,
    end: datetime,
    scale_factor: float = 1.0,
) -> float:
    """Somme l'énergie (kWh) produite entre *start* et *end*."""

    total_wh = 0.0
    for instant in _hourly_datetimes(start, end):
        pos = get_sun_position(instant, latitude, longitude)
        elevation = pos["elevation"]
        if elevation <= 0.0:
            continue

        ghi, dhi = _estimate_irradiance_components(elevation)
        if ghi <= 0.0:
            continue

        irr = compute_irradiance(
            azimuth_sun=pos["azimuth"],
            elevation_sun=elevation,
            tilt_panel=tilt,
            azimuth_panel=azimuth,
            ghi=ghi,
            dhi=dhi,
        )
        poa = max(0.0, float(irr.get("poa_global", 0.0)))
        # poa [W/m²] * surface [m²] donne la puissance DC en W.
        total_wh += poa * area * scale_factor  # 1 h par pas temporel

    return total_wh / 1000.0  # conversion Wh -> kWh


def _loss_factor(losses: Iterable[LossItem]) -> float:
    """Produit des rendements résiduels (1 - pertes)."""

    factor = 1.0
    for loss in losses:
        factor *= max(0.0, 1.0 - loss.fraction)
    return factor


def _compute_loss_breakdown(energy_kwh: float, losses: Iterable[LossItem]):
    """Retourne la table de pertes appliquée à *energy_kwh*."""

    breakdown = []
    remaining = energy_kwh
    for loss in losses:
        loss_value = remaining * max(0.0, loss.fraction)
        remaining -= loss_value
        breakdown.append(
            {
                "name": loss.name,
                "percent": loss.as_percent(),
                "loss_kwh": loss_value,
                "remaining_kwh": max(0.0, remaining),
            }
        )
    return breakdown, max(0.0, remaining)


def _as_date(value: date | datetime | None) -> date:
    if value is None:
        return datetime.now().date()
    if isinstance(value, datetime):
        return value.date()
    return value


def _parse_weather_timestamp(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _derive_irradiance_scale(
    weather_data: Optional[dict], latitude: float, longitude: float
) -> float:
    """Calcule un facteur d'échelle basé sur la GHI mesurée."""

    if not weather_data:
        return 1.0

    measured = weather_data.get("global_radiation")
    if measured is None:
        return 1.0

    timestamp = _parse_weather_timestamp(weather_data.get("timestamp"))
    if not timestamp:
        timestamp = datetime.now()

    pos = get_sun_position(timestamp, latitude, longitude)
    synthetic = max(0.0, 1000.0 * np.sin(max(0.0, pos["elevation"])))
    if synthetic <= 1e-3:
        return 1.0

    scale = float(measured) / synthetic
    return float(max(0.2, min(1.5, scale)))


def simulate_energy_production(
    latitude: float,
    longitude: float,
    tilt: float,
    azimuth: float,
    area: float,
    reference_date: date | datetime | None = None,
    losses: Iterable[LossItem] | None = None,
    weather_data: Optional[dict] = None,
):
    """Calcule l'énergie journalière, mensuelle et annuelle (kWh).

    :returns: dictionnaire contenant les énergies "raw" (DC avant pertes),
        les valeurs nettes et un diagramme de pertes annuel.
    """

    ref_date = _as_date(reference_date)
    area = max(0.1, float(area))  # évite les surfaces nulles
    losses = list(losses) if losses is not None else list(DEFAULT_LOSSES)

    day_start = datetime(ref_date.year, ref_date.month, ref_date.day)
    day_end = day_start + timedelta(days=1)

    month_start = datetime(ref_date.year, ref_date.month, 1)
    if ref_date.month == 12:
        month_end = datetime(ref_date.year + 1, 1, 1)
    else:
        month_end = datetime(ref_date.year, ref_date.month + 1, 1)

    year_start = datetime(ref_date.year, 1, 1)
    year_end = datetime(ref_date.year + 1, 1, 1)

    scale_factor = _derive_irradiance_scale(weather_data, latitude, longitude)

    daily = _integrate_energy(
        latitude,
        longitude,
        tilt,
        azimuth,
        area,
        day_start,
        day_end,
        scale_factor=scale_factor,
    )
    monthly = _integrate_energy(
        latitude,
        longitude,
        tilt,
        azimuth,
        area,
        month_start,
        month_end,
        scale_factor=scale_factor,
    )
    annual = _integrate_energy(
        latitude,
        longitude,
        tilt,
        azimuth,
        area,
        year_start,
        year_end,
        scale_factor=scale_factor,
    )

    factor = _loss_factor(losses)
    energies = {
        "daily": {"raw": daily, "net": daily * factor},
        "monthly": {"raw": monthly, "net": monthly * factor},
        "annual": {"raw": annual, "net": annual * factor},
    }

    loss_table, final_energy = _compute_loss_breakdown(annual, losses)

    return {
        "energies": energies,
        "losses": loss_table,
        "final_annual_energy": final_energy,
        "net_factor": factor,
        "weather": weather_data,
    }


__all__ = [
    "LossItem",
    "DEFAULT_LOSSES",
    "simulate_energy_production",
]
