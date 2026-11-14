"""
Orchestrateur qui calcule les consignes (azimut/inclinaison) à partir
de la position solaire et pilote les PID + limites mécaniques.
"""

from helios.calculus.geometry import rad2deg
from helios.calculus.sun import get_sun_position
from helios.data.loader import load_config
from helios.regul.engine import MotorEngine
from helios.regul.pid import PIDController


def _extract_limits(limit_section: dict | None) -> tuple[float | None, float | None]:
    """Helper to turn a {min, max} dict into a tuple usable by MotorEngine."""
    if not limit_section:
        return (None, None)
    return (limit_section.get("min"), limit_section.get("max"))


class OrientationEngine:
    def __init__(self, config: dict | None = None):
        cfg = config or load_config()

        pid_params_azimuth = cfg["pid"]["azimuth"]
        pid_params_tilt = cfg["pid"]["elevation"]

        azimuth_pid = PIDController(
            kp=pid_params_azimuth["kp"],
            ki=pid_params_azimuth["ki"],
            kd=pid_params_azimuth["kd"],
            integral_limits=tuple(
                pid_params_azimuth.get("integral_limits", (None, None))
            ),
            output_limits=tuple(pid_params_azimuth.get("output_limits", (None, None))),
        )

        tilt_pid = PIDController(
            kp=pid_params_tilt["kp"],
            ki=pid_params_tilt["ki"],
            kd=pid_params_tilt["kd"],
            integral_limits=tuple(pid_params_tilt.get("integral_limits", (None, None))),
            output_limits=tuple(pid_params_tilt.get("output_limits", (None, None))),
        )

        mech_limits = cfg.get("mechanical_limits", {})
        self.engine = MotorEngine(
            azimuth_pid=azimuth_pid,
            tilt_pid=tilt_pid,
            azimuth_limits=_extract_limits(mech_limits.get("azimuth")),
            tilt_limits=_extract_limits(mech_limits.get("elevation")),
        )

        self.latitude = cfg["latitude"]
        self.longitude = cfg["longitude"]

    def compute_targets(self, time) -> tuple[float, float]:
        pos = get_sun_position(time, self.latitude, self.longitude)
        sun_azimuth_deg = rad2deg(pos["azimuth"])
        sun_elevation_deg = rad2deg(pos["elevation"])

        target_azimuth = sun_azimuth_deg
        target_tilt = 90.0 - sun_elevation_deg  # simple two-axis tracking
        return target_azimuth, target_tilt

    def apply_limits(
        self, value: float, limits: tuple[float | None, float | None]
    ) -> float:
        min_limit, max_limit = limits
        if min_limit is not None:
            value = max(value, min_limit)
        if max_limit is not None:
            value = min(value, max_limit)
        return value

    def update(self, time, dt: float) -> dict[str, float]:
        target_azimuth, target_tilt = self.compute_targets(time)

        target_azimuth = self.apply_limits(target_azimuth, self.engine.azimuth_limits)
        target_tilt = self.apply_limits(target_tilt, self.engine.tilt_limits)

        current_azimuth = self.engine.set_azimuth(target_azimuth, dt)
        current_tilt = self.engine.set_tilt(target_tilt, dt)

        return {
            "current_azimuth": current_azimuth,
            "current_tilt": current_tilt,
            "target_azimuth": target_azimuth,
            "target_tilt": target_tilt,
        }

    def get_state(self) -> dict[str, float]:
        return {
            "current_azimuth": self.engine.current_azimuth,
            "current_tilt": self.engine.current_tilt,
        }


# Exemple d'utilisation
if __name__ == "__main__":
    from datetime import datetime, timedelta

    orientation_engine = OrientationEngine()
    orientation_engine.engine.reset()

    start_time = datetime.utcnow()
    dt = 1.0  # 1 seconde

    for step in range(10):
        current_time = start_time + timedelta(seconds=step * dt)
        state = orientation_engine.update(current_time, dt)
        print(f"Time: {current_time}, State: {state}")
