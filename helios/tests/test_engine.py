from helios.regul.engine import MotorEngine
from helios.regul.pid import PIDController


def test_motor_engine_respects_limits():
    az_pid = PIDController(kp=1.0, ki=0.0, kd=0.0)
    tilt_pid = PIDController(kp=1.0, ki=0.0, kd=0.0)
    engine = MotorEngine(
        azimuth_pid=az_pid,
        tilt_pid=tilt_pid,
        azimuth_limits=(0.0, 180.0),
        tilt_limits=(0.0, 90.0),
    )

    # cible très haute -> clamp sur la limite mécanique
    new_az = engine.set_azimuth(target_azimuth=400.0, dt=1.0)
    assert new_az == 180.0

    new_tilt = engine.set_tilt(target_tilt=200.0, dt=1.0)
    assert new_tilt == 90.0


def test_motor_engine_reset():
    az_pid = PIDController(kp=1.0, ki=0.1, kd=0.0, integral_limits=(-5, 5))
    tilt_pid = PIDController(kp=1.0, ki=0.1, kd=0.0, integral_limits=(-5, 5))
    engine = MotorEngine(az_pid, tilt_pid)

    engine.set_azimuth(target_azimuth=90.0, dt=1.0)
    engine.set_tilt(target_tilt=30.0, dt=1.0)
    engine.reset()

    assert engine.current_azimuth == 0.0
    assert engine.current_tilt == 0.0
    assert engine.azimuth_pid.integral == 0.0
    assert engine.tilt_pid.integral == 0.0
