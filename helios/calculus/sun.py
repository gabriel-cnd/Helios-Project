"""
1. Importer les modules nécessaires
2. Importer les fonctions créées dans geometry.py
3. Créer la fonction 'get_sun_position(time, latitude, longitude)'
4. Extraire et convertir les angles nécessaires
5. Retourner les valeurs sous forme de dictionnaire
6. Ajouter bloc de test
"""

import pvlib.solarposition as solarposition
import pvlib.irradiance as irradiance
import numpy as np
from datetime import datetime
from helios.calculus.geometry import deg2rad


def get_sun_position(time, latitude, longitude):
    """Calculate the sun's position: azimuth and elevation"""
    df = solarposition.get_solarposition(
        time=time, latitude=latitude, longitude=longitude
    )

    azimuth = deg2rad(df["azimuth"].iloc[0])
    elevation = deg2rad(df["elevation"].iloc[0])

    return {"azimuth": azimuth, "elevation": elevation}


if __name__ == "__main__":
    """Test get_sun_position function"""
    now = datetime.now()
    pos = get_sun_position(now, 46.5, 6.6)  # E.g. for Romandie, Switzerland
    print("Sun position (radians):", pos)


def compute_irradiance(
    azimuth_sun, elevation_sun, tilt_panel, azimuth_panel, ghi=800, dhi=100, dni=None
):
    """
    Compute irradiation received by the PV panel using pvlib.
    ghi = Global Horizontal Irradiance (W/m2)
    dhi = Diffuse Horizontal Irradiance (W/m2)
    dni = Direct Normal Irradiance (W/m2)
    If dni is None, it is estimated from ghi and dhi.
    """

    # Convert radians → degrees
    az_sun_deg = np.degrees(azimuth_sun)
    el_sun_deg = np.degrees(elevation_sun)
    zenith = 90 - el_sun_deg  # pvlib uses zenith, not elevation

    # Estimate DNI if not provided
    if dni is None:
        dni = max(0, (ghi - dhi) / max(0.1, np.cos(np.radians(zenith))))

    result = irradiance.get_total_irradiance(
        surface_tilt=tilt_panel,
        surface_azimuth=azimuth_panel,
        dni=dni,
        ghi=ghi,
        dhi=dhi,
        solar_zenith=zenith,
        solar_azimuth=az_sun_deg,
    )

    return result  # dictionary with: poa_global, poa_direct, poa_diffuse, poa_ground
