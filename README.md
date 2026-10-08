# Weather Risk Intelligence Agent

![React 19.2.8](https://img.shields.io/badge/React-19.2.8-61DAFB?style=for-the-badge&logo=react&logoColor=black) ![TypeScript 6.0.2](https://img.shields.io/badge/TypeScript-6.0.2-3178C6?style=for-the-badge&logo=typescript&logoColor=white) ![Vite 8.3.0](https://img.shields.io/badge/Vite-8.3.0-646CFF?style=for-the-badge&logo=vite&logoColor=white) ![Tailwind CSS 4.3.3](https://img.shields.io/badge/Tailwind_CSS-4.3.3-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white) ![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white) ![FastAPI 0.129.0](https://img.shields.io/badge/FastAPI-0.129.0-009688?style=for-the-badge&logo=fastapi&logoColor=white) ![LangChain 1.4.3](https://img.shields.io/badge/LangChain-1.4.3-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white) ![Ollama 1.1.0](https://img.shields.io/badge/Ollama-1.1.0-ffffff?style=for-the-badge&logo=ollama&logoColor=black) ![MongoDB 4.17.0](https://img.shields.io/badge/MongoDB-4.17.0-47A248?style=for-the-badge&logo=mongodb&logoColor=white)

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

The image serves the chat at `/` and the API under `/api`, on port 8000. Compose reads `server/.env`. Locally, `npm run dev` in `weather-app/` is still the dev chat. If Ollama or MongoDB is on the host, point `BASE_URL` and `MONGODB_URI` at `host.docker.internal` instead of `127.0.0.1`.

## Repository

```
server/         API and the agent package
weather-app/    chat UI
docs/           requirements, architecture, tests, agent sessions
```

## Docs

- [Architecture](docs/architecture.md)
- [Agent structure](server/agent/structure.md)
- [Requirements](docs/requirements.md)
- [Tests](docs/test.md)
- [Agent sessions](docs/conversations/README.md)

From `server/`, `python -m eval.run` grades a small set of questions against the live agent.
