# Include a small evaluation set and a way to run it

- Session: `fe60d785-73bd-493b-96f7-32da7aaa2f12`
- Started: 2026-10-07 19:42

## You

Include a small evaluation set and a way to run it

how to create an eval for the agent?

## Agent

I'll look at the requirements, architecture, and how the agent is wired so the eval set matches the existing flow.

The eval item is still open. I'll read how the agent answers so the set checks the behavior the assignment actually needs.

The eval should be a short list of real questions, run through the same agent the API uses, and scored on the tools it called and the answer text. I'll add that set and a runner next to the agent.

The eval note landed in the middle of the assumptions section. I'll move it to its own section.

The grader check passed. Next I’ll run the six cases against the live agent.

Five cases passed. “How many snow days were there last year?” was read as all hubs, so I’ll point that case at a question that names no hub.

An eval for this agent is a fixed set of questions run through the same Ollama agent the API uses. Each turn is graded on what came back over the stream: which tools ran, what arguments they got, and whether the answer text matches the check. The model does not grade itself.

The set is in `server/eval/cases.py`. Six cases:

| Case | What it checks |
| --- | --- |
| snow days | `get_weather_history` for 2025, a percentage in the answer, no disaster or alert tools |
| rank hubs | one `score_hubs` call for Miami and Houston, both cities and a score in the answer |
| not a hub | Paris is called out as not a company hub, and no weather data is fetched |
| out of scope | no tools, and the reply stays on weather and hubs |
| which hub | a question with no hub named should be one follow-up question and no tools |
| follow up | weather in Denver now, then snow days for that hub on the same thread |

Run it from `server/`:

```bash
python -m eval.run
```

A name filters the set, for example `python -m eval.run snow`. A failed case prints the tools and the answer, and the process exits with status 1.

The grader itself does not call the model. That check passed: `[] ['called list_hubs', 'answer is not a question'] 6 True`.

The live run was **5/6 passed**. `which hub` ("What is the hurricane risk?") called `list_hubs` and `get_disaster_history` and ranked every hub, instead of asking which hub.

Tools: `Read`, `Glob`, `Grep`, `Write`, `StrReplace`, `Shell`

## You

should the eval be in test as a pytest?

## Agent

The eval and the existing test style are different jobs. I’ll check how this repo runs checks today so the recommendation matches that.

Keep the live eval as `python -m eval.run`. This repo has no pytest suite: every check in `docs/tests.md` is a `python -c` command you run by hand. The eval does not fit that shape.

The six cases call the real Ollama agent, MongoDB, and the public weather APIs. The last full run took about 70 seconds, and `which hub` failed because the model ranked every hub instead of asking which one. A pytest file would turn that model miss into a red test run. You want to run this set when you are judging the agent, and you want the printed tools and answer when a case fails. `eval/run.py` already does that, including `python -m eval.run snow` for one case.

The part that is a real test is `grade_turn` in `server/eval/check.py`. It never calls the model. That check already lives in `docs/tests.md` and passed: an answer of `12.1%` grades clean, and a tool call on a no-tool question returns `called list_hubs` and `answer is not a question`. If you add pytest later, that grader is the function to put in a test. The cases in `server/eval/cases.py` should stay data that the runner loads.

Tools: `Read`, `Grep`

## You

@c:\Users\עומרי_שפיצר\.cursor\projects\c-GitProjects-moveo-assignment\terminals\1.txt:429-445 the agent can answer a question about the weather thats not in hub

## Agent

The Paris reply is a refusal, and the eval marked it wrong on wording. I’ll check the case check against what the prompt actually asks for.

The Paris turn did the right thing. The eval failed on the exact words, not on the behavior.

The prompt says a city that is not a hub is named as such, the hubs are listed, and no weather data is fetched. The run called only `list_hubs` and replied:

> Paris is not one of our company hubs. Our hubs are located in cities across the Midwest, South, West, and Northeast regions...

That is an answer to a weather question about a place that is not a hub. It did not call `get_weather_history` or the other data tools.

`not a hub` in `server/eval/cases.py` requires the substring `not a company hub`. The reply says `not one of our company hubs`, so `grade_turn` reports `answer missing not a company hub` and the case fails.

Loosen that check to accept either wording, for example `has_any`: `not a company hub` and `not one of our company hubs`. The tool check can stay as it is: `list_hubs` is allowed, and the weather, disaster, alert, and score tools are not.

Tools: `Read`

## You

where in the prompt of the agent it says he cant check on other cities in the us?

## Agent

The limit is in the system prompt, not in the tools. I’ll point at the exact lines.

It is in the boundaries prompt, in `server/agent/prompts/boundaries_prompt.py`. This line is the ban:

```10:10:server/agent/prompts/boundaries_prompt.py
- If the user asks about a city that is not a hub, say it is not a company hub and name the hubs in the same region. Do not fetch data for it.
```

Two other lines say the same limit. The weather section defines a weather question as hub conditions only:

```4:4:server/agent/prompts/boundaries_prompt.py
- A weather question is about a weather concept, a hazard type, or the conditions and risk for one or more hubs.
```

The out-of-scope reply is told to stay on the hub list:

```21:21:server/agent/prompts/boundaries_prompt.py
- The reply is one or two friendly sentences. Say you only help with weather and hazard risk for the hubs already on the list, then offer to list them or compare that risk. Do not mention administrators.
```

The tool prompt repeats it on `list_hubs` in `server/agent/prompts/tool_prompt.py`: "Answers cover only these hubs."

The weather tools themselves take any coordinates. Nothing in the tool code rejects a US city that is not a hub. The model skips those calls because the prompt says not to fetch data for a city that is not a hub.

Tools: `Read`

## You

so why did it fail?

## Agent

It failed the wording check. The tool check passed.

The `not a hub` case requires the answer to contain the exact substring `not a company hub`. The model wrote "Paris is **not one of our** company hubs." Those words are not that substring, so `grade_turn` reported `answer missing not a company hub`.

The tools were what the prompt asks for. It called only `list_hubs` and did not call `get_weather_history` or the other data tools. That part of the case passed.

## You

change tests

## You

change tests

## Agent

The Paris case failed on the exact phrase. I’ll loosen that check so “not one of our company hubs” counts as a pass.

The `not a hub` case now accepts both phrasings. "Paris is not one of our company hubs" grades as a pass, and so does "not a company hub."

The tool rule is unchanged: `list_hubs` is allowed, and the weather, disaster, alert, and score tools are not. The grader check printed `[]`.

Tools: `Read`, `StrReplace`, `Shell`

## You

@c:\Users\עומרי_שפיצר\.cursor\projects\c-GitProjects-moveo-assignment\terminals\1.txt:502-510 fix this

## Agent

The `which hub` case failed because the model ranked every hub instead of asking which one. The prompt already requires one follow-up question, so I’ll make that rule explicit and re-run the case.

The model stopped calling tools and asked which hub. The case still failed because that sentence has no question mark. I’ll require the question mark in the prompt and run the case again.

`which hub` now passes. A question that names no hub no longer fetches data for every hub.

The weather boundaries now say: if the question does not name a hub, do not call a tool, including `list_hubs`. The whole reply is one question asking which hub, and it ends with a question mark.

The live case returned no tool calls and asked which hub. `1/1 passed`.

Tools: `Read`, `StrReplace`, `Shell`, `Grep`
