# Architecture

Analysts use a React chat. The chat calls one FastAPI service. That service runs an Ollama agent with read-only tools. Tools read the `hubs` collection and, when a question needs it, public weather and hazard APIs. Ranking uses a score computed in code, not by the model. The model explains the result. Follow-up turns stay on one in-memory thread.

```
browser
  -> Vite /api proxy
  -> FastAPI
  -> agent tools
  -> MongoDB hubs, Open-Meteo, OpenFEMA, NWS
  -> score in code
  -> SSE answer
```

## Components

**Web client** (`weather-app`). `App.tsx` holds the session and the composer. `Header`, `ChatDisplay`, `SuggestionsDisplay`, `MessageCard`, `HubsDropUp`, and `VoiceInput` are the screen. `VoiceInput` sits beside Send. A click opens the microphone for English. A pause of about a second ends the recording and inserts the transcript into the text box. The user sends that text with Send. `services/api.ts` calls `GET /api/hubs` and `POST /api/agent/stream`. `services/chat.ts` turns each stream event into the tool step on the assistant card. Types live in `types`.

`ChatDisplay` shows `SuggestionsDisplay` when the chat is empty. Those questions are built from the loaded hubs, and none are shown when the hub list is empty. `HubsDropUp` keeps the chosen hub and uses a tinted background. Choosing a hub does not write it into the input. A send with no input text is ignored. When the typed text does not already name the chosen hub, that hub is added to the question sent to the agent.

**API** (`server/server.py`, `server/routes/agent_routes.py`). The router is mounted at `/api`.

| Method | Path | Role |
| --- | --- | --- |
| GET | `/` and `/json/version` | Name the API so port probes are not 404 |
| GET | `/api/health` | Health check |
| GET | `/api/hubs` | Hub list from the collection |
| GET | `/api/agent` | One-shot reply |
| POST | `/api/agent/stream` | Server-Sent Events for one turn |

Stream events are `tool_call`, `tool_result`, `answer`, `error`, and `done`. The running process uses the real Ollama agent (`Agent(is_fake=False)`). `FakeAgent` exists for tests that do not need a model.

**Agent.** `agent/agent.py` picks `OllamaAgent` or `FakeAgent`. `OllamaAgent` uses LangChain `create_agent`, `ChatOllama`, and `ToolStrategy(LLMAnswer)`. Code builds the full `Answer` (`timestamp`, `model`, `prompt`, `answer`). A plain-text final reply is accepted when it validates as `LLMAnswer`. A call-limit failure is an `error` event, not an answer.

Registered tools are `list_hubs`, `score_hubs`, `get_location`, `get_weather_history`, `get_disaster_history`, `get_active_alerts`, and `get_current_weather`. `set_hub` is not registered.

## Repository structure

```
server/
  server.py                 process entry, dotenv, FastAPI
  routes/agent_routes.py    HTTP and the SSE stream
  agent/agent.py            provider switch
  agent/providers/          Ollama agent, fake agent, base type
  agent/prompts/            system, tool, and boundary text
  agent/tools/              hubs, location, weather, database helpers
  agent/scoring/            weights and ScoreMethod
  agent/schema/             answer and tool-result models
  data/                     MongoDB manager and hub seed
  eval/                     cases, grader, runner
weather-app/
  src/App.tsx
  src/components/
  src/services/
  src/types/
docs/
  requirements.md
  architecture.md
  tests.md
```

## Data storage

MongoDB (`server/data/manager.py`), chosen because the app will run on the internet with a hosted database. One collection, `hubs`, one document per hub:

- `city`, `city_key` (unique, lowercase), `state_code`, `region`, optional `county` override, `created_at`. The seed includes `location` (latitude, longitude, county) for every hub. Existing hub documents missing coordinates get that seed location on startup.
- The agent does not add or update hubs. It calls `get_location` only when `list_hubs` did not already return coordinates. `get_location` takes the city list and resolves every city in parallel inside that one call. It then calls `get_weather_history`, `get_disaster_history`, `get_active_alerts`, and `get_current_weather` only for the sections a question needs. `get_current_weather` is the Open-Meteo forecast current block, used when the question asks what the weather is now. Each of those tools takes a list and fetches every place in that one call.

## Scoring

`agent/scoring/factors.py` holds static weights. `ScoreMethod.score_hub` in `agent/scoring/score.py` turns weather, FEMA history, and active alerts into a 0-100 `RiskScore`: weather 50 (snow, freezing, heavy rain, high wind), disasters 40, alerts 10. A section that failed is omitted and the remaining weights are scaled to 100. `score_hubs` calls it when a question ranks or compares hubs. The score is stored on the hub document with `scored_at`. A score older than one day is recalculated; a newer score is reused.

## Session

The Ollama agent stores each chat in process memory (`InMemorySaver`), keyed by `thread_id`. A later request with the same id continues that chat and adds only the new message. A thread with nothing saved yet uses the message list on the request. The memory is gone when the server process stops.

## Assumptions and scope

The agent is registered with read tools only: `list_hubs`, `score_hubs`, `get_location`, and the weather, disaster, alert, and current-weather getters. A weather question may call tools. A general question (how the score works, or a greeting) is answered without a tool. A question about technologies, or a request to add, update, or remove hubs, is answered by the model itself, in one or two friendly sentences, with no tool call and no list of tool names. A city that is not a hub is named as such, with the hubs in that region, and no data is fetched for it. `GET /` and `GET /json/version` on the API port return the API name so those probes are not 404. Weather answers name a fact once, and mention total snowfall only when the user asks how much snow fell. If the hub or the hazard is missing, the reply is one follow-up question and does not describe what data is available. A question that names no hub does not call a tool, including `list_hubs`, and asks which hub.

## Evaluation

`server/eval/cases.py` holds a small set of questions. From `server/`, `python -m eval.run` sends each turn to the Ollama agent on one in-memory thread and grades the streamed tools and answer text (`server/eval/check.py`). A name argument runs only the matching cases. The process exits with status 1 when any case fails.
