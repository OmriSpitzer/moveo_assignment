# based on the @assignment.pdf create a breif AGENTS.md, with titles: structure, requirments (as checklist), boundries. make it modern and

- Session: `d634695d-7ffd-4bae-9f06-b0d0235a37fb`
- Started: 2026-10-07 10:20

## You

based on the @assignment.pdf create a breif AGENTS.md, with titles: structure, requirments (as checklist), boundries. make it modern and most understanding for other agents to read

## Agent

I'll read the assignment and the rule-writing guidance, then draft a short AGENTS.md with structure, a requirements checklist, and boundaries.

The assignment is a one-day weather-risk agent. I'll check the repo so the structure section matches what's actually here.

The repo is only a stub, so I'll write a short AGENTS.md that tells other agents the target layout, the assignment checklist, and what to leave out.

`AGENTS.md` is at the repo root. It is written for another agent picking up the assignment cold.

**Structure** — a small Python layout: chat UI, API, agent, deterministic scoring, data, eval, and the architecture doc. The model explains scores; it does not compute them.

**Requirements** — a checklist of the must-haves (public weather data, coded KPI, follow-up chat, JSON schema, eval set, README, architecture doc, session record). Voice, alerts, and a deployed URL sit in a separate bonus list that only starts after the core list is done.

**Boundaries** — one day, a handful of US hubs, and only the hazards in the sample questions. Missing or proxy data must be called out, and extra hubs or features stay out unless a sample question needs them.

Tools: `Read`, `Glob`, `Write`

## You

Boundaries

Don't change the overall architecture of the system

Don't infer, check with user if you do not understand

Don't change comments

i meant boundries like this

## Agent

I'll rewrite the Boundaries section as short "Don't" rules for agent behavior, starting with your three.

I'll replace the Boundaries section with their three rules, keeping the same style, and maybe add one or two more in that vein without overloading it.

The file has changed since I wrote it, so I'll read it again before editing.

Your three rules are already in the file. I'll keep them exactly as written and add a few project-specific rules in the same style below them.

The user already edited the Boundaries section themselves, removing README/doc items, showing exactly the style they want. I should respect their edits and not restore what they removed, maybe just add a couple project-specific items in that same minimal style after their three.

The Boundaries section of `AGENTS.md` now lists agent-behavior rules in your style. Your three are unchanged at the top, and I added four project-specific ones below them:

- Don't change the overall architecture of the system
- Don't infer, check with user if you do not understand
- Don't change comments
- Don't let the LLM compute or decide scores; ranking lives in `app/scoring`
- Don't invent data; use public APIs and say when data is missing or a proxy
- Don't add hubs, hazards, or features the sample questions don't need
- Don't start bonus items until every core requirement is done

The other sections are as you edited them, including the requirement items you removed. If you only want your original three, delete the last four lines.

Tools: `StrReplace`, `Read`
