"""
Boucle de contrôle des axes azimut / inclinaison.
Inclut un clamp sur les limites mécaniques pour éviter des valeurs irréalistes.
"""

from helios.regul.pid import PIDController


def _clamp(value: float, min_val: float | None, max_val: float | None) -> float:
    if min_val is not None and value < min_val:
        return min_val
    if max_val is not None and value > max_val:
        return max_val
    return value


class MotorEngine:
    def __init__(
        self,
        azimuth_pid: PIDController,
        tilt_pid: PIDController,
        *,
        azimuth_limits: tuple[float | None, float | None] = (0.0, 180.0),
        tilt_limits: tuple[float | None, float | None] = (0.0, 90.0),
    ):
        self.azimuth_pid = azimuth_pid
        self.tilt_pid = tilt_pid
        self.azimuth_limits = azimuth_limits
        self.tilt_limits = tilt_limits
        self.current_azimuth = 0.0
        self.current_tilt = 0.0

    def reset(self) -> None:
        """Réinitialise les positions simulées et l'état PID."""
        self.current_azimuth = 0.0
        self.current_tilt = 0.0
        self.azimuth_pid.reset()
        self.tilt_pid.reset()

    def set_azimuth(self, target_azimuth: float, dt: float) -> float:
        """
        Met à jour la position en azimut en utilisant le PID et applique les limites.
        """
        output = self.azimuth_pid.compute(target_azimuth, self.current_azimuth, dt)
        self.current_azimuth = _clamp(
            self.current_azimuth + output * dt, *self.azimuth_limits
        )
        return self.current_azimuth

    def set_tilt(self, target_tilt: float, dt: float) -> float:
        """
        Met à jour la position en inclinaison en utilisant le PID et applique les limites.
        """
        output = self.tilt_pid.compute(target_tilt, self.current_tilt, dt)
        self.current_tilt = _clamp(self.current_tilt + output * dt, *self.tilt_limits)
        return self.current_tilt


# Exemple d'utilisation
if __name__ == "__main__":
    azimuth_pid = PIDController(
        kp=1.0, ki=0.1, kd=0.05, integral_limits=(-20, 20), output_limits=(-50, 50)
    )
    tilt_pid = PIDController(
        kp=1.2, ki=0.15, kd=0.07, integral_limits=(-20, 20), output_limits=(-50, 50)
    )
    motor_engine = MotorEngine(azimuth_pid, tilt_pid)

    target_azimuth = 90.0  # Position cible en azimut
    target_tilt = 45.0  # Position cible en inclinaison
    dt = 0.1  # Intervalle de temps

    for _ in range(100):
        new_azimuth = motor_engine.set_azimuth(target_azimuth, dt)
        new_tilt = motor_engine.set_tilt(target_tilt, dt)
        print(f"Azimuth: {new_azimuth:.2f}, Tilt: {new_tilt:.2f}")
