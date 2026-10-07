# Tests

## Agent tools (2026-10-07 12:18)

Requires `requests` installed. Run from `server/`.

1. Tools return dataclasses from the live APIs:

```bash
python -c "from agent.tools.location_tools import LocationTools; from agent.tools.weather_tools import WeatherTools; loc = LocationTools.get_location.invoke({'city': 'Denver'}); print(loc); print(WeatherTools.get_weather_history.invoke({'latitude': loc.latitude, 'longitude': loc.longitude, 'start_date': '2025-01-01', 'end_date': '2025-12-31'})); print(WeatherTools.get_disaster_history.invoke({'state_code': 'FL', 'since_year': 2000, 'county': 'Miami-Dade'})); print(WeatherTools.get_active_alerts.invoke({'latitude': loc.latitude, 'longitude': loc.longitude}))"
```

Expected: `Location` for Denver with `state_code='CO'`; `WeatherHistory` with `days=365` and `snow_days_pct` > 0; `DisasterHistory` with `Hurricane` in `by_incident_type`; `ActiveAlerts` (count may be 0). No `ToolError`.

2. Agent picks relevant tools: ask "What percentage of days in Denver in 2025 had snowfall?" through the API. Expected: the agent calls `get_location` then `get_weather_history`, and the returned `Answer.answer` contains the snow-day percentage from the tool.

## Agent stream and weather-app (2026-10-07 12:24)

1. Stream endpoint (fake agent, no Ollama needed). Run from `server/`:

```bash
python -c "from fastapi.testclient import TestClient; from server import app; r = TestClient(app).post('/agent/stream', json={'messages': [{'role': 'user', 'content': 'hi'}]}); print(r.status_code, r.headers['content-type']); print(r.text)"
```

Expected: `200 text/event-stream`, then `data:` lines with `tool_call`, `tool_result`, `answer` (`"answer": "fake answer"`) and `done`.

2. End to end: in `server/` run `python server.py`; in `weather-app/` run `npm run dev` and open http://localhost:5173. Click a suggestion. Expected: while a tool is running, one amber step shows the current tool and changes when the next tool starts. After the answer, that step is gone. A follow-up question in the same page sends the earlier turns as history.

## Real agent structured answer (2026-10-07 12:33)

Requires Ollama settings in `server/.env`; uses the `RUN_LIMIT` set there. Run from `server/` (PowerShell):

```bash
$env:PYTHONIOENCODING = "utf-8"; python -c "from fastapi.testclient import TestClient; from server import app; r = TestClient(app).post('/agent/stream', json={'messages': [{'role': 'user', 'content': 'What percentage of days in Denver in 2025 had snowfall?'}]}); print(r.status_code); print(r.text)"
```

Expected: `tool_call`/`tool_result` for `get_location` and `get_weather_history`, then an `answer` event whose `answer.answer` mentions about 12.1% (not "agent finished without a structured answer"), with `model` = `MODEL` from `.env`, and no `LLMAnswer` step shown as a tool.

## Hub tool and failure reporting (2026-10-07 12:40)

Run from `server/` (PowerShell), `$env:PYTHONIOENCODING = "utf-8"` first.

1. Hub tool, live APIs, no model:

```bash
python -c "from agent.tools.hub_tools import HubTools; print(HubTools.get_hub_risk.invoke({'city': 'Miami'}))"
```

Expected: `HubRisk` with `Location` (`state_code='FL'`, `county='Miami-Dade County'`), `WeatherHistory` for last calendar year, `DisasterHistory` with `total_disasters` > 0 and `Hurricane` in `by_incident_type`, and `ActiveAlerts`.

2. Real agent, two cities within `RUN_LIMIT`:

```bash
python -c "from fastapi.testclient import TestClient; from server import app; r = TestClient(app).post('/agent/stream', json={'messages': [{'role': 'user', 'content': 'Compare Miami and Houston in terms of hurricane and flood exposure.'}]}); print(r.status_code); print(r.text)"
```

Expected: one `get_hub_risk` `tool_call`/`tool_result` pair per city (same `id`), then an `answer` event comparing FEMA hurricane and flood counts. Result 2026-10-07: passed in 3 model calls.

3. Failure reporting: temporarily set `RUN_LIMIT=1` and rerun step 2. Expected: an `error` event whose message contains the model call limit text (not an `answer` event); in the web app the reply is red and is not sent as history on the next question.

