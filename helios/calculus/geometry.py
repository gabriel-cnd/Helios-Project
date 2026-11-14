"""
1. Créer la fonction `deg2rad(deg)`
2. Créer la fonction `rad2deg(rad)`
3. Créer la fonction `normalize_angle(angle)`
4. Créer la fonction `clamp(value, min_val, max_val)`
5. Créer la fonction `vector_from_angles(azimuth, elevation)`
6. Ajouter les imports nécessaires (math / numpy)
7. Ajouter un petit test interne dans un `if __name__ == "__main__":`
8. Vérifier que chaque fonction retourne bien un float ou un tuple
"""

import math


def deg2rad(deg):
    """Converse degrees to radians"""
    return deg * (math.pi / 180.0)


def rad2deg(rad):
    """Converse radians to degrees"""
    return rad * (180.0 / math.pi)


def normalize_angle(angle):
    """Normalize angle to be within [0, 2pi["""
    return angle % (2 * math.pi)


def clamp(value, min_val, max_val):
    """Clamp value between min_val and max_val"""
    return max(min_val, min(value, max_val))


def vector_from_angles(azimuth, elevation):
    """Create a 3D unit vector from azimuth and elevation angles"""
    x = math.cos(elevation) * math.cos(azimuth)
    y = math.cos(elevation) * math.sin(azimuth)
    z = math.sin(elevation)
    return (x, y, z)


if __name__ == "__main__":
    # Test deg2rad and rad2deg
    deg = 180.0
    rad = deg2rad(deg)
    print(f"{deg} degrees is {rad} radians")
    print(f"{rad} radians is {rad2deg(rad)} degrees")

    # Test normalize_angle
    angle = 7 * math.pi
    normalized = normalize_angle(angle)
    print(f"Normalized angle of {angle} is {normalized}")

    # Test clamp
    value = 10
    clamped_value = clamp(value, 0, 5)
    print(f"Clamped value of {value} between 0 and 5 is {clamped_value}")

    # Test vector_from_angles
    azimuth = deg2rad(45)
    elevation = deg2rad(30)
    vector = vector_from_angles(azimuth, elevation)
    print(f"Vector from azimuth {azimuth} and elevation {elevation} is {vector}")

    # Additional simple tests
    if __name__ == "__main__":
        print("deg2rad(180) =", deg2rad(180))
        print("rad2deg(pi) =", rad2deg(math.pi))
        print("normalize_angle(7) =", normalize_angle(7))
        print("vector_from_angles(1.0, 0.5) =", vector_from_angles(1.0, 0.5))
