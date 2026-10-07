from dataclasses import dataclass

"""
    Result dataclasses returned by the agent tools
"""

# Tool error answer class
@dataclass(frozen=True)
class ToolError:
    source: str
    error: str


# Location answer class
@dataclass(frozen=True)
class Location:
    source: str
    name: str
    latitude: float
    longitude: float
    state: str | None
    state_code: str | None
    county: str | None


# Weather history answer class
@dataclass(frozen=True)
class WeatherHistory:
    source: str
    latitude: float
    longitude: float
    start_date: str
    end_date: str
    days: int
    snow_days: int
    freezing_days: int
    heavy_rain_days: int
    high_wind_days: int
    snow_days_pct: float
    freezing_days_pct: float
    heavy_rain_days_pct: float
    high_wind_days_pct: float
    total_snowfall_cm: float
    heavy_rain_threshold_mm: float
    high_wind_threshold_kmh: float
    freezing_threshold_c: float


# Disaster history answer class
@dataclass(frozen=True)
class DisasterHistory:
    source: str
    state: str
    county: str | None
    since_year: int
    total_disasters: int
    by_incident_type: dict[str, int]


# Alert answer class
@dataclass(frozen=True)
class Alert:
    event: str | None
    severity: str | None
    headline: str | None
    expires: str | None


# Active alerts answer class
@dataclass(frozen=True)
class ActiveAlerts:
    source: str
    latitude: float
    longitude: float
    active_alert_count: int
    alerts: list[Alert]


# Current weather answer class
@dataclass(frozen=True)
class CurrentWeather:
    source: str
    latitude: float
    longitude: float
    time: str
    temperature_c: float
    precipitation_mm: float
    wind_speed_kmh: float
    wind_gusts_kmh: float
    weather_code: int
    condition: str


# Factor score answer class
@dataclass(frozen=True)
class FactorScore:
    name: str
    points: float
    weight: float
    detail: str


# Risk score answer class
@dataclass(frozen=True)
class RiskScore:
    score: float | None
    factors: list[FactorScore]
    excluded: list[str]


# Hub score answer class
@dataclass(frozen=True)
class HubScore:
    city: str
    state_code: str
    region: str
    score: float | None
    factors: list[FactorScore]
    excluded: list[str]
    scored_at: str
    refreshed: bool
    

# Hub answer class
@dataclass(frozen=True)
class Hub:
    city: str
    state_code: str
    region: str
    county: str | None = None
    latitude: float | None = None
    longitude: float | None = None
