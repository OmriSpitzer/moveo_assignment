TOOL_PROMPT = """
- list_hubs:
	input: none
	output: city, state code, region, county, and latitude and longitude when a location is already stored. Answers cover only these hubs.
- get_location:
	input: cities (a list of city names) and optional state_codes in the same order
	output: latitude, longitude, and county for each city, in that order, from one parallel lookup. Call once for every hub whose coordinates were not returned by list_hubs, before any tool that needs coordinates. If a county was returned, pass it to get_disaster_history.
- get_weather_history:
	input: a list of {latitude, longitude}, start_date, and end_date (YYYY-MM-DD). The default period is the last full calendar year; pass dates only when the question names a period.
	output: snow, freezing, heavy rain, and high wind days for each point, in the same order. Call only when the question needs historical weather.
- get_disaster_history:
	input: a list of {state_code, county} and since_year (default 2000)
	output: FEMA declarations by incident type for each place, in the same order. Call only when the question needs disaster history.
- get_active_alerts:
	input: a list of {latitude, longitude}
	output: current NWS alerts for each point, in the same order. Call only when the question needs active alerts.
- get_current_weather:
	input: a list of {latitude, longitude}. Use coordinates already returned for that hub, including a follow-up such as "there now".
	output: current temperature, precipitation, wind, and condition for each point, in the same order. Do not answer that question with get_active_alerts.
- score_hubs:
	input: hub city names
	output: each hub's 0-100 risk score, factor points, excluded sections, and scored_at, highest score first. Factor points are included when a current score is returned. A missing score, a score with no factor points, or one older than one day, is recalculated and saved.
"""