## Agent boundaries (2026-10-07 12:43)

Ask each question in the web app (or with the step 2 command above, changing `content`):

1. "What is a hurricane storm surge?" Expected: no tool steps; an answer of at most 3 sentences.
2. "Who won the last World Cup?" Expected: no tool steps; a one-sentence reply that it is out of scope.
3. "What percentage of days in Denver last year had snowfall?" Expected: one `get_hub_risk` step; the answer states the exact percentage, the period (last calendar year dates) and the source (Open-Meteo).

## Plain-text model reply accepted (2026-10-07 12:46)

Run from `server/` (PowerShell), `$env:PYTHONIOENCODING = "utf-8"` first:

```bash
python -c "from fastapi.testclient import TestClient; from server import app; r = TestClient(app).post('/agent/stream', json={'messages': [{'role': 'user', 'content': 'what is the weather at new york?'}]}); print(r.status_code); print(r.text[-1500:])"
```

Expected: one `get_hub_risk` step, then an `answer` event (not `error`) with the New York 2025 weather summary. Result 2026-10-07: passed.

## Answer format (2026-10-07 12:47)

Same command as above. Expected `answer.answer`: one opening sentence, at most 5 lines starting with "- ", no coordinates, no `**` markdown, and no closing "Period:" or "Sources:" line.

## No Period or Sources line (2026-10-07 17:19)

The prompt tells the model not to end an answer with a period or sources line. Run from `server/`.

```bash
python -c "from agent.prompts.ollama_system_prompt import SYSTEM_PROMPT; print('Period: <dates>' not in SYSTEM_PROMPT, 'Do not end with a Period or Sources line' in SYSTEM_PROMPT)"
```

Expected: `True True`. Result 2026-10-07: passed.

## MongoDB hubs (2026-10-07 13:15)

Set `MONGODB_URI` (and optionally `MONGODB_DB`) in `server/.env`. Run from `server/` (PowerShell), `$env:PYTHONIOENCODING = "utf-8"` first.

1. Connection, seeding and the hub option list:

```bash
python -c "from fastapi.testclient import TestClient; from server import app; r = TestClient(app).get('/hubs'); print(r.status_code, len(r.json())); print(r.json()[:3])"
```

Expected: `200 14` on an empty database, each item only `city`, `state_code`, `region` (no weather data). In MongoDB, `weather_risk.hubs` has 14 documents with a unique `city_key` index.

2. Timestamps decide API calls:

```bash
python -c "import time; from agent.tools.hub_tools import HubTools; t=time.time(); a=HubTools.get_hub_risk.invoke({'cities': ['Kansas City', 'New York', 'Paris']}); print('%.1fs' % (time.time()-t)); t=time.time(); b=HubTools.get_hub_risk.invoke({'cities': ['Kansas City']}); print('%.1fs' % (time.time()-t), a[0].data_as_of == b[0].data_as_of); print(a)"
```

Expected: Kansas City resolves to `MO`; New York uses county `New York`; Paris returns `ToolError` "not a company hub"; the second call is faster and `data_as_of` is unchanged (served from MongoDB). The hub document now has `location`, `weather`, `disasters`, `alerts` and `updated_at` for each. Result 2026-10-07: passed with an in-memory DB stand-in (1.5s then 0.3s). 13:55 against MongoDB Atlas: step 1 passed (`200 14`, index `city_key_1`); step 2 passed after fixing weather storage (3.6s then 0.3s, all four sections stored).

3. Web app: open http://localhost:5173. Expected: the "Hubs (14)" option list grouped by region; choosing a hub inserts its name into the input; the six quick questions are hub-based. Asking "Tell me about Paris" answers that Paris is not a company hub. Asking "Add Seattle, WA as a West hub" shows a "Saving hub" step and Seattle appears in the option list after the answer.

## Hubs collection only through DataManager (2026-10-07 16:08)

`HUBS_COLLECTION` is read only in `DataManager.hubs()`. `DbTools` calls that, and `hub_key` is `DataManager.hub_key`. Load `.env` before importing. Run from `server/` (PowerShell), `$env:PYTHONIOENCODING = "utf-8"` first.

```bash
python -c "from dotenv import load_dotenv; load_dotenv(); from data.manager import DataManager; from agent.tools.hub_tools import HubTools; print(DataManager.hubs().name, len(HubTools.list_hubs.invoke({})))"
```

