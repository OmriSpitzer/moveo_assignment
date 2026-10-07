from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import re
import requests
from pydantic import BaseModel
from langchain_core.tools import tool
from agent.schema.tool_results import ActiveAlerts, Alert, CurrentWeather, DisasterHistory, ToolError, WeatherHistory
from dotenv import load_dotenv
import os

"""
    Weather tools class

    Methods:
        get_weather_history: get weather history for multiple points
        get_disaster_history: get disaster history for multiple places
        get_active_alerts: get active alerts for multiple points
        get_current_weather: get current weather for multiple points
        get_tools: get the tools
"""

# Constants
HEAVY_RAIN_MM = 25.0
HIGH_WIND_KMH = 60.0
FREEZING_C = 0.0
load_dotenv()
URL_TIMEOUT = float(os.getenv("URL_TIMEOUT"))

# WMO weather interpretation codes used by Open-Meteo current conditions
WEATHER_CONDITIONS = {
    0: "Clear",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Rime fog",
    51: "Light drizzle",
    53: "Drizzle",
    55: "Heavy drizzle",
    56: "Light freezing drizzle",
    57: "Freezing drizzle",
    61: "Light rain",
    63: "Rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Freezing rain",
    71: "Light snow",
    73: "Snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Light rain showers",
    81: "Rain showers",
    82: "Heavy rain showers",
    85: "Light snow showers",
    86: "Snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with hail",
    99: "Thunderstorm with heavy hail",
}

# Point model
class Point(BaseModel):
    latitude: float
    longitude: float


# Disaster place model
class DisasterPlace(BaseModel):
    state_code: str
    county: str | None = None


# Model validator
def _model(cls, item):
    return item if isinstance(item, cls) else cls.model_validate(item)


# Thread pool executor
def _execture_parallel(fn, items: list):
    if not items:
        return []
    with ThreadPoolExecutor(max_workers=min(8, len(items))) as pool:
        return list(pool.map(fn, items))


def _area_name(value: str) -> str:
    name = re.sub(r"\s*\([^)]*\)\s*$", "", value.strip())
    name = re.sub(r"\s+(county|parish|borough|census area|municipality)$", "", name, flags=re.IGNORECASE)
    return name.strip().lower()


