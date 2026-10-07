from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import re
import requests
from pydantic import BaseModel
from langchain_core.tools import tool
from agent.schema.tool_results import ActiveAlerts, Alert, DisasterHistory, ToolError, WeatherHistory

HISTORY_API_URL = "https://archive-api.open-meteo.com/v1/archive"
DISASTER_API_URL = "https://www.fema.gov/api/open/v2/DisasterDeclarationsSummaries"
CURRENT_API_URL = "https://api.weather.gov/alerts/active"

TIMEOUT = 20
NWS_HEADERS = {"User-Agent": "moveo-weather-risk-agent", "Accept": "application/geo+json"}

HEAVY_RAIN_MM = 25.0
HIGH_WIND_KMH = 60.0
FREEZING_C = 0.0


def _count(values, predicate) -> int:
    return sum(1 for v in values if v is not None and predicate(v))


# Geocoding says "Miami-Dade County", OpenFEMA says "Miami-Dade (County)"
def _county_key(county: str) -> str:
    return re.sub(r"\s+(county|parish|borough|census area|municipality)$", "", county.strip(), flags=re.IGNORECASE).lower()


def _pct(part: int, total: int) -> float:
    return round(100 * part / total, 1) if total else 0.0


class Point(BaseModel):
    latitude: float
    longitude: float


class DisasterPlace(BaseModel):
    state_code: str
    county: str | None = None


def _model(cls, item):
    return item if isinstance(item, cls) else cls.model_validate(item)


def _each(fn, items: list):
    if not items:
        return []
    with ThreadPoolExecutor(max_workers=min(8, len(items))) as pool:
        return list(pool.map(fn, items))


class WeatherTools:
    def _weather_one(point: Point, start_date: str, end_date: str) -> WeatherHistory | ToolError:
        point = _model(Point, point)
        latitude, longitude = point.latitude, point.longitude
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date,
            "end_date": end_date,
            "daily": "snowfall_sum,temperature_2m_min,precipitation_sum,wind_gusts_10m_max",
            "timezone": "auto",
        }
        try:
            response = requests.get(HISTORY_API_URL, params=params, timeout=TIMEOUT)
            response.raise_for_status()
            daily = response.json()["daily"]
        except (requests.RequestException, KeyError) as e:
            return ToolError(source="open-meteo-archive", error=str(e))

        days = len(daily["time"])
        snow = _count(daily["snowfall_sum"], lambda v: v > 0)
        freezing = _count(daily["temperature_2m_min"], lambda v: v < FREEZING_C)
        rain = _count(daily["precipitation_sum"], lambda v: v >= HEAVY_RAIN_MM)
        wind = _count(daily["wind_gusts_10m_max"], lambda v: v >= HIGH_WIND_KMH)

        return WeatherHistory(
            source="open-meteo-archive",
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date,
            days=days,
            snow_days=snow,
            freezing_days=freezing,
            heavy_rain_days=rain,
            high_wind_days=wind,
            snow_days_pct=_pct(snow, days),
            freezing_days_pct=_pct(freezing, days),
            heavy_rain_days_pct=_pct(rain, days),
            high_wind_days_pct=_pct(wind, days),
            total_snowfall_cm=round(sum(v for v in daily["snowfall_sum"] if v is not None), 1),
            heavy_rain_threshold_mm=HEAVY_RAIN_MM,
            high_wind_threshold_kmh=HIGH_WIND_KMH,
            freezing_threshold_c=FREEZING_C,
        )

    @tool
    def get_weather_history(points: list[Point], start_date: str, end_date: str) -> list[WeatherHistory | ToolError]:
        """Summarize daily historical weather for each point between start_date and end_date (YYYY-MM-DD):
        snow days, freezing days, heavy rain days, high wind days, and their percentages.
        total_snowfall_cm is included; mention it only when the user asks how much snow fell.
        Results stay in the same order as points. Pass every location in one call."""
        return _each(lambda point: WeatherTools._weather_one(point, start_date, end_date), points)

    def _disaster_one(place: DisasterPlace, since_year: int) -> DisasterHistory | ToolError:
        place = _model(DisasterPlace, place)
        state_code = place.state_code
        county = place.county or None
        params = {
            "$filter": f"state eq '{state_code.upper()}' and declarationDate ge '{since_year}-01-01T00:00:00.000z'",
            "$select": "disasterNumber,incidentType,designatedArea",
            "$top": 10000,
        }
        try:
            response = requests.get(DISASTER_API_URL, params=params, timeout=TIMEOUT)
            response.raise_for_status()
            records = response.json()["DisasterDeclarationsSummaries"]
        except (requests.RequestException, KeyError) as e:
            return ToolError(source="openfema", error=str(e))

        if county:
            key = _county_key(county)
            records = [r for r in records if key in (r.get("designatedArea") or "").lower()]
        # OpenFEMA has one row per county per disaster
        unique = {r["disasterNumber"]: r["incidentType"] for r in records}

        return DisasterHistory(
            source="openfema",
            state=state_code.upper(),
            county=county,
            since_year=since_year,
            total_disasters=len(unique),
            by_incident_type=dict(Counter(unique.values()).most_common()),
        )

    @tool
    def get_disaster_history(places: list[DisasterPlace], since_year: int = 2000) -> list[DisasterHistory | ToolError]:
        """Count FEMA disaster declarations by incident type (Hurricane, Flood, Snowstorm, Severe Storm, ...)
        for each place (state_code, optional county such as 'Miami-Dade') since since_year.
        Results stay in the same order as places. Pass every place in one call."""
        return _each(lambda place: WeatherTools._disaster_one(place, since_year), places)

    def _alerts_one(point: Point) -> ActiveAlerts | ToolError:
        point = _model(Point, point)
        latitude, longitude = point.latitude, point.longitude
        params = {"point": f"{round(latitude, 4)},{round(longitude, 4)}"}
        try:
            response = requests.get(CURRENT_API_URL, params=params, headers=NWS_HEADERS, timeout=TIMEOUT)
            response.raise_for_status()
            features = response.json()["features"]
        except (requests.RequestException, KeyError) as e:
            return ToolError(source="nws", error=str(e))

        alerts = [
            Alert(
                event=p.get("event"),
                severity=p.get("severity"),
                headline=p.get("headline"),
                expires=p.get("expires"),
            )
            for p in (f["properties"] for f in features)
        ]
        return ActiveAlerts(
            source="nws",
            latitude=latitude,
            longitude=longitude,
            active_alert_count=len(alerts),
            alerts=alerts,
        )

    @tool
    def get_active_alerts(points: list[Point]) -> list[ActiveAlerts | ToolError]:
        """Get currently active National Weather Service alerts for each point.
        Results stay in the same order as points. Pass every location in one call."""
        return _each(WeatherTools._alerts_one, points)

    @staticmethod
    def get_tools():
        return [
            WeatherTools.get_weather_history,
            WeatherTools.get_disaster_history,
            WeatherTools.get_active_alerts,
        ]