Expected: `hubs` and the hub count (14 when the seeded collection is unchanged). Result 2026-10-07: passed (`hubs 14`).

## `get_hub_risk` description (2026-10-07 16:12)

The tool description is one sentence. Run from `server/`.

```bash
python -c "from agent.tools.hub_tools import HubTools; print(HubTools.get_hub_risk.description)"
```

Expected: `Weather, disasters, and active alerts for company hubs. A city that is not a hub returns an error.` Result 2026-10-07: passed.

## Static hub score (2026-10-07 16:21)

Run from `server/`. No API or database.

```bash
python -c "from datetime import date; from agent.scoring.score import ScoreMethod; from agent.schema.tool_results import WeatherHistory, DisasterHistory, ActiveAlerts, Alert, ToolError; w=lambda rain: WeatherHistory(source='t', latitude=0, longitude=0, start_date='2025-01-01', end_date='2025-12-31', days=365, snow_days=0, freezing_days=0, heavy_rain_days=0, high_wind_days=0, snow_days_pct=0, freezing_days_pct=0, heavy_rain_days_pct=rain, high_wind_days_pct=0, total_snowfall_cm=0, heavy_rain_threshold_mm=25, high_wind_threshold_kmh=60, freezing_threshold_c=0); d=DisasterHistory(source='t', state='FL', county=None, since_year=date.today().year, total_disasters=4, by_incident_type={'Hurricane': 4}); a=ActiveAlerts(source='t', latitude=0, longitude=0, active_alert_count=1, alerts=[Alert(event='Hurricane Warning', severity='Extreme', headline=None, expires=None)]); calm=DisasterHistory(source='t', state='CO', county=None, since_year=2000, total_disasters=0, by_incident_type={}); none=ActiveAlerts(source='t', latitude=0, longitude=0, active_alert_count=0, alerts=[]); high=ScoreMethod.score_hub(w(10), d, a); low=ScoreMethod.score_hub(w(0), calm, none); partial=ScoreMethod.score_hub(ToolError(source='t', error='down'), d, a); print(high.score, low.score, partial.score, partial.excluded)"
```

Expected: `65.0 0.0 100.0 ['weather']`. The 65 is heavy rain at its cap (15) plus FEMA at its cap (40, 4 hurricanes in the current year) plus one Extreme alert (10). The partial score drops weather and scales disasters and alerts to 100. `high` factor points are Snow days 0, Freezing days 0, Heavy rain days 15, High wind days 0, FEMA disasters 40, Active alerts 10. Result 2026-10-07: passed.

## `get_hub_risk` fetches live data only (2026-10-07 16:27)

`_is_fresh` and `_hub_risk` are gone. The tool does not read stored weather and does not set `score`. Load `.env` before importing. Run from `server/` (PowerShell), `$env:PYTHONIOENCODING = "utf-8"` first.

```bash
python -c "from dotenv import load_dotenv; load_dotenv(); from agent.tools.hub_tools import HubTools; from agent.schema.tool_results import HubRisk, ToolError, WeatherHistory; r=HubTools.get_hub_risk.invoke({'cities': ['Denver', 'Paris']}); print(type(r[0]).__name__, r[0].score, type(r[0].weather).__name__, type(r[1]).__name__, hasattr(HubTools, '_is_fresh'))"
```

Expected: `HubRisk None WeatherHistory ToolError False`. Denver has a location and weather for the last calendar year. Paris is not a company hub. Result 2026-10-07: passed.

## `HubRisk` has no location (2026-10-07 16:33)

Geocoding stays inside `get_hub_risk` and is not a field on the result. Load `.env` before importing. Run from `server/` (PowerShell), `$env:PYTHONIOENCODING = "utf-8"` first.

```bash
python -c "from dotenv import load_dotenv; load_dotenv(); from agent.tools.hub_tools import HubTools; from agent.schema.tool_results import WeatherHistory; r=HubTools.get_hub_risk.invoke({'cities': ['Denver', 'Paris']}); print(type(r[0]).__name__, hasattr(r[0], 'location'), type(r[0].weather).__name__, sorted(r[0].data_as_of), type(r[1]).__name__)"
```

Expected: `HubRisk False WeatherHistory ['alerts', 'disasters', 'weather'] ToolError`. Paris is not a company hub. Result 2026-10-07: passed.

## Model picks weather tools (2026-10-07 16:38)

