# Architecture

## Components


## Repository structure


## Data storage

MongoDB (`server/data/manager.py`), chosen because the app will run on the internet with a hosted database. One collection, `hubs`, one document per hub:

- `city`, `city_key` (unique, lowercase), `state_code`, `region`, optional `county` override, `created_at`. The seed includes `location` (latitude, longitude, county) for every hub. Existing hub documents missing coordinates get that seed location on startup.
- `location`, `weather`, `disasters`, `alerts`: the agent does not add or update hubs. It calls `get_location` only when `list_hubs` did not already return coordinates. `get_location` takes the city list and resolves every city in parallel inside that one call. It then calls `get_weather_history`, `get_disaster_history`, and `get_active_alerts` only for the sections a question needs. Each of those tools takes a list and fetches every place in that one call.


## Scoring

`agent/scoring/factors.py` holds static weights. `score_hub` in `agent/scoring/score.py` turns weather, FEMA history, and active alerts into a 0-100 `RiskScore`: weather 50 (snow, freezing, heavy rain, high wind), disasters 40, alerts 10. A section that failed is omitted and the remaining weights are scaled to 100. `score_hubs` calls it when a question ranks or compares hubs. The score is stored on the hub document with `scored_at`. A score older than one day is recalculated; a newer score is reused.

## Session

The Ollama agent stores each chat in process memory (`InMemorySaver`), keyed by `thread_id`. A later request with the same id continues that chat and adds only the new message. A thread with nothing saved yet uses the message list on the request. The memory is gone when the server process stops.

## Assumptions and scope

The agent is registered with read tools only: `list_hubs`, `score_hubs`, `get_location`, and the weather, disaster, and alert getters. A question about technologies, or a request to add, update, or remove hubs, is answered by the model itself, in one or two friendly sentences, with no tool call and no list of tool names. `GET /` and `GET /json/version` on the API port return the API name so those probes are not 404. Weather answers name a fact once, and mention total snowfall only when the user asks how much snow fell. If the hub or the hazard is missing, the reply is one follow-up question and does not describe what data is available.
