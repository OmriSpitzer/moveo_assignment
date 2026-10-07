from dataclasses import asdict
from datetime import datetime, timezone
from typing import Literal
from langchain_core.tools import tool
from agent.schema.tool_results import (
    ActiveAlerts, DisasterHistory, FactorScore, Hub, HubScore, Location, RiskScore, ToolError, WeatherHistory,
)
from agent.scoring.score import ScoreMethod
from agent.tools.db_tools import DbTools
from agent.tools.weather_tools import WeatherTools
from data.manager import DataManager

"""
    Hub tools used by the agent

    Methods:
        list_hubs() -> list[Hub]
        set_hub(city: str, state_code: str, region: Literal["Northeast", "Midwest", "South", "West"]) -> Hub | ToolError
        get_tools() -> list[Callable[[], Any]]
"""

# Get the stored score
def _stored_score(raw) -> tuple[RiskScore, datetime] | None:
    if not isinstance(raw, dict) or raw.get("scored_at") is None:
        return None
    scored_at = raw["scored_at"]
    if isinstance(scored_at, str):
        scored_at = datetime.fromisoformat(scored_at)
    if not isinstance(scored_at, datetime):
        return None
    if scored_at.tzinfo is None:
        scored_at = scored_at.replace(tzinfo=timezone.utc)
    factors = [
        FactorScore(name=row["name"], points=float(row["points"]), weight=float(row["weight"]), detail=row["detail"])
        for row in raw.get("factors") or []
    ]
    score = raw.get("score")
    return RiskScore(
        score=None if score is None else float(score),
        factors=factors,
        excluded=list(raw.get("excluded") or []),
    ), scored_at

# Build the hub score object
def _hub_score(doc: dict, risk: RiskScore, scored_at: datetime, refreshed: bool) -> HubScore:
    if scored_at.tzinfo is None:
        scored_at = scored_at.replace(tzinfo=timezone.utc)
    return HubScore(
        city=doc["city"],
        state_code=doc["state_code"],
        region=doc["region"],
        score=risk.score,
        factors=risk.factors,
        excluded=list(risk.excluded),
        scored_at=scored_at.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        refreshed=refreshed,
    )

# Save the score
def _save_score(doc: dict, risk: RiskScore, scored_at: datetime) -> None:
    payload = asdict(risk)
    payload["scored_at"] = scored_at
    DbTools.set_fields({"city_key": doc["city_key"]}, {"score": payload})

# Refresh the scores
def _refresh_scores(pending: list[tuple[int, dict]], results: list, now: datetime) -> None:
    points = []
    places = []
    for _, doc in pending:
        location = doc["location"]
        points.append({"latitude": location["latitude"], "longitude": location["longitude"]})
        places.append({
            "state_code": doc["state_code"],
            "county": doc.get("county") or location.get("county"),
        })
    year = datetime.now(timezone.utc).year - 1
    start_date, end_date = f"{year}-01-01", f"{year}-12-31"
    weather = WeatherTools.get_weather_history.invoke({"points": points, "start_date": start_date, "end_date": end_date})
    disasters = WeatherTools.get_disaster_history.invoke({"places": places})
    alerts = WeatherTools.get_active_alerts.invoke({"points": points})
    for n, (i, doc) in enumerate(pending):
        risk = ScoreMethod.score_hub(weather[n], disasters[n], alerts[n])
        complete = all(
            isinstance(item, (WeatherHistory, DisasterHistory, ActiveAlerts))
            for item in (weather[n], disasters[n], alerts[n])
        )
        if complete and risk.score is not None:
            _save_score(doc, risk, now)
        results[i] = _hub_score(doc, risk, now, refreshed=True)

class HubTools:
    # List the company's distribution hubs
    @tool()
    def list_hubs() -> list[Hub]:
        """Company hubs: city, state code, region, county, and coordinates when stored."""
        
        docs = DbTools.find_all(projection={"city": 1, "state_code": 1, "region": 1, "county": 1, "location": 1})

        # create a list of hubs
        list_of_hubs = []
        for doc in docs:
            stored = doc.get("location") or {}
            list_of_hubs.append(Hub(
                city=doc["city"],
                state_code=doc["state_code"],
                region=doc["region"],
                county=doc.get("county") or stored.get("county"),
                latitude=stored.get("latitude"),
                longitude=stored.get("longitude"),
            ))
        return list_of_hubs

    @tool
    def score_hubs(cities: list[str]) -> list[HubScore | ToolError]:
        """0-100 risk score per hub, highest first. A score older than one day is refreshed. Pass every city in one call."""
        now = datetime.now(timezone.utc)
        results: list[HubScore | ToolError | None] = [None] * len(cities)
        pending: list[tuple[int, dict]] = []
        for i, city in enumerate(cities):
            doc = DbTools.find_one({"city_key": DataManager.hub_key(city)})
            if doc is None:
                results[i] = ToolError(source="hubs", error=f"{city} is not a company hub")
                continue
            stored = _stored_score(doc.get("score"))
            if stored is not None and not ScoreMethod.score_needs_refresh(stored[1], now):
                results[i] = _hub_score(doc, stored[0], stored[1], refreshed=False)
                continue
            location = doc.get("location") or {}
            if location.get("latitude") is None or location.get("longitude") is None:
                results[i] = ToolError(source="hubs", error=f"{doc['city']} has no stored location")
                continue
            pending.append((i, doc))
        if pending:
            _refresh_scores(pending, results, now)
        scored = [item for item in results if isinstance(item, HubScore)]
        errors = [item for item in results if isinstance(item, ToolError)]
        scored.sort(key=lambda item: (item.score is not None, item.score or 0), reverse=True)
        return scored + errors

    # Add a new company hub or update an existing hub's
    @tool
    def set_hub(
        city: str, state_code: str, region: Literal["Northeast", "Midwest", "South", "West"],
        latitude: float, longitude: float, county: str | None = None, state: str | None = None,
    ) -> Hub | ToolError:
        """Add or update a hub. Call only when the user asks to add or change one."""

        location = Location(
            source="open-meteo-geocoding",
            name=city,
            latitude=latitude,
            longitude=longitude,
            state=state,
            state_code=state_code,
            county=county,
        )
        now = datetime.now(timezone.utc)
        key = DataManager.hub_key(location.name)
        fields = {
            "city": location.name,
            "city_key": key,
            "state_code": location.state_code,
            "region": region,
            "location": asdict(location),
            "weather": None,
            "disasters": None,
            "alerts": None,
            "updated_at": {"location": now},
        }
        if DbTools.find_one({"city_key": key}) is None:
            fields["created_at"] = now
        DbTools.set_fields({"city_key": key}, fields, upsert=True)
        return Hub(
            city=location.name, state_code=location.state_code, region=region,
            county=county, latitude=latitude, longitude=longitude,
        )

    # Get the tools as a list of callables
    @staticmethod
    def get_tools():
        return [HubTools.list_hubs, HubTools.score_hubs]