`get_hub_risk` is not registered. The agent tools are the hub list, geocoding, and the three weather tools. Run from `server/`.

```bash
python -c "from agent.providers.ollama_agent import agent_tools; print([t.name for t in agent_tools()])"
```

Expected: `['list_hubs', 'set_hub', 'get_location', 'get_weather_history', 'get_disaster_history', 'get_active_alerts']`. Result 2026-10-07: passed.

## List inputs for location and weather tools (2026-10-07 16:43)

One call takes every place. A failed place is a `ToolError` in that position. Run from `server/` (PowerShell), `$env:PYTHONIOENCODING = "utf-8"` first.

```bash
python -c "from agent.tools.location_tools import LocationTools; from agent.tools.weather_tools import WeatherTools; locs=LocationTools.get_location.invoke({'places': [{'city': 'Denver', 'state_code': 'CO'}, {'city': 'NotARealCity', 'state_code': 'ZZ'}]}); weather=WeatherTools.get_weather_history.invoke({'points': [{'latitude': 39.74, 'longitude': -104.99}, {'latitude': 25.76, 'longitude': -80.19}], 'start_date': '2025-01-01', 'end_date': '2025-01-07'}); print(type(locs[0]).__name__, locs[0].state_code, type(locs[1]).__name__, len(weather), round(weather[0].latitude, 2), round(weather[1].latitude, 2), type(weather[0]).__name__)"
```

Expected: `Location CO ToolError 2 39.74 25.76 WeatherHistory`. Denver is first. The unknown city is an error and does not drop Denver. The two weather rows stay in the order of the points. Result 2026-10-07: passed.

## `set_hub` takes a location from the agent (2026-10-07 16:50)

`set_hub` does not call `get_location`. The agent passes coordinates it already has. `get_location` stays registered. Run from `server/`.

```bash
python -c "import inspect; from agent.tools.hub_tools import HubTools; from agent.providers.ollama_agent import agent_tools; print(sorted(HubTools.set_hub.args), 'get_location.invoke' in inspect.getsource(HubTools.set_hub.func), 'get_location' in [t.name for t in agent_tools()])"
```

Expected: `['city', 'county', 'latitude', 'longitude', 'region', 'state', 'state_code'] False True`. Result 2026-10-07: passed.

## `get_location` city list (2026-10-07 16:51)

One call takes every city. Lookups run in parallel. Results stay in the same order. Run from `server/` (PowerShell), `$env:PYTHONIOENCODING = "utf-8"` first.

```bash
python -c "from agent.tools.location_tools import LocationTools; r=LocationTools.get_location.invoke({'cities': ['Denver', 'Miami', 'NotARealCity'], 'state_codes': ['CO', 'FL', 'ZZ']}); print([type(x).__name__ for x in r], [getattr(x, 'state_code', None) for x in r])"
```

Expected: `['Location', 'Location', 'ToolError'] ['CO', 'FL', None]`. Result 2026-10-07: passed.

## Seed locations (2026-10-07 16:55)

Every seed hub has latitude and longitude. New York keeps county `New York`. Run from `server/`.

```bash
python -c "from data.seed_hubs import SEED_HUBS; print(len(SEED_HUBS), all('latitude' in h['location'] for h in SEED_HUBS), next(h['location']['county'] for h in SEED_HUBS if h['city']=='New York'), next(h['location']['state_code'] for h in SEED_HUBS if h['city']=='Denver'))"
```

Expected: `14 True New York CO`. Result 2026-10-07: passed.

## In-memory session (2026-10-07 17:01)

The Ollama agent stores a thread in process memory. A new thread is given the full message list. A thread that already has turns is given only the newest message. Run from `server/`.

```bash
python -c "from langchain_core.messages import AIMessage, HumanMessage; from agent.providers.ollama_agent import OllamaAgent; a=OllamaAgent(); fresh=a._messages_for_turn([HumanMessage(content='one'), AIMessage(content='two'), HumanMessage(content='three')], 'thread-new'); a._agent.update_state({'configurable': {'thread_id': 'thread-kept'}}, {'messages': [HumanMessage(content='earlier')]}); again=a._messages_for_turn([HumanMessage(content='one'), HumanMessage(content='follow up')], 'thread-kept'); print(type(a._agent.checkpointer).__name__, len(fresh), fresh[-1].content, len(again), again[0].content)"
```

