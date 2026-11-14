"""Client minimal pour récupérer des données MeteoSwiss.

Ce module encapsule la logique de sélection d'une station proche,
interroge l'API publique utilisée par l'application MeteoSwiss et
retourne un dictionnaire homogène contenant les mesures utiles à la
simulation PV (irradiance globale, température, etc.).

En environnement hors-ligne ou si l'appel HTTP échoue, un fallback basé
sur un ciel clair simple est renvoyé pour éviter de casser l'IHM.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional
import csv
import math
from pathlib import Path

import requests

from helios.calculus.sun import get_sun_position


@dataclass(slots=True)
class Station:
    code: str
    name: str
    latitude: float
    longitude: float
    altitude: float | None = None


_DEFAULT_STATIONS: tuple[Station, ...] = (
    Station("GVE", "Genève Cointrin", 46.25, 6.13, 420),
    Station("BER", "Bern Zollikofen", 46.99, 7.46, 552),
    Station("BAS", "Bâle/EuroAirport", 47.59, 7.63, 316),
    Station("ZRH", "Zürich Fluntern", 47.38, 8.56, 556),
    Station("LUG", "Lugano", 46.00, 8.96, 273),
    Station("DAV", "Davos", 46.81, 9.84, 1594),
)


def _load_stations_from_csv(path: Path) -> tuple[Station, ...]:
    stations: list[Station] = []
    try:
        with path.open(newline="", encoding="latin-1") as handle:
            reader = csv.DictReader(handle, delimiter=";")
            for row in reader:
                code = (row.get("station_abbr") or "").strip()
                name = (row.get("station_name") or "").strip()
                lat = row.get("station_coordinates_wgs84_lat")
                lon = row.get("station_coordinates_wgs84_lon")
                if not code or not name or not lat or not lon:
                    continue
                try:
                    latitude = float(lat)
                    longitude = float(lon)
                except ValueError:
                    continue
                alt_raw = row.get("station_height_masl") or ""
                try:
                    altitude = float(alt_raw) if alt_raw else None
                except ValueError:
                    altitude = None
                stations.append(
                    Station(
                        code=code,
                        name=name,
                        latitude=latitude,
                        longitude=longitude,
                        altitude=altitude,
                    )
                )
    except FileNotFoundError:
        return ()
    except Exception:
        return ()
    return tuple(stations)


_CSV_PATH = Path(__file__).with_name("ogd-smn_meta_stations.csv")
_CSV_STATIONS = _load_stations_from_csv(_CSV_PATH)
SWISS_METNET_STATIONS: tuple[Station, ...] = _CSV_STATIONS or _DEFAULT_STATIONS


def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Retourne la distance approximative (km) entre deux points."""

    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return 2 * r * math.asin(math.sqrt(a))


def find_closest_station(
    lat: float, lon: float, stations: Iterable[Station] = SWISS_METNET_STATIONS
) -> Station:
    """Sélectionne la station la plus proche des coordonnées fournies."""

    return min(
        stations, key=lambda s: _haversine_distance(lat, lon, s.latitude, s.longitude)
    )


class MeteoSwissError(RuntimeError):
    """Erreur levée lors de l'accès MeteoSwiss."""


class MeteoSwissClient:
    def __init__(
        self,
        *,
        lang: str = "fr",
        base_url: str = "https://app-prod-ws.meteoswiss.ch/v1/plasma/rest",
        timeout: int = 10,
        session: Optional[requests.Session] = None,
        allow_fallback: bool = True,
    ) -> None:
        self.lang = lang
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()
        self.allow_fallback = allow_fallback

    def fetch_weather(
        self,
        latitude: float,
        longitude: float,
        *,
        when: Optional[datetime] = None,
        station: Optional[Station] = None,
    ) -> Dict[str, Any]:
        """Récupère les mesures météo normalisées."""

        when = when or datetime.now(timezone.utc).astimezone().replace(tzinfo=None)
        station = station or find_closest_station(latitude, longitude)

        params = {"station": station.code, "lang": self.lang}
        try:
            payload = self._request("stationdata", params)
            return self._normalise_payload(payload, station)
        except Exception as exc:  # noqa: BLE001 - on encapsule pour fallback
            if not self.allow_fallback:
                raise MeteoSwissError("Échec de récupération MeteoSwiss") from exc
            return self._synthetic_payload(latitude, longitude, when, station, exc)

    # -------------------------
    #       HTTP UTILITIES
    # -------------------------
    def _request(
        self, path: str, params: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        response = self.session.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    # -------------------------
    #     DATA NORMALISATION
    # -------------------------
    def _normalise_payload(
        self, payload: dict[str, Any], station: Station
    ) -> dict[str, Any]:
        measures = payload.get("measurements") or payload.get("stationdata") or payload

        def pick(*names: str) -> Optional[float]:
            for name in names:
                value = measures.get(name)
                if value is None:
                    continue
                if isinstance(value, dict):
                    value = value.get("value", value.get("data"))
                try:
                    return float(value)
                except (TypeError, ValueError):
                    continue
            return None

        timestamp = self._parse_timestamp(
            payload.get("timestamp")
            or payload.get("date")
            or payload.get("time")
            or measures.get("time")
        )

        return {
            "station": {
                "id": station.code,
                "name": station.name,
                "latitude": station.latitude,
                "longitude": station.longitude,
                "altitude": station.altitude,
            },
            "timestamp": timestamp.isoformat() if timestamp else None,
            "temperature": pick("temperature", "tre200s0"),
            "relative_humidity": pick("humidity", "ure200s0"),
            "wind_speed": pick("windSpeed", "fu3010z0"),
            "wind_direction": pick("windDirection", "dkl010z0"),
            "global_radiation": pick("globalRadiation", "gre000z0"),
            "raw": payload,
            "source": "meteoswiss",
        }

    @staticmethod
    def _parse_timestamp(value: Any) -> Optional[datetime]:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(float(value), tz=timezone.utc)
        if isinstance(value, str):
            for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y%m%d%H%M"):
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
        if isinstance(value, datetime):
            return value
        return None

    # -------------------------
    #          FALLBACK
    # -------------------------
    def _synthetic_payload(
        self,
        latitude: float,
        longitude: float,
        when: datetime,
        station: Station,
        error: Exception,
    ) -> dict[str, Any]:
        pos = get_sun_position(when, latitude, longitude)
        elevation = max(0.0, pos["elevation"])
        ghi = max(0.0, 1000.0 * math.sin(elevation))
        return {
            "station": {
                "id": station.code,
                "name": station.name,
                "latitude": latitude,
                "longitude": longitude,
            },
            "timestamp": when.isoformat(),
            "temperature": 20.0 - 10.0 * math.cos((when.hour / 24) * 2 * math.pi),
            "relative_humidity": 50.0,
            "wind_speed": 2.0,
            "wind_direction": None,
            "global_radiation": ghi,
            "source": "synthetic-clear-sky",
            "error": str(error),
        }


__all__ = [
    "MeteoSwissClient",
    "MeteoSwissError",
    "Station",
    "find_closest_station",
]
