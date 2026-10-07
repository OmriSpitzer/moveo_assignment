from datetime import date, datetime, timedelta, timezone
from agent.schema.tool_results import (
    ActiveAlerts, DisasterHistory, FactorScore, RiskScore, ToolError, WeatherHistory,
)
from agent.scoring.factors import (
    ALERT_SEVERITY_POINTS, ALERT_WEIGHT,
    DISASTER_FULL_AT, DISASTER_OTHER_POINTS_PER_YEAR, DISASTER_POINTS_PER_YEAR, DISASTER_WEIGHT,
    WEATHER_FACTORS,
)

"""
    Deterministic hub risk score from the static factors in factors.py
"""


# A stored score older than one day is recalculated
def score_needs_refresh(scored_at: datetime | None, now: datetime | None = None) -> bool:
    if scored_at is None:
        return True
    now = now or datetime.now(timezone.utc)
    if scored_at.tzinfo is None:
        scored_at = scored_at.replace(tzinfo=timezone.utc)
    return now - scored_at > timedelta(days=1)


def _ratio(value: float, cap: float) -> float:
    return min(value / cap, 1.0) if cap else 0.0


def _weather(weather: WeatherHistory) -> tuple[float, float, list[tuple[str, float, float, str]]]:
    earned = 0.0
    weight = 0.0
    rows = []
    for field, label, factor_weight, cap in WEATHER_FACTORS:
        percent = getattr(weather, field)
        points = _ratio(percent, cap) * factor_weight
        earned += points
        weight += factor_weight
        rows.append((label, points, factor_weight, f"{percent}% of days, full weight at {cap}%"))
    return earned, weight, rows


def _disasters(disasters: DisasterHistory) -> tuple[float, float, list[tuple[str, float, float, str]]]:
    years = max(1, date.today().year - disasters.since_year + 1)
    raw = 0.0
    counts = []
    for incident, count in disasters.by_incident_type.items():
        per_year = DISASTER_POINTS_PER_YEAR.get(incident, DISASTER_OTHER_POINTS_PER_YEAR)
        raw += count / years * per_year
        if count:
            counts.append(f"{incident} {count}")
    points = _ratio(raw, DISASTER_FULL_AT) * DISASTER_WEIGHT
    detail = ", ".join(counts) if counts else "none"
    detail = f"{disasters.total_disasters} since {disasters.since_year} ({detail})"
    return points, DISASTER_WEIGHT, [("FEMA disasters", points, DISASTER_WEIGHT, detail)]


def _alerts(alerts: ActiveAlerts) -> tuple[float, float, list[tuple[str, float, float, str]]]:
    raw = 0.0
    counts: dict[str, int] = {}
    for alert in alerts.alerts:
        severity = (alert.severity or "Unknown").strip().title()
        if severity not in ALERT_SEVERITY_POINTS:
            severity = "Unknown"
        raw += ALERT_SEVERITY_POINTS[severity]
        counts[severity] = counts.get(severity, 0) + 1
    points = min(raw, ALERT_WEIGHT)
    detail = ", ".join(f"{severity} {count}" for severity, count in counts.items()) or "none"
    return points, ALERT_WEIGHT, [("Active alerts", points, ALERT_WEIGHT, detail)]


def score_hub(
    weather: WeatherHistory | ToolError | None,
    disasters: DisasterHistory | ToolError | None,
    alerts: ActiveAlerts | ToolError | None,
) -> RiskScore:
    parts = []
    excluded = []
    for name, value, score_section in (
        ("weather", weather, _weather),
        ("disasters", disasters, _disasters),
        ("alerts", alerts, _alerts),
    ):
        if not isinstance(value, (WeatherHistory, DisasterHistory, ActiveAlerts)):
            excluded.append(name)
            continue
        earned, weight, rows = score_section(value)
        parts.append((earned, weight, rows))

    available = sum(weight for _, weight, _ in parts)
    if not available:
        return RiskScore(score=None, factors=[], excluded=excluded)

    scale = 100 / available
    factors = []
    total = 0.0
    for earned, _, rows in parts:
        total += earned * scale
        for label, points, weight, detail in rows:
            factors.append(FactorScore(
                name=label,
                points=round(points * scale, 1),
                weight=round(weight * scale, 1),
                detail=detail,
            ))
    return RiskScore(score=round(total, 1), factors=factors, excluded=excluded)