Expected: `InMemorySaver 3 three 1 follow up`. Result 2026-10-07: passed.

## Boundary replies come from the model (2026-10-07 17:11)

`decline_request` is not a tool. The prompt tells the model to answer a removal, a bulk clear, or an out-of-scope question itself, with no tool call. Run from `server/`.

```bash
python -c "from agent.providers.ollama_agent import agent_tools; from agent.prompts.ollama_system_prompt import SYSTEM_PROMPT; names=[t.name for t in agent_tools()]; print('decline_request' not in names, 'Do not call a tool' in SYSTEM_PROMPT, 'administrators' in SYSTEM_PROMPT)"
```

Expected: `True True True`. Result 2026-10-07: passed.

## Root probes and read-only agent (2026-10-07 17:14)

`GET /` and `GET /json/version` return 200. The agent does not register `set_hub`. Weather, disaster, and alert tools stay registered, and the prompt says the agent cannot add, update, or remove hubs. Run from `server/`.

```bash
python -c "from fastapi.testclient import TestClient; from server import app; from agent.providers.ollama_agent import agent_tools; from agent.prompts.ollama_system_prompt import SYSTEM_PROMPT; names=[t.name for t in agent_tools()]; print(TestClient(app).get('/').status_code, TestClient(app).get('/json/version').status_code, 'set_hub' not in names, 'get_weather_history' in names, 'cannot add, update, or remove hubs' in SYSTEM_PROMPT)"
```

Expected: `200 200 True True True`. Result 2026-10-07: passed.

## Technology questions stay out of scope (2026-10-07 17:16)

The prompt treats a question about technologies as outside weather. The model must not list tool names. Run from `server/`.

```bash
python -c "from agent.prompts.ollama_system_prompt import SYSTEM_PROMPT; print('technologies' in SYSTEM_PROMPT, 'Do not list tool names' in SYSTEM_PROMPT, 'data sources' not in SYSTEM_PROMPT)"
```

Expected: `True True True`. Result 2026-10-07: passed.

## Hub score cached for one day (2026-10-07 17:23)

`score_hubs` is registered. A stored score newer than one day is returned unchanged and stays in score order. A score older than one day is refreshed. Load `.env` before importing. Run from `server/` (PowerShell), `$env:PYTHONIOENCODING = "utf-8"` first.

```bash
python -c "from datetime import datetime, timedelta, timezone; from dotenv import load_dotenv; load_dotenv(); from agent.scoring.score import ScoreMethod; from agent.prompts.ollama_system_prompt import SYSTEM_PROMPT; from agent.providers.ollama_agent import agent_tools; from agent.tools.db_tools import DbTools; from agent.tools.hub_tools import HubTools; from data.manager import DataManager; now=datetime.now(timezone.utc); print(ScoreMethod.score_needs_refresh(now - timedelta(hours=1), now), ScoreMethod.score_needs_refresh(now - timedelta(days=1, seconds=1), now), 'score_hubs' in [t.name for t in agent_tools()], 'Infer a 0-100' not in SYSTEM_PROMPT); factor=lambda n: {'name': n, 'points': 1.0, 'weight': 1.0, 'detail': 'test'}; keys=[DataManager.hub_key('Denver'), DataManager.hub_key('Miami')]; DbTools.set_fields({'city_key': keys[0]}, {'score': {'score': 80.0, 'factors': [factor('Snow days')], 'excluded': [], 'scored_at': now}}); DbTools.set_fields({'city_key': keys[1]}, {'score': {'score': 10.0, 'factors': [factor('Heavy rain days')], 'excluded': [], 'scored_at': now}}); cached=HubTools.score_hubs.invoke({'cities': ['Miami', 'Denver', 'Paris']}); print([type(x).__name__ for x in cached], [getattr(x, 'city', None) for x in cached], [getattr(x, 'score', None) for x in cached], [getattr(x, 'refreshed', None) for x in cached]); [DbTools.set_fields({'city_key': key}, {'score': None}) for key in keys]"
```

Expected: `False True True True` then `['HubScore', 'HubScore', 'ToolError'] ['Denver', 'Miami', None] [80.0, 10.0, None] [False, False, None]`. Paris is not a company hub. Denver stays ahead of Miami because 80 is higher, and neither score is refreshed. The command then clears those test scores. Result 2026-10-07: passed.

2. A score older than one day is recalculated and the next call reuses it. Uses the live weather, FEMA, and alert APIs.

