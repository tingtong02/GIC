from __future__ import annotations

import math


def project_field_onto_line(ex: float, ey: float, azimuth_deg: float) -> float:
    radians = math.radians(azimuth_deg)
    return ex * math.cos(radians) + ey * math.sin(radians)


def induced_voltage(projected_field: float, length_km: float) -> float:
    return projected_field * length_km
