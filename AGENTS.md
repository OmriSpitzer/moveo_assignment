# Weather Risk Intelligence Agent

Help logistics analysts decide which US distribution hubs to upgrade for weather resilience. Answer questions, rank hubs, and explain the reasoning. A narrow path that runs beats a broad one that does not.

## Boundaries

Before implementing, read `docs/requirements.md`, `docs/architecture.md`, `docs/test.md` :

- Don't change the overall architecture of the system
- Don't infer, check with user if you do not understand
- Don't change comments
- Requirements live in `docs/requirements.md`. Update their status there, and add a timestamped entry to its work log for all work done
- Change the architecture in `docs/architecture.md` only to the specific.
- Unit tests live in `server/tests/`. Add a folder there when the area does not already have one. For each implementation, add a test in that tree and list the case by subject in `docs/test.md`. Run all tests with `python server/tests/run.py`.