class WeatherTools:
    # Get weather history for a single point
    def _weather_one(point: Point, start_date: str, end_date: str) -> WeatherHistory | ToolError:
        # Count the number of values that satisfy the predicate
        def count(values, predicate) -> int:
            return sum(1 for v in values if v is not None and predicate(v))

        # Calculate the percentage of a part of a total
        def percentage_of(part: int, total: int) -> float:
            return round(100 * part / total, 1) if total else 0.0

        # Validate the point
        point = _model(Point, point)
        latitude, longitude = point.latitude, point.longitude

        # Build the parameters for the API call
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date,
            "end_date": end_date,
            "daily": "snowfall_sum,temperature_2m_min,precipitation_sum,wind_gusts_10m_max",
            "timezone": "auto",
        }

        # Make the API call
        try:
            response = requests.get(os.getenv("HISTORY_API_URL"), params=params, timeout=URL_TIMEOUT)
            response.raise_for_status()
            daily = response.json()["daily"]
        except (requests.RequestException, KeyError) as e:
            return ToolError(source="open-meteo-archive", error=str(e))

        # Calculate the number of days, snow days, freezing days, heavy rain days, and high wind days
        days = len(daily["time"])
        snow = count(daily["snowfall_sum"], lambda v: v > 0)
        freezing = count(daily["temperature_2m_min"], lambda v: v < FREEZING_C)
        rain = count(daily["precipitation_sum"], lambda v: v >= HEAVY_RAIN_MM)
        wind = count(daily["wind_gusts_10m_max"], lambda v: v >= HIGH_WIND_KMH)

        # Build the weather history object
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
            snow_days_pct=percentage_of(snow, days),
            freezing_days_pct=percentage_of(freezing, days),
            heavy_rain_days_pct=percentage_of(rain, days),
            high_wind_days_pct=percentage_of(wind, days),
            total_snowfall_cm=round(sum(v for v in daily["snowfall_sum"] if v is not None), 1),
            heavy_rain_threshold_mm=HEAVY_RAIN_MM,
            high_wind_threshold_kmh=HIGH_WIND_KMH,
            freezing_threshold_c=FREEZING_C,
        )

    # Get disaster history for a single place
    def _disaster_one(place: DisasterPlace, since_year: int) -> DisasterHistory | ToolError:
        # Validate the place
        place = _model(DisasterPlace, place)
        state_code = place.state_code
        county = place.county or None

        # Build the parameters for the API call
        params = {
            "$filter": f"state eq '{state_code.upper()}' and declarationDate ge '{since_year}-01-01T00:00:00.000z'",
            "$select": "disasterNumber,incidentType,designatedArea",
            "$top": 10000,
        }

        # Make the API call
        try:
            response = requests.get(os.getenv("DISASTER_API_URL"), params=params, timeout=URL_TIMEOUT)
            response.raise_for_status()
            records = response.json()["DisasterDeclarationsSummaries"]
        except (requests.RequestException, KeyError) as e:
            return ToolError(source="openfema", error=str(e))

        # Filter the records by county if provided
        if county:
            key = _area_name(county)
            records = [r for r in records if _area_name(r.get("designatedArea") or "") == key]
        
        # Build the disaster history object
        unique = {r["disasterNumber"]: r["incidentType"] for r in records}
        return DisasterHistory(
            source="openfema",
            state=state_code.upper(),
            county=county,
            since_year=since_year,
            total_disasters=len(unique),
            by_incident_type=dict(Counter(unique.values()).most_common()),
        )
    
    # Get active alerts for a single point
    def _alerts_one(point: Point) -> ActiveAlerts | ToolError:
        # Validate the point
        point = _model(Point, point)
        latitude, longitude = point.latitude, point.longitude

        # Build the parameters for the API call
        params = {"point": f"{round(latitude, 4)},{round(longitude, 4)}"}

        # Make the API call
        try:
            response = requests.get(os.getenv("CURRENT_API_URL"), params=params, headers={"User-Agent": "moveo-weather-risk-agent", "Accept": "application/geo+json"}, timeout=URL_TIMEOUT)
            response.raise_for_status()
            features = response.json()["features"]
        except (requests.RequestException, KeyError) as e:
            return ToolError(source="nws", error=str(e))

        # Build the active alerts object
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
    
    # Get current weather for a single point
    def _current_one(point: Point) -> CurrentWeather | ToolError:
        # Validate the point
        point = _model(Point, point)
        latitude, longitude = point.latitude, point.longitude

        # Build the parameters for the API call
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,precipitation,weather_code,wind_speed_10m,wind_gusts_10m",
            "timezone": "auto",
        }

        # Make the API call
        try:
            response = requests.get(os.getenv("FORECAST_API_URL"), params=params, timeout=URL_TIMEOUT)
            response.raise_for_status()
            current = response.json()["current"]
            code = int(current["weather_code"])

            # Build the current weather object
            return CurrentWeather(
                source="open-meteo-forecast",
                latitude=latitude,
                longitude=longitude,
                time=str(current["time"]),
                temperature_c=float(current["temperature_2m"]),
                precipitation_mm=float(current["precipitation"]),
                wind_speed_kmh=float(current["wind_speed_10m"]),
                wind_gusts_kmh=float(current["wind_gusts_10m"]),
                weather_code=code,
                condition=WEATHER_CONDITIONS.get(code, f"code {code}"),
            )
        except (requests.RequestException, KeyError, TypeError, ValueError) as e:
            return ToolError(source="open-meteo-forecast", error=str(e))

    # Get weather history for multiple points
    @tool
    def get_weather_history(points: list[Point], start_date: str, end_date: str) -> list[WeatherHistory | ToolError]:
        """Snow, freezing, heavy rain, and high wind days per point, in order. Pass every point in one call."""
        return _execture_parallel(lambda point: WeatherTools._weather_one(point, start_date, end_date), points)

    # Get disaster history for multiple places
    @tool
    def get_disaster_history(places: list[DisasterPlace], since_year: int = 2000) -> list[DisasterHistory | ToolError]:
        """FEMA declarations by incident type per place, in order, since since_year. Pass every place in one call."""
        return _execture_parallel(lambda place: WeatherTools._disaster_one(place, since_year), places)

    # Get active alerts for multiple points
    @tool
    def get_active_alerts(points: list[Point]) -> list[ActiveAlerts | ToolError]:
        """Active NWS alerts per point, in order. Pass every point in one call."""
        return _execture_parallel(WeatherTools._alerts_one, points)

    # Get current weather for multiple points
    @tool
    def get_current_weather(points: list[Point]) -> list[CurrentWeather | ToolError]:
        """Current temperature, precipitation, wind, and condition per point, in order. Pass every point in one call."""
        return _execture_parallel(WeatherTools._current_one, points)

    @staticmethod
    def get_tools():
        return [
            WeatherTools.get_weather_history,
            WeatherTools.get_disaster_history,
            WeatherTools.get_active_alerts,
            WeatherTools.get_current_weather,
        ]
