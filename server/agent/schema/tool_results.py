from dataclasses import dataclass

"""
    Result dataclasses returned by the agent tools

    Classes:
        ToolError: a tool call failed
        Location: geocoded US city
        WeatherHistory: summarized daily historical weather
        DisasterHistory: FEMA disaster declarations counted by incident type
        Alert: a single active NWS alert
        ActiveAlerts: active NWS alerts for a location
        FactorScore: one static factor's points inside a hub score
        RiskScore: 0-100 score, factor points, and sections left out
        HubScore: stored 0-100 score for one hub, with the time it was calculated
        HubRisk: weather, disasters, alerts, and score for one hub city
        Hub: a company hub from the hubs collection
"""

@dataclass(frozen=True)
class ToolError:
    source: str
    error: str


@dataclass(frozen=True)
class Location:
    source: str
    name: str
    latitude: float
    longitude: float
    state: str | None
    state_code: str | None
    county: str | None


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


@dataclass(frozen=True)
class DisasterHistory:
    source: str
    state: str
    county: str | None
    since_year: int
    total_disasters: int
    by_incident_type: dict[str, int]


@dataclass(frozen=True)
class Alert:
    event: str | None
    severity: str | None
    headline: str | None
    expires: str | None


@dataclass(frozen=True)
class ActiveAlerts:
    source: str
    latitude: float
    longitude: float
    active_alert_count: int
    alerts: list[Alert]


@dataclass(frozen=True)
class FactorScore:
    name: str
    points: float
    weight: float
    detail: str


@dataclass(frozen=True)
class RiskScore:
    score: float | None
    factors: list[FactorScore]
    excluded: list[str]


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


@dataclass(frozen=True)
class HubRisk:
    city: str
    state_code: str
    region: str
    weather: WeatherHistory | ToolError | None
    disasters: DisasterHistory | ToolError | None
    alerts: ActiveAlerts | ToolError | None
    data_as_of: dict[str, str]
    score: RiskScore | None = None


@dataclass(frozen=True)
class Hub:
    city: str
    state_code: str
    region: str
    county: str | None = None
    latitude: float | None = None
    longitude: float | None = None
