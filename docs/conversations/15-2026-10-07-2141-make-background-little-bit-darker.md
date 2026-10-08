# make background a little bit darker.

- Session: `5377992d-7414-4e1d-9c49-a791d5eb65be`
- Started: 2026-10-07 21:41

## You

make background a little bit darker.
make all unit testing in the server at tests folder. add folders if needed. document it in test.md (also remove all content that is now in tests.md)

## Agent

I'll darken the background and move the server unit tests into a `tests` folder, then document that in `test.md` and clear the matching content from `tests.md`. First I'm reading the project docs and locating the current tests and background styles.

The docs are a long list of one-off server checks. Next I’ll look at the app background and how the server is laid out so the unit tests can live in a `tests` folder.

The page background is `bg-slate-50`. I’ll darken that, then read the server modules so the new `tests` folder matches the code that actually runs.

The page background is `bg-slate-50`. I’ll darken that, then move the server checks that can run without live services into `server/tests` and document them in `docs/test.md`.

The background is now a step darker. I’m adding the server unit tests under `server/tests`, documenting them in `docs/test.md`, and clearing `docs/tests.md`.

The test folders were shadowing the server packages. I’ll run discovery from the server root so `agent`, `data`, and `eval` import correctly.

The chat background is a step darker, and the server unit tests now live in `server/tests`.

The main screen uses `bg-slate-200` instead of `bg-slate-50`. I could not open the running page, so this is the class change only.

From `server/`, run:

```bash
python -m unittest discover -s tests -t .
```

That run passed: **21 tests**. The `-t .` flag keeps `server/` on the import path so the test folders do not hide the `agent`, `data`, and `eval` packages.

| Folder | What it checks |
| --- | --- |
| `tests/scoring` | Score formula and the one-day refresh window |
| `tests/prompts` | Boundaries and the tool list |
| `tests/tools` | Registered tools, descriptions, county match, timeout, location order |
| `tests/data` | Seed hub coordinates |
| `tests/eval` | Grader |
| `tests/agent` | Fake stream and where `Answer` is built |

How to run them is in `docs/test.md`. `docs/tests.md` is empty. These tests do not call Ollama, MongoDB, or the public weather APIs.

Tools: `Read`, `Glob`, `Grep`, `StrReplace`, `Write`, `Shell`

## You

update AGENT.md

## Agent

The test docs moved to `docs/test.md` and the suite lives under `server/tests`. I’ll update `AGENTS.md` so those instructions match.

`AGENTS.md` now follows the unit-test layout from the last change.

Before implementing, read `docs/test.md` along with the requirements and architecture. New tests go in `server/tests/`, with a new folder when that area does not already have one, and the run command is recorded in `docs/test.md`. From `server/`, that command is `python -m unittest discover -s tests -t .`.

Tools: `Glob`, `Read`, `StrReplace`

## You

show in @docs/test.md all test cases (list all by subject) add in tests a ps1 script to run all tests

## Agent

I’ll list every unit test by subject in `docs/test.md` and add a PowerShell script under `server/tests` that runs the full suite.

The suite has 21 cases across six subjects. I’ll list each one in `docs/test.md` and add `server/tests/run-tests.ps1` to run them all.

`docs/test.md` now lists all 22 cases by subject: scoring, prompts, tools, data, eval, agent, and the runner.

`server/tests/run-tests.ps1` moves to `server/` and runs the suite. From the repository root:

```powershell
powershell -File server/tests/run-tests.ps1
```

That run passed: 22 tests, all ok.

Tools: `Grep`, `Read`, `Write`, `StrReplace`, `Shell`
