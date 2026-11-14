"""
Implémente un contrôleur PID simple avec protections basiques
anti-windup et saturation de la sortie.
"""


class PIDController:
    def __init__(
        self,
        kp: float,
        ki: float,
        kd: float,
        *,
        integral_limits: tuple[float | None, float | None] = (None, None),
        output_limits: tuple[float | None, float | None] = (None, None),
    ):
        self.kp = kp  # Gain proportionnel
        self.ki = ki  # Gain intégral
        self.kd = kd  # Gain dérivé
        self.integral_limits = integral_limits
        self.output_limits = output_limits
        self.previous_error = 0.0
        self.integral = 0.0

    @staticmethod
    def _clamp(value: float, min_val: float | None, max_val: float | None) -> float:
        if min_val is not None and value < min_val:
            return min_val
        if max_val is not None and value > max_val:
            return max_val
        return value

    def reset(self) -> None:
        """Réinitialise l'état interne du PID."""
        self.previous_error = 0.0
        self.integral = 0.0

    def compute(self, setpoint: float, measured_value: float, dt: float) -> float:
        """
        Calcule la sortie du contrôleur PID.

        :param setpoint: consigne cible.
        :param measured_value: mesure actuelle.
        :param dt: pas de temps écoulé (s).
        :return: sortie PID saturée si output_limits est défini.
        """
        if dt <= 0:
            raise ValueError("dt must be positive to compute PID output")

        error = setpoint - measured_value

        proportional = self.kp * error

        self.integral += error * dt
        self.integral = self._clamp(self.integral, *self.integral_limits)
        integral = self.ki * self.integral

        derivative = self.kd * (error - self.previous_error) / dt
        self.previous_error = error

        output = proportional + integral + derivative
        output = self._clamp(output, *self.output_limits)
        return output


# Exemple d'utilisation
if __name__ == "__main__":
    pid = PIDController(
        kp=1.0, ki=0.1, kd=0.05, integral_limits=(-10, 10), output_limits=(-50, 50)
    )
    setpoint = 10.0  # Valeur cible
    measured_value = 0.0  # Valeur initiale
    dt = 0.1  # Intervalle de temps

    for _ in range(100):
        output = pid.compute(setpoint, measured_value, dt)
        measured_value += output * dt  # Simuler la réponse du système
        print(f"Measured Value: {measured_value:.2f}, PID Output: {output:.2f}")
