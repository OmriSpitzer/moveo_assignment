# Tests

Server unit tests live in `server/tests/`. They do not call Ollama, MongoDB, or the public weather APIs. Location and disaster HTTP calls are replaced with fakes.

Run all of them from anywhere:

```powershell
python server/tests/run.py
```

`run.py` discovers every test file in `server/tests/` and runs that suite. `server/` stays on the import path, so `agent`, `data`, and `eval` import.

The agent sessions are in [docs/conversations](conversations/README.md).

## Scoring

`tests/scoring/test_score.py`

- `test_score_hub_scales_missing_sections`: heavy rain, four hurricanes this year, and one Extreme alert score 65.0. A calm hub scores 0.0. A missing weather section is excluded and the rest scales to 100.0. Factor names are Snow days, Freezing days, Heavy rain days, High wind days, FEMA disasters, and Active alerts.
- `test_score_needs_refresh_after_one_day`: a missing timestamp needs a refresh. A score from the last hour does not. A score older than one day does.
- `test_score_methods_are_callable`: `ScoreMethod.score_hub` and `ScoreMethod.score_needs_refresh` are callable.

## Prompts

`tests/prompts/test_prompts.py`

- `test_answer_format_has_no_period_or_sources_line`: the prompt does not contain `Period: <dates>`, and it tells the model not to end with a Period or Sources line.
- `test_boundaries_split_weather_general_and_out_of_scope`: weather, general, and out-of-scope stay separate. A city that is not a hub is named as such. General answers do not call a tool. Tool names are not listed. Hubs cannot be added, updated, or removed. A missing hub is one follow-up question.
- `test_tools_are_listed_with_input_and_output`: each tool is a name with an input line and an output line. Current weather is not answered with `get_active_alerts`.
- `test_missing_hub_is_one_question`: a question that names no hub does not call a tool, including `list_hubs`. The reply asks which hub, ends with a question mark, and does not describe available data. A data answer does not ask a question.
- `test_technology_questions_are_out_of_scope`: technology questions are out of scope, tool names are not listed, data sources are not mentioned, and administrators are not mentioned as the people who change hubs.

`tests/test_prompts.py`

- `test_explain_one_score_is_detailed_and_simple`: a why or explain question for one hub skips the short-answer limits. It opens with the score, then one everyday bullet for each factor that added points. A factor with 0 points gets no bullet. The reply does not say the score was reused or that the breakdown is missing.

## Tools

`tests/tools/test_hub_tools.py`

- `test_registered_tools_are_read_only`: registered tools are `list_hubs`, `score_hubs`, `get_location`, `get_weather_history`, `get_disaster_history`, `get_active_alerts`, and `get_current_weather`. `set_hub` and `decline_request` are not registered.
- `test_set_hub_does_not_geocode`: `set_hub` does not call `get_location`. Its arguments are city, county, latitude, longitude, region, state, and state code.
- `test_hub_descriptions_are_one_sentence`: `list_hubs`, `score_hubs`, and `set_hub` each have a description shorter than 160 characters.
- `test_set_hub_writes_score_and_timestamp`: `set_hub` with a score writes that number and `scored_at`, and does not write `weather`.
- `test_stale_score_updates_through_set_hub_and_alerts`: a Denver score of 0 from two days ago is recalculated to 65.0 through `set_hub`, and one `score_alert` reports the change from 0.
- `test_fresh_score_is_kept`: a current score that already has factor points is returned unchanged and is not written.
- `test_missing_scored_at_is_refreshed`: a score of 0 with no `scored_at` is recalculated to 65.0 through `set_hub`, and one `score_alert` reports the change from 0.

`tests/tools/test_location_tools.py`

- `test_one_call_keeps_order_and_reports_a_miss`: one `get_location` call returns Denver (`CO`), Miami (`FL`), then a `ToolError` for an unknown city, in that order. The request timeout is a float.

`tests/tools/test_weather_tools.py`

- `test_timeout_is_a_float`: `URL_TIMEOUT` is a float greater than 0.
- `test_county_matches_the_area_name_exactly`: Harris matches Harris County and not Harrison County. Maricopa matches Maricopa County and not the tribal area names. Each request timeout is a float.
- `test_weather_history_description_is_one_sentence`: the description mentions high wind and one call, omits `total_snowfall_cm`, and is shorter than 120 characters.
- `test_other_weather_descriptions_are_one_sentence`: disaster history, active alerts, and current weather each mention one call and are shorter than 140 characters.

## Data

`tests/data/test_seed_hubs.py`

- `test_every_seed_hub_has_coordinates`: there are 14 seed hubs. Each score starts at 0 and none has `scored_at`. Each location has latitude and longitude. New York county is `New York`. Denver state code is `CO`.

## Eval

`tests/eval/test_check.py`

- `test_grade_turn_checks_tools_and_answer_text`: a snow-day turn that calls `get_weather_history` for 2025 and answers with a percent passes. A turn that calls `list_hubs` and does not end with a question fails with those two reasons. The set has 6 cases with unique names.
- `test_not_a_hub_accepts_either_wording`: "not one of our company hubs" passes the `not a hub` case, and a `list_hubs` call is allowed.

## Agent

`tests/agent/test_stream.py`

- `test_fake_stream_ends_with_an_answer`: `FakeAgent` yields `tool_call`, `tool_result`, then an answer whose text is `fake answer` and whose model is `fake`.
- `test_ollama_stream_builds_answer_in_two_places`: `OllamaAgent` has no `_to_answer`. `stream` builds `Answer` once for a structured reply and once for plain text.

## Score alerts

`tests/test_score_alerts.py`

- `test_alerts_sit_beside_the_chat_and_vanish`: a `score_alert` is kept out of the chat message. The yellow list scrolls itself with `scrollTop` and does not call `scrollIntoView`. The chat still scrolls when its messages change.

## Voice

`tests/test_voice_input.py`

- `test_pause_sends_and_a_click_only_stops`: after the listen pause the microphone marks the turn to send, then stops. A click while listening clears that mark and stops without sending. A recognition error does not send. The chat sends that transcript when the pause ends.

## Runner

`tests/run.py` discovers every `test*.py` file in `server/tests/` and runs that suite. It exits with the suite status.

Result 2026-10-08: `Ran 23 tests` ... `OK`.
