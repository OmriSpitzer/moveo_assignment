"""
    Static risk-factor weights for the hub score (0-100).

    Weather: min(day_percent / cap_percent, 1) * weight
    Disasters: min(weighted declarations per year / full_at, 1) * weight
    Alerts: min(sum of severity points, weight)
    A missing section is dropped and the remaining weights are scaled to 100.
"""

# (field, label, weight, cap percent of days that earns the full weight)
WEATHER_FACTORS = (
    ("snow_days_pct", "Snow days", 15, 25),
    ("freezing_days_pct", "Freezing days", 10, 40),
    ("heavy_rain_days_pct", "Heavy rain days", 15, 10),
    ("high_wind_days_pct", "High wind days", 10, 15),
)

# Weighted declarations per year. full_at earns DISASTER_WEIGHT.
DISASTER_POINTS_PER_YEAR = {
    "Hurricane": 4.0,
    "Typhoon": 4.0,
    "Tsunami": 3.0,
    "Earthquake": 3.0,
    "Flood": 3.0,
    "Coastal Storm": 2.5,
    "Tropical Storm": 2.5,
    "Severe Storm": 2.0,
    "Tornado": 2.0,
    "Winter Storm": 2.0,
    "Snowstorm": 2.0,
    "Ice Storm": 2.0,
    "Fire": 1.5,
    "Mud/Landslide": 1.5,
    "Drought": 1.0,
}
DISASTER_OTHER_POINTS_PER_YEAR = 0.5
DISASTER_FULL_AT = 4.0
DISASTER_WEIGHT = 40

ALERT_SEVERITY_POINTS = {
    "Extreme": 10,
    "Severe": 6,
    "Moderate": 3,
    "Minor": 1,
    "Unknown": 1,
}
ALERT_WEIGHT = 10
