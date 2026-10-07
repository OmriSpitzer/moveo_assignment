"""
    Small evaluation set for the weather agent.

    Each case is one chat. A turn lists the user text and the checks for that reply:
    tools the agent must call, tools it must not call, substrings the answer must
    or must not contain, and whether the whole reply is one question.
"""

CASES = [
    {
        "name": "snow days",
        "turns": [
            {
                "content": "What percentage of days in Denver in 2025 had snowfall?",
                "tools": ["get_weather_history"],
                "forbid": ["get_disaster_history", "get_active_alerts", "get_current_weather", "score_hubs"],
                "args": {"get_weather_history": ["2025"]},
                "pattern": r"\d+(\.\d+)?\s*(%|percent)",
                "lacks": ["sources:"],
            }
        ],
    },
    {
        "name": "rank hubs",
        "turns": [
            {
                "content": "Rank Miami and Houston by weather risk. Which should we upgrade first?",
                "tools": ["score_hubs"],
                "args": {"score_hubs": ["Miami", "Houston"]},
                "has": ["Miami", "Houston"],
                "pattern": r"\d",
            }
        ],
    },
    {
        "name": "not a hub",
        "turns": [
            {
                "content": "How many snow days did Paris have last year?",
                "forbid": [
                    "get_location", "get_weather_history", "get_disaster_history",
                    "get_active_alerts", "get_current_weather", "score_hubs",
                ],
                "has_any": ["not a company hub", "not one of our company hubs"],
            }
        ],
    },
    {
        "name": "out of scope",
        "turns": [
            {
                "content": "Which database and programming language is this agent built with?",
                "no_tools": True,
                "lacks": ["get_weather_history", "list_hubs", "score_hubs"],
                "has_any": ["weather", "hub"],
            }
        ],
    },
    {
        "name": "which hub",
        "turns": [
            {
                "content": "What is the hurricane risk?",
                "no_tools": True,
                "has": ["which hub"],
                "question": True,
            }
        ],
    },
    {
        "name": "follow up",
        "turns": [
            {
                "content": "What is the weather in Denver right now?",
                "tools": ["get_current_weather"],
                "forbid": ["get_active_alerts", "get_weather_history"],
                "has": ["Denver"],
            },
            {
                "content": "How many snow days did that hub have in 2025?",
                "tools": ["get_weather_history"],
                "args": {"get_weather_history": ["2025"]},
                "pattern": r"\d",
            },
        ],
    },
]
