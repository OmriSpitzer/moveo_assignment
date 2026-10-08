# Requirements

## Requirements

- [x] Answer hub questions using public weather and hazard APIs
- [x] Rank and compare hubs with an explicit KPI in code
- [x] Explain the reasoning in plain language
- [x] State assumptions, uncertainty, and what is out of scope
- [x] Keep conversational follow-ups in one session
- [x] Chat UI talks to the agent only through the API
- [x] Model output uses defined structured JSON 
- [x] Include a small evaluation set and a way to run it

Bonus, only after every item above is done:

- [x] Voice input
- [x] Scheduled or webhook alert when a hub's risk score changes
- [x] Deployed URL



### Current status (Done, Work on, Not implemented)


| Requirement                     | Status |
| ------------------------------- | ------ |
| Public weather and hazard APIs  | Done   |
| KPI in code                     | Done   |
| Plain-language reasoning        | Done   |
| Assumptions, uncertainty, scope | Done   |
| Follow-ups in one session       | Done   |
| UI only through the API         | Done   |
| JSON schema                     | Done   |
| Eval set                        | Done   |




## Work log



### 2026-10-07


| Time  | Work                                                              |
| ----- | ----------------------------------------------------------------- |
| 10:30 | Documentation and file structure.                                 |
| 11:08 | Ollama agent, fake provider, and structured answer.               |
| 11:28 | Model returns `LLMAnswer` only; code fills the rest of `Answer`.  |
| 12:18 | Location, weather, disaster, and alert tools.                     |
| 12:24 | Agent SSE stream and React chat through the API.                  |
| 12:33 | Routes use the real Ollama agent and `LLMAnswer`.                 |
| 12:34 | `RUN_LIMIT` is read from `server/.env`.                           |
| 12:40 | One `get_hub_risk` call; stream errors stay out of the answer.    |
| 12:43 | Prompt boundaries for precise, general, and out-of-scope answers. |
| 12:46 | Plain text that validates as `LLMAnswer` counts as the answer.    |
| 12:47 | Answer format is one sentence plus short bullets.                 |
| 12:50 | Requirements status reviewed against the system.                  |
| 13:15 | MongoDB hubs, hub tools, and the hub picker.                      |
| 13:55 | Atlas connected; weather-history storage fixed.                   |
| 16:00 | Collection name read from `HUBS_COLLECTION`.                      |
| 16:08 | Collection name stays in `DataManager`.                           |
| 16:12 | `get_hub_risk` description shortened to one sentence.             |
| 16:21 | Static 0-100 hub score in code.                                   |
| 16:27 | `get_hub_risk` always fetches and leaves the score empty.         |
| 16:33 | `HubRisk` no longer includes location.                            |
| 16:38 | `get_hub_risk` removed; separate read tools per question.         |
| 16:43 | Location and weather tools fetch a list in one call.              |
| 16:46 | Hub document schema added.                                        |
| 16:48 | Hub document schema reverted.                                     |
| 16:50 | `set_hub` stores a location from `get_location`.                  |
| 16:51 | `get_location` geocodes a city list in one call.                  |
| 16:55 | Seed hubs include coordinates.                                    |
| 16:58 | Requirements status checked again.                                |
| 17:01 | One in-memory thread per chat.                                    |
| 17:07 | `decline_request` added for deletions and out-of-scope topics.    |
| 17:11 | `decline_request` removed; the model answers those itself.        |
| 17:14 | `GET /` and `/json/version` return 200; `set_hub` unregistered.   |
| 17:16 | Technology questions are out of scope.                            |
| 17:19 | Removed the Period and Sources closing line.                      |
| 17:23 | `score_hubs` ranks in code and reuses a score for one day.        |
| 17:34 | A missing hub or hazard is one follow-up question.                |
| 17:35 | Chat shows only the tool step still running.                      |
| 17:41 | `get_current_weather` for weather now.                            |
| 18:09 | `stream` builds `Answer` for structured and plain-text replies.   |
| 18:16 | Tool prompt lists name, input, and output.                        |
| 18:38 | Boundaries split into weather, general, and out of scope.         |
| 18:44 | Seed hub layout aligned.                                          |
| 19:09 | `get_weather_history` description shortened to one sentence.      |
| 19:11 | Disaster, alert, and current-weather descriptions shortened.      |
| 19:21 | Hub tool descriptions shortened to one sentence.                  |
| 19:25 | Scoring moved onto `ScoreMethod`.                                 |
| 19:32 | Timeout and county matching reviewed; no code change.             |
| 19:40 | Timeout is a float; county match is exact.                        |
| 19:46 | Env file loads before `URL_TIMEOUT` is read.                      |
| 19:50 | Small eval set and runner.                                        |
| 19:54 | "Not a hub" accepts either wording.                               |
| 19:57 | A question with no hub asks which hub and calls no tool.          |
| 20:06 | Weather app split into components, services, and types.           |
| 20:40 | Empty-chat suggestions moved into `SuggestionsDisplay`.           |
| 20:44 | Hub picker keeps the choice and adds it to the question.          |
| 20:50 | Suggestions are questions built from the loaded hubs.             |
| 20:55 | READMEs and architecture doc rewritten.                           |
| 21:00 | Voice input inserts a transcript; Send stays separate.            |
| 21:10 | Docker image for the API and the web app.                         |
| 21:15 | Web container no longer requires the API at startup.              |
| 21:19 | Docker image is the API only, on port 8000.                       |
| 21:23 | API image trusts Atlas TLS certificates.                          |
| 21:28 | Removed the image CA package; Atlas allows this host.             |
| 21:33 | API image builds the chat and serves it at `/`.                   |
| 21:40 | Voice writes words into the box while listening.                  |
| 21:50 | Darker chat background; unit tests live in `server/tests/`.       |
| 21:52 | `AGENTS.md` points at `docs/test.md` and `server/tests/`.         |
| 21:55 | `docs/test.md` lists every unit test by subject.                  |
| 22:00 | `server/tests/run.py` runs the suite.                             |




### 2026-10-08


| Time  | Work                                                                       |
| ----- | -------------------------------------------------------------------------- |
| 08:10 | Voice sends after the listen pause; a click while listening only stops.    |
| 08:20 | Architecture redrawn in Mermaid, with company hubs as the focus.           |
| 08:20 | Exported 21 agent sessions to `docs/conversations`.                        |
| 08:23 | System block is Agent; tools grouped as hub, location, and weather.        |
| 08:28 | Reason and Act sit in a Loop block.                                        |
| 08:30 | Work log entries shortened; `AGENTS.md` says to keep them to one sentence. |
| 08:39 | `server/agent/structure.md` maps the agent package; architecture and the README follow it and show technology icons under the title. |
| 08:42 | Technology lines under those titles are pills with the name and the version pinned in the repo. |
| 08:45 | `weather-app/README.md` has the same pills for the chat stack. |
| 08:48 | Refreshed `docs/conversations` to 22 sessions and linked that folder from the other docs. |
| 08:57 | Seed scores start at 0. A score older than a day is saved through `set_hub`, and a change shows as a yellow alert beside the chat. |
| 09:05 | Seed hubs have no `scored_at`, so the first scoring run always recalculates them. |
| 09:13 | An explain question for one hub states the score, then one simple bullet for each factor that added points. |
| 09:17 | A why question explains the stored factor points. A score saved without those points is recalculated. |
| 09:27 | `python eval\run.py` from `server/` imports `eval.cases` instead of `server.eval`. |
| 09:31 | Refreshed `docs/conversations` so this session includes the later turns. |