```bash
python -c "from datetime import datetime, timedelta, timezone; from dotenv import load_dotenv; load_dotenv(); from agent.tools.db_tools import DbTools; from agent.tools.hub_tools import HubTools; from data.manager import DataManager; old=datetime.now(timezone.utc) - timedelta(days=2); DbTools.set_fields({'city_key': DataManager.hub_key('Denver')}, {'score': {'score': 1.0, 'factors': [{'name': 'Snow days', 'points': 1.0, 'weight': 1.0, 'detail': 'stale'}], 'excluded': [], 'scored_at': old}}); first=HubTools.score_hubs.invoke({'cities': ['Denver']})[0]; second=HubTools.score_hubs.invoke({'cities': ['Denver']})[0]; print(first.refreshed, first.score != 1.0, second.refreshed, second.score == first.score, second.scored_at == first.scored_at)"
```

Expected: `True True False True True`. The first call replaces the stale score. The second call is not a refresh and keeps the same score and timestamp. Result 2026-10-07: passed (`True True False True True 23.5`).

## Follow-up question only (2026-10-07 17:34)

When the hub or the hazard is missing, the prompt says the whole reply is one question, with no explanation of available data. Run from `server/`.

```bash
python -c "from agent.prompts.ollama_system_prompt import SYSTEM_PROMPT; print('one follow-up question' in SYSTEM_PROMPT, 'Do not explain what data you have or do not have' in SYSTEM_PROMPT, 'does not ask a question' in SYSTEM_PROMPT)"
```

Expected: `True True True`. Result 2026-10-07: passed.

## Current weather (2026-10-07 17:41)

`get_current_weather` calls the Open-Meteo forecast current block and is registered. The prompt says to use it for the weather now, not alerts. Run from `server/` (PowerShell), `$env:PYTHONIOENCODING = "utf-8"` first.

```bash
python -c "from agent.tools.weather_tools import WeatherTools; from agent.providers.ollama_agent import agent_tools; from agent.prompts.ollama_system_prompt import SYSTEM_PROMPT; r=WeatherTools.get_current_weather.invoke({'points': [{'latitude': 41.88, 'longitude': -87.63}]}); print(type(r[0]).__name__, r[0].condition, r[0].temperature_c, 'get_current_weather' in [t.name for t in agent_tools()], 'Do not answer that question with get_active_alerts' in SYSTEM_PROMPT)"
```

Expected: `CurrentWeather`, a condition such as `Clear`, a temperature in °C, then `True True`. Result 2026-10-07: passed (`CurrentWeather Clear 16.4 True True`).

## Answer built at each call (2026-10-07 18:09)

`_to_answer` is gone. `stream` builds `Answer` once for a structured reply and once for plain text. Run from `server/`.

```bash
python -c "import inspect; from agent.providers.ollama_agent import OllamaAgent; src=inspect.getsource(OllamaAgent.stream); print(not hasattr(OllamaAgent, '_to_answer'), src.count('Answer(') == 2)"
```

Expected: `True True`. Result 2026-10-07: passed.

## Tool prompt format (2026-10-07 18:16)

Each tool in the system prompt is listed as a name with input and output. Run from `server/`.

```bash
python -c "from agent.prompts.ollama_system_prompt import SYSTEM_PROMPT; print('- list_hubs:' in SYSTEM_PROMPT, '\tinput:' in SYSTEM_PROMPT, '\toutput:' in SYSTEM_PROMPT, 'Do not answer that question with get_active_alerts' in SYSTEM_PROMPT)"
```

Expected: `True True True True`. Result 2026-10-07: passed.

## Boundaries categories (2026-10-07 18:38)

Weather, general, and out-of-scope questions are separate. The `score_hubs` field list stays on the tool. Run from `server/`.

```bash
python -c "from agent.prompts.ollama_system_prompt import SYSTEM_PROMPT; print('not a Boundaries question' not in SYSTEM_PROMPT, 'Score_hubs' not in SYSTEM_PROMPT, 'not a company hub' in SYSTEM_PROMPT, 'Do not call a tool' in SYSTEM_PROMPT, 'Do not list tool names' in SYSTEM_PROMPT, 'cannot add, update, or remove hubs' in SYSTEM_PROMPT, 'one follow-up question' in SYSTEM_PROMPT)"
```

Expected: `True True True True True True True`. Result 2026-10-07: passed.

