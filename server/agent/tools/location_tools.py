from concurrent.futures import ThreadPoolExecutor
import requests
from pydantic import BaseModel
from langchain_core.tools import tool
from agent.schema.tool_results import Location, ToolError

GEOCODING_API_URL = "https://geocoding-api.open-meteo.com/v1/search"

TIMEOUT = 20

US_STATE_CODES = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR", "California": "CA",
    "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE", "District of Columbia": "DC",
    "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID", "Illinois": "IL",
    "Indiana": "IN", "Iowa": "IA", "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA",
    "Maine": "ME", "Maryland": "MD", "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN",
    "Mississippi": "MS", "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
    "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
    "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK", "Oregon": "OR",
    "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC", "South Dakota": "SD",
    "Tennessee": "TN", "Texas": "TX", "Utah": "UT", "Vermont": "VT", "Virginia": "VA",
    "Washington": "WA", "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY",
}


class CityPlace(BaseModel):
    city: str
    state_code: str | None = None


class LocationTools:
    def _one(place: CityPlace) -> Location | ToolError:
        place = place if isinstance(place, CityPlace) else CityPlace.model_validate(place)
        city = place.city
        state_code = place.state_code
        params = {"name": city, "count": 10 if state_code else 1, "countryCode": "US", "language": "en", "format": "json"}
        try:
            response = requests.get(GEOCODING_API_URL, params=params, timeout=TIMEOUT)
            response.raise_for_status()
            results = response.json().get("results") or []
        except requests.RequestException as e:
            return ToolError(source="open-meteo-geocoding", error=str(e))

        if state_code:
            results = [r for r in results if US_STATE_CODES.get(r.get("admin1")) == state_code.upper()]
        if not results:
            where = f"{city}, {state_code.upper()}" if state_code else city
            return ToolError(source="open-meteo-geocoding", error=f"no US location found for '{where}'")

        r = results[0]
        state = r.get("admin1")
        return Location(
            source="open-meteo-geocoding",
            name=r["name"],
            latitude=r["latitude"],
            longitude=r["longitude"],
            state=state,
            state_code=US_STATE_CODES.get(state),
            county=r.get("admin2"),
        )

    @tool
    def get_location(cities: list[str], state_codes: list[str] | None = None) -> list[Location | ToolError]:
        """Resolve each US city to latitude, longitude, state, 2-letter state code and county.
        Pass every city in one list. state_codes, when given, matches that list in order (Kansas City with MO).
        Results stay in the same order as cities."""
        codes = state_codes or []
        places = [
            CityPlace(city=city, state_code=codes[i] if i < len(codes) else None)
            for i, city in enumerate(cities)
        ]
        if not places:
            return []
        with ThreadPoolExecutor(max_workers=min(8, len(places))) as pool:
            return list(pool.map(LocationTools._one, places))

    @staticmethod
    def get_tools():
        return [LocationTools.get_location]
