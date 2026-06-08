PRESETS = [
    {"name": "Near-worst case", "rates": [0.95, 0.05]},
    {"name": "Uniform (4)", "rates": [0.25, 0.25, 0.25, 0.25]},
    {"name": "Geometric", "rates": [0.5, 0.25, 0.125, 0.125]},
    {"name": "One dominant", "rates": [0.7, 0.1, 0.1, 0.1]},
    {"name": "Five stalks", "rates": [0.4, 0.2, 0.15, 0.15, 0.1]},
]

ALGO_META = {
    "reduce_max": {
        "label": "Reduce-Max",
        "color": "#1a7a3a",
        "bound": "9",
    },
    "reduce_fastest": {
        "label": "Reduce-Fastest(x)",
        "color": "#b45309",
        "bound": "2.62",
    },
    "makespan_two": {
        "label": "Makespan-2 schedule",
        "color": "#1d4ed8",
        "bound": "2",
    },
}

MAX_STALKS = 8
GAME_RATES = [0.45, 0.25, 0.2, 0.1]
GAME_LIMIT = 3.2
