import pytest

from helios.regul.pid import PIDController


def test_pid_basic_output_and_reset():
    pid = PIDController(kp=2.0, ki=0.5, kd=0.0, output_limits=(-10, 10))
    output = pid.compute(setpoint=5.0, measured_value=0.0, dt=1.0)
    assert -10 <= output <= 10

    pid.reset()
    assert pid.previous_error == 0.0
    assert pid.integral == 0.0


def test_pid_integral_and_output_clamp():
    pid = PIDController(
        kp=0.0,
        ki=1.0,
        kd=0.0,
        integral_limits=(-1.0, 1.0),
        output_limits=(-2.0, 2.0),
    )
    # erreur constante de 5 pendant 1s -> intégrale serait 5 mais clampée à 1
    output = pid.compute(setpoint=5.0, measured_value=0.0, dt=1.0)
    assert output == pytest.approx(1.0)

    # erreur négative, intégrale descend jusqu'à -1 (clamp)
    output = pid.compute(setpoint=-5.0, measured_value=0.0, dt=1.0)
    assert output == pytest.approx(-1.0)  # intégrale clampée


def test_pid_requires_positive_dt():
    pid = PIDController(1.0, 0.0, 0.0)
    with pytest.raises(ValueError):
        pid.compute(setpoint=1.0, measured_value=0.0, dt=0)