## Weather history tool text (2026-10-07 19:09)

The `get_weather_history` description is one sentence. Run from `server/`.

```bash
python -c "from agent.tools.weather_tools import WeatherTools; d=WeatherTools.get_weather_history.description; print('high wind' in d, 'one call' in d, 'total_snowfall_cm' not in d, len(d) < 120)"
```

Expected: `True True True True`. Result 2026-10-07: passed.

## Disaster, alert, and current weather tool text (2026-10-07 19:11)

Those three descriptions are one sentence each. Run from `server/`.

```bash
python -c "from agent.tools.weather_tools import WeatherTools; ds=[t.description for t in WeatherTools.get_tools() if t.name != 'get_weather_history']; print(all('one call' in d and len(d) < 140 for d in ds), len(ds))"
```

Expected: `True 3`. Result 2026-10-07: passed.

## Hub tool text (2026-10-07 19:21)

`list_hubs`, `score_hubs`, and `set_hub` descriptions are one sentence each. Run from `server/`.

```bash
python -c "from agent.tools.hub_tools import HubTools; ds=[HubTools.list_hubs.description, HubTools.score_hubs.description, HubTools.set_hub.description]; print(all(len(d) < 160 for d in ds), len(ds))"
```

Expected: `True 3`. Result 2026-10-07: passed.

## ScoreMethod (2026-10-07 19:25)

Scoring is static methods on `ScoreMethod`. The same formula test as 16:21, with `ScoreMethod.score_hub`. Run from `server/`.

```bash
python -c "from agent.scoring.score import ScoreMethod; print(callable(ScoreMethod.score_hub), callable(ScoreMethod.score_needs_refresh))"
```

Expected: `True True`. The formula command in the 16:21 section still prints `65.0 0.0 100.0 ['weather']`. Result 2026-10-07: passed.

## Request timeout and county match (2026-10-07 19:40)

`URL_TIMEOUT` is passed as a number. A county matches the FEMA area name exactly, so Harris does not include Harrison and Maricopa does not include tribal areas. Run from `server/`.

```bash
python -c "from dotenv import load_dotenv; load_dotenv(); import requests; from agent.tools.weather_tools import WeatherTools; from agent.tools.location_tools import LocationTools; seen=[]; 
class R:
 def __init__(self, url): self.url=url
 def raise_for_status(self): pass
 def json(self):
  if self.url and 'geocoding' in self.url: return {'results':[{'name':'Denver','latitude':39.7,'longitude':-104.9,'admin1':'Colorado','admin2':'Denver'}]}
  return {'DisasterDeclarationsSummaries':[{'disasterNumber':1,'incidentType':'Flood','designatedArea':'Harris (County)'},{'disasterNumber':2,'incidentType':'Flood','designatedArea':'Harrison (County)'},{'disasterNumber':3,'incidentType':'Fire','designatedArea':'Maricopa (County)'},{'disasterNumber':4,'incidentType':'Fire','designatedArea':'Salt River Pima-Maricopa Indian Community'},{'disasterNumber':5,'incidentType':'Fire','designatedArea':'Maricopa Indian Reservation (Ak Chin)'}]}
def fake(url, params=None, timeout=None, headers=None):
 seen.append(type(timeout).__name__); return R(url)
requests.get=fake
h=WeatherTools._disaster_one({'state_code':'TX','county':'Harris County'},2000)
m=WeatherTools._disaster_one({'state_code':'AZ','county':'Maricopa'},2000)
loc=LocationTools._one({'city':'Denver','state_code':'CO'})
print(seen==['float','float','float'], h.total_disasters, m.total_disasters, type(loc).__name__, loc.state_code)"
```

Expected: `True 1 1 Location CO`. Result 2026-10-07: passed.

## Server import with URL_TIMEOUT (2026-10-07 19:46)

`URL_TIMEOUT` is loaded from `.env` before the weather and location tools parse it, so `python server.py` can import those modules. Run from `server/`.

```bash
python -c "import server; from agent.tools.weather_tools import URL_TIMEOUT; print(type(URL_TIMEOUT).__name__, URL_TIMEOUT)"
```

Expected: `float 20.0`. Result 2026-10-07: passed.

## Evaluation set (2026-10-07 19:50)

Six cases in `server/eval/cases.py`. The grader checks tools, tool arguments, and answer text without calling the model. Run from `server/`.

