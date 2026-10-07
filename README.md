# Weather Risk Intelligence Agent

A chat for logistics analysts who need to know which US distribution hubs are most exposed to weather. The browser talks only to the API. The API runs an agent that calls public weather and hazard services, scores hubs in code, and answers in plain language.

## Stack

| Layer | Technology |
| --- | --- |
| Web | React 19, TypeScript, Vite, Tailwind CSS |
| API | FastAPI, Server-Sent Events |
| Agent | LangChain, Ollama, structured JSON answers |
| Data | MongoDB, one `hubs` collection |
| External data | Open-Meteo geocoding, archive, and forecast; OpenFEMA; National Weather Service alerts |

## Run

Start the API from `server/`. Settings live in `server/.env` (model, Ollama, MongoDB, request timeout, and the public API URLs).

```bash
python server.py
```

Start the UI from `weather-app/`. Vite proxies `/api` to `API_URL`, or to `http://127.0.0.1:8000` when that variable is unset.

```bash
npm install
npm run dev
```

Open the local URL Vite prints.

The API image is the root `Dockerfile`. From the repository root:

```bash
docker compose -f docker-compose.yaml up --build
```

The API is at http://localhost:8000. Compose reads `server/.env` and listens on `0.0.0.0:8000`. The chat still runs with `npm run dev` in `weather-app/`. If Ollama or MongoDB is on the host, point `BASE_URL` and `MONGODB_URI` at `host.docker.internal` instead of `127.0.0.1`.

## Repository

```
server/         API, agent, tools, scoring, evaluation
weather-app/    chat UI
docs/           requirements, architecture, tests
```

## Docs

- [Architecture](docs/architecture.md)
- [Requirements](docs/requirements.md)
- [Tests](docs/tests.md)

From `server/`, `python -m eval.run` grades a small set of questions against the live agent.
