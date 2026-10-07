# Weather Risk Intelligence Agent

Help logistics analysts decide which US distribution hubs to upgrade for weather resilience. Answer questions, rank hubs, and explain the reasoning. A narrow path that runs beats a broad one that does not.

## Structure

Python. One app an interviewer can start and talk to.


Flow: HTTP client → API → agent tools → public weather/hazard APIs and `agent/scoring` → structured result → explanation in the API response.

## Boundaries

Before implementing, read `docs/requirements.md`, `docs/architecture.md`, `docs/tests.md` :

- Don't change the overall architecture of the system
- Don't infer, check with user if you do not understand
- Don't change comments
- Requirements live in `docs/requirements.md`. Update their status there, and add a timestamped entry to its work log for all work done
- Change the architecture in `docs/architecture.md` only to the specific.
- For each implementation, require a test to run in `docs/tests.md`