```bash
python -c "from eval.check import grade_turn; from eval.cases import CASES; ok=grade_turn({'tools':['get_weather_history'],'forbid':['score_hubs'],'args':{'get_weather_history':['2025']},'pattern':r'\d+(\.\d+)?\s*(%|percent)','lacks':['sources:']},[{'type':'tool_call','name':'get_weather_history','args':{'start_date':'2025-01-01'}},{'type':'answer','answer':{'answer':'12.1% of days had snow.'}}]); bad=grade_turn({'no_tools':True,'question':True},[{'type':'tool_call','name':'list_hubs'},{'type':'answer','answer':{'answer':'Denver had snow.'}}]); print(ok, bad, len(CASES), len({c['name'] for c in CASES})==len(CASES))"
```

Expected: `[] ['called list_hubs', 'answer is not a question'] 6 True`.

The live run needs Ollama settings in `server/.env` and MongoDB. It calls the model and the public APIs.

```bash
python -m eval.run
```

Expected: one `pass` line per case, then `6/6 passed`, exit status 0. `python -m eval.run snow` runs only cases whose name contains `snow`. Result 2026-10-07: `5/6 passed`. `which hub` ("What is the hurricane risk?") called `list_hubs` and `get_disaster_history` and ranked the hubs instead of asking which hub.

## Not a hub wording (2026-10-07 19:54)

`not a hub` accepts "not a company hub" or "not one of our company hubs". A `list_hubs` call is allowed. Run from `server/`.

```bash
python -c "from eval.check import grade_turn; from eval.cases import CASES; turn=next(c for c in CASES if c['name']=='not a hub')['turns'][0]; events=[{'type':'tool_call','name':'list_hubs'},{'type':'answer','answer':{'answer':'Paris is not one of our company hubs.'}}]; print(grade_turn(turn, events))"
```

Expected: `[]`. Result 2026-10-07: passed.

## Missing hub asks which hub (2026-10-07 19:57)

A question that names no hub does not call a tool. The reply is one question asking which hub. Run from `server/`.

```bash
python -c "from agent.prompts.ollama_system_prompt import SYSTEM_PROMPT; print('does not name a hub' in SYSTEM_PROMPT, 'including list_hubs' in SYSTEM_PROMPT, 'question mark' in SYSTEM_PROMPT, 'Do not answer for every hub' in SYSTEM_PROMPT)"
```

Expected: `True True True True`. Result 2026-10-07: passed. Live `python -m eval.run "which hub"` passed: no tools, and the reply asked which hub.

## Weather app modules (2026-10-07 20:06)

`App.tsx` composes the header, chat, message card, and hub list. Types are in `src/types`. The hub fetch, agent stream, and tool-step update are in `src/services`. Run from `weather-app/`.

```bash
npx tsc -p tsconfig.app.json --noEmit
```

Expected: exit status 0. Result 2026-10-07: passed.

## Suggestions display (2026-10-07 20:40)

The empty chat shows suggestion buttons from `SuggestionsDisplay`. Run from `weather-app/`.

```bash
npx tsc -p tsconfig.app.json --noEmit
```

Expected: exit status 0.

## Selected hub stays in the dropdown (2026-10-07 20:44)

Choosing a hub leaves that city selected and tints the dropdown. The input text is unchanged. Sending with an empty input does nothing. Sending text that does not already name the hub adds the hub to the question. Run from `weather-app/`.

```bash
npx tsc -p tsconfig.app.json --noEmit
```

Expected: exit status 0.

## Friendly hub suggestions (2026-10-07 20:50)

Suggestion buttons name hubs from the loaded list. An empty hub list shows no buttons. Run from `weather-app/`.

```bash
npx tsc -p tsconfig.app.json --noEmit
```

Expected: exit status 0. Result 2026-10-07: passed.

## Project docs (2026-10-07 20:55)

The root README, the weather-app README, and `docs/architecture.md` describe the same system. Run from the repository root.

```bash
python -c "from pathlib import Path; root=Path('README.md').read_text(encoding='utf-8'); web=Path('weather-app/README.md').read_text(encoding='utf-8'); arch=Path('docs/architecture.md').read_text(encoding='utf-8'); print('FastAPI' in root, 'Vite' in web, 'browser' in arch and 'ScoreMethod' in arch and '## Components' in arch)"
```

Expected: `True True True`. Result 2026-10-07: passed.
