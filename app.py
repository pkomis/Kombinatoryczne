from __future__ import annotations

import html
import math
import time
from dataclasses import dataclass
from typing import Callable

import streamlit as st


@dataclass(frozen=True)
class Bamboo:
    id: int
    growth: float
    height: float = 0.0


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
    "optimal": {
        "label": "Makespan-2 oracle",
        "color": "#1d4ed8",
        "bound": "2",
    },
}

MAX_STALKS = 8


def create_bamboos(rates: list[float]) -> list[Bamboo]:
    return [Bamboo(id=i, growth=float(rate), height=0.0) for i, rate in enumerate(rates)]


def oracle_reduce_max(bamboos: list[Bamboo]) -> int:
    return max(range(len(bamboos)), key=lambda i: bamboos[i].height)


def oracle_reduce_fastest(threshold: float) -> Callable[[list[Bamboo]], int]:
    def pick(bamboos: list[Bamboo]) -> int:
        eligible = [i for i, bamboo in enumerate(bamboos) if bamboo.height >= threshold]
        if not eligible:
            return oracle_reduce_max(bamboos)
        return max(eligible, key=lambda i: bamboos[i].growth)

    return pick


def oracle_optimal(bamboos: list[Bamboo]) -> int:
    return max(range(len(bamboos)), key=lambda i: bamboos[i].height * bamboos[i].growth * 4)


def grow(bamboos: list[Bamboo]) -> list[Bamboo]:
    return [
        Bamboo(id=bamboo.id, growth=bamboo.growth, height=bamboo.height + bamboo.growth)
        for bamboo in bamboos
    ]


def cut(bamboos: list[Bamboo], index: int) -> list[Bamboo]:
    return [
        Bamboo(id=bamboo.id, growth=bamboo.growth, height=0.0 if i == index else bamboo.height)
        for i, bamboo in enumerate(bamboos)
    ]


def advance_day(
    bamboos: list[Bamboo],
    oracle: Callable[[list[Bamboo]], int],
) -> tuple[list[Bamboo], float, int]:
    grown = grow(bamboos)
    target = oracle(grown)
    return cut(grown, target), max_height(grown), target


def max_height(bamboos: list[Bamboo]) -> float:
    return max((bamboo.height for bamboo in bamboos), default=0.0)


def makespan(history: list[float]) -> float:
    return max(history) if history else 0.0


def normalize_rates(rates: list[float]) -> list[float]:
    positive = [max(0.0, float(rate)) for rate in rates]
    total = sum(positive)
    if total <= 0:
        return [1 / len(positive)] * len(positive)
    return [rate / total for rate in positive]


def panel_title(title: str, color: str | None = None) -> None:
    dot = ""
    if color:
        dot = f'<span class="panel-dot" style="background:{html.escape(color)}"></span>'
    st.markdown(
        f'<div class="panel-title">{dot}<span>{html.escape(title)}</span></div>',
        unsafe_allow_html=True,
    )


def render_svg(svg: str) -> None:
    st.image(svg, width="stretch")


def panda_svg(flipped: bool, cutting: bool) -> str:
    flip = ' transform="translate(48 0) scale(-1 1)"' if flipped else ""
    scissors = ""
    if cutting:
        scissors = """
        <g transform="translate(32,28) rotate(-30)">
          <line x1="0" y1="0" x2="10" y2="0" stroke="#888" stroke-width="1.5" stroke-linecap="round"/>
          <line x1="0" y1="3" x2="10" y2="3" stroke="#888" stroke-width="1.5" stroke-linecap="round"/>
          <circle cx="0" cy="1.5" r="2.5" fill="none" stroke="#888" stroke-width="1"/>
        </g>
        """
    return f"""
    <g{flip}>
      <ellipse cx="24" cy="38" rx="13" ry="12" fill="#f0f0f0" stroke="#222" stroke-width="1.2"/>
      <circle cx="24" cy="20" r="11" fill="#f0f0f0" stroke="#222" stroke-width="1.2"/>
      <circle cx="14" cy="11" r="5" fill="#222"/>
      <circle cx="34" cy="11" r="5" fill="#222"/>
      <ellipse cx="19" cy="19" rx="4" ry="3.5" fill="#222" transform="rotate(-10,19,19)"/>
      <ellipse cx="29" cy="19" rx="4" ry="3.5" fill="#222" transform="rotate(10,29,19)"/>
      <circle cx="19" cy="19" r="1.5" fill="#fff"/>
      <circle cx="29" cy="19" r="1.5" fill="#fff"/>
      <ellipse cx="24" cy="23.5" rx="2.5" ry="1.5" fill="#444"/>
      <path d="M21 25.5 Q24 27.5 27 25.5" fill="none" stroke="#444" stroke-width="0.8" stroke-linecap="round"/>
      <ellipse cx="11" cy="38" rx="5" ry="8" fill="#222" stroke="#222" stroke-width="0.8" transform="rotate(-15,11,38)"/>
      <ellipse cx="37" cy="38" rx="5" ry="8" fill="#222" stroke="#222" stroke-width="0.8" transform="rotate(15,37,38)"/>
      <ellipse cx="18" cy="49" rx="5" ry="4" fill="#222"/>
      <ellipse cx="30" cy="49" rx="5" ry="4" fill="#222"/>
      {scissors}
    </g>
    """


def bamboo_garden_svg(
    bamboos: list[Bamboo],
    max_display_height: float,
    last_cut: int | None = None,
    panda_at: int | None = None,
    hint: str | None = None,
) -> str:
    width = 540
    height = 280
    ground_y = 220
    left_pad = 56
    right_pad = 70
    usable_width = width - left_pad - right_pad
    count = len(bamboos)
    slot_width = usable_width / max(count, 1)
    stalk_width = max(14, min(28, slot_width * 0.38))
    scale_height = max(max_display_height, 1.5, max_height(bamboos))
    scale = (ground_y - 30) / scale_height

    def stalk_x(index: int) -> float:
        return left_pad + slot_width * index + slot_width / 2

    parts: list[str] = [
        f'<svg viewBox="0 0 {width} {height + 30}" xmlns="http://www.w3.org/2000/svg">',
        f'<rect width="{width}" height="{height + 30}" fill="#fafaf7" rx="6"/>',
    ]

    if bamboos:
        tallest = max(bamboos, key=lambda bamboo: bamboo.height)
        bracket_height = tallest.height * scale
        if bracket_height > 10:
            y_mid = ground_y - bracket_height / 2
            parts.extend(
                [
                    f'<line x1="18" y1="{ground_y - bracket_height:.2f}" x2="18" y2="{ground_y}" stroke="#555" stroke-width="0.8"/>',
                    f'<line x1="14" y1="{ground_y - bracket_height:.2f}" x2="22" y2="{ground_y - bracket_height:.2f}" stroke="#555" stroke-width="0.8"/>',
                    f'<line x1="14" y1="{ground_y}" x2="22" y2="{ground_y}" stroke="#555" stroke-width="0.8"/>',
                    f'<text x="10" y="{y_mid + 4:.2f}" text-anchor="middle" font-size="11" font-family="Georgia,serif" font-style="italic" fill="#333">h</text>',
                    f'<text x="13" y="{y_mid + 10:.2f}" font-size="7" font-family="Georgia,serif" fill="#333">max</text>',
                ]
            )

    for value in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]:
        y = ground_y - value * scale
        if 10 <= y <= ground_y:
            parts.extend(
                [
                    f'<line x1="{left_pad - 4}" y1="{y:.2f}" x2="{width - right_pad + 4}" y2="{y:.2f}" stroke="#ccc" stroke-width="0.5" stroke-dasharray="3 4"/>',
                    f'<text x="{left_pad - 6}" y="{y + 3.5:.2f}" text-anchor="end" font-size="8.5" font-family="Georgia,serif" fill="#999">{value:.1f}</text>',
                ]
            )

    for index, bamboo in enumerate(bamboos):
        center_x = stalk_x(index)
        display_height = max(0.0, bamboo.height)
        pixel_height = display_height * scale
        top = ground_y - pixel_height
        was_cut = last_cut == index
        is_target = panda_at == index
        green_1 = "#22c55e" if was_cut else "#2d8a3e"
        green_2 = "#16a34a" if was_cut else "#1f6b2e"
        green_3 = "#bbf7d0" if was_cut else "#a7d9a0"

        if is_target:
            parts.append(
                f'<rect x="{center_x - stalk_width / 2 - 3:.2f}" y="{top - 3:.2f}" width="{stalk_width + 6:.2f}" height="{pixel_height + 6:.2f}" rx="8" fill="none" stroke="#f59e0b" stroke-width="1.5" stroke-dasharray="3 2" opacity="0.75"/>'
            )

        if pixel_height > 0:
            parts.extend(
                [
                    f'<rect x="{center_x - stalk_width / 2:.2f}" y="{top:.2f}" width="{stalk_width:.2f}" height="{pixel_height:.2f}" rx="{stalk_width / 2:.2f}" fill="{green_1}" stroke="{green_2}" stroke-width="0.8"/>',
                    f'<circle cx="{center_x:.2f}" cy="{top:.2f}" r="{stalk_width / 2 + 1:.2f}" fill="{green_1}" stroke="{green_2}" stroke-width="0.8"/>',
                ]
            )
            if pixel_height > 4:
                parts.append(
                    f'<rect x="{center_x - stalk_width / 2 + 3:.2f}" y="{top + 2:.2f}" width="{stalk_width * 0.25:.2f}" height="{max(0.0, pixel_height - 4):.2f}" rx="2" fill="{green_3}" opacity="0.5"/>'
                )
            joint_count = max(1, math.floor(display_height * 3))
            for joint in range(joint_count):
                y = ground_y - ((joint + 1) / (joint_count + 1)) * pixel_height
                parts.append(
                    f'<line x1="{center_x - stalk_width / 2:.2f}" y1="{y:.2f}" x2="{center_x + stalk_width / 2:.2f}" y2="{y:.2f}" stroke="{green_2}" stroke-width="1.2" opacity="0.6"/>'
                )
            parts.append(
                f'<circle cx="{center_x - stalk_width * 0.15:.2f}" cy="{top - stalk_width * 0.1:.2f}" r="{stalk_width * 0.12:.2f}" fill="{green_3}" opacity="0.6"/>'
            )

        label_y = min(top - stalk_width / 2 - 4, ground_y - 4)
        label_color = "#16a34a" if was_cut else "#444"
        label_weight = "700" if was_cut else "400"
        parts.extend(
            [
                f'<text x="{center_x:.2f}" y="{label_y:.2f}" text-anchor="middle" font-size="9" font-family="Georgia,serif" fill="{label_color}" font-weight="{label_weight}">{display_height:.2f}</text>',
                f'<text x="{center_x:.2f}" y="{ground_y + 18}" text-anchor="middle" font-size="11" font-family="Georgia,serif" font-style="italic" fill="#333">b<tspan font-size="8" baseline-shift="-4">{index + 1}</tspan></text>',
            ]
        )

    ground_width = width - left_pad - right_pad + 16
    parts.extend(
        [
            f'<rect x="{left_pad - 8}" y="{ground_y}" width="{ground_width}" height="3" rx="1" fill="#8B6914"/>',
            f'<rect x="{left_pad - 8}" y="{ground_y + 3}" width="{ground_width}" height="8" rx="1" fill="#a07830" opacity="0.4"/>',
        ]
    )

    if last_cut is not None and 0 <= last_cut < count:
        center_x = stalk_x(last_cut)
        cut_y = ground_y - max(0.2, bamboos[last_cut].height) * scale - stalk_width / 2
        for ray in range(6):
            angle = (ray / 6) * math.tau
            radius = stalk_width + 6
            parts.append(
                f'<line x1="{center_x:.2f}" y1="{cut_y:.2f}" x2="{center_x + math.cos(angle) * radius:.2f}" y2="{cut_y + math.sin(angle) * radius:.2f}" stroke="#fbbf24" stroke-width="1" opacity="0.6"/>'
            )

    panda_x = stalk_x(panda_at) if panda_at is not None and 0 <= panda_at < count else width - right_pad + 10
    flipped = panda_at is not None and panda_at < count / 2
    parts.append(
        f'<g transform="translate({panda_x - 24:.2f}, {ground_y - 50})">{panda_svg(flipped=flipped, cutting=panda_at is not None)}</g>'
    )

    if hint:
        parts.append(
            f'<text x="{width / 2}" y="{height + 22}" text-anchor="middle" font-size="9.5" font-family="Georgia,serif" fill="#777" font-style="italic">{html.escape(hint)}</text>'
        )

    parts.append("</svg>")
    return "\n".join(parts)


def sparkline_svg(
    data: list[float],
    color: str,
    height: int = 52,
    max_value: float = 3.0,
) -> str:
    width = 400
    if len(data) < 2:
        return f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg"></svg>'

    upper = max(max_value, max(data))
    points = []
    for index, value in enumerate(data):
        x = (index / (len(data) - 1)) * width
        y = height - (value / upper) * (height - 2) - 1
        points.append(f"{x:.2f},{y:.2f}")
    point_string = " ".join(points)

    parts = [f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">']
    for bound, bound_color in {"9": "#dc2626", "2.62": "#b45309", "2": "#1d4ed8"}.items():
        y = height - (float(bound) / upper) * (height - 2) - 1
        if 0 <= y <= height:
            parts.append(
                f'<line x1="0" y1="{y:.2f}" x2="{width}" y2="{y:.2f}" stroke="{bound_color}" stroke-width="0.6" stroke-dasharray="3 3" opacity="0.5"/>'
            )
    parts.extend(
        [
            f'<polyline points="{point_string}" fill="none" stroke="{html.escape(color)}" stroke-width="1.8" stroke-linejoin="round"/>',
            f'<polyline points="0,{height} {point_string} {width},{height}" fill="{html.escape(color)}" opacity="0.08" stroke="none"/>',
            "</svg>",
        ]
    )
    return "\n".join(parts)


def apply_global_style() -> None:
    st.set_page_config(
        page_title="Bamboo Garden Trimming",
        layout="wide",
    )
    st.markdown(
        """
        <style>
        :root {
            --paper: #f4f0e8;
            --ink: #222;
            --muted: #6b7280;
            --rule: #d1c9b8;
        }
        .stApp {
            background: var(--paper);
            color: var(--ink);
        }
        .block-container {
            max-width: 1220px;
            padding-top: 1.25rem;
            padding-bottom: 2rem;
        }
        h1, h2, h3, label, p, span, div {
            font-family: Georgia, "Times New Roman", serif;
        }
        h1 {
            font-size: 1.9rem;
            line-height: 1.15;
            margin-bottom: 0.15rem;
        }
        .app-caption {
            color: #69707a;
            font-size: 0.82rem;
            margin-bottom: 0.7rem;
        }
        .panel-title {
            align-items: center;
            border-bottom: 1px solid var(--rule);
            color: #4b5563;
            display: flex;
            font-size: 0.72rem;
            font-weight: 700;
            gap: 0.45rem;
            letter-spacing: 0.06em;
            margin: -0.45rem -0.45rem 0.65rem;
            padding: 0.45rem 0.7rem;
            text-transform: uppercase;
        }
        .panel-dot {
            border-radius: 999px;
            display: inline-flex;
            height: 0.55rem;
            width: 0.55rem;
        }
        [data-testid="stMetric"] {
            background: #fffdf8;
            border: 1px solid var(--rule);
            border-radius: 4px;
            padding: 0.55rem 0.7rem;
        }
        [data-testid="stMetricLabel"] {
            color: #777;
            font-size: 0.7rem;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }
        [data-testid="stMetricValue"] {
            color: #1f2937;
            font-family: Georgia, "Times New Roman", serif;
            font-size: 1.45rem;
        }
        div[data-testid="stButton"] > button {
            border-radius: 4px;
            min-height: 2.1rem;
        }
        div[data-testid="stRadio"] label {
            font-size: 0.88rem;
        }
        .leader-row {
            align-items: center;
            background: #fffdf8;
            border: 1px solid var(--rule);
            border-radius: 4px;
            display: flex;
            font-size: 0.86rem;
            justify-content: space-between;
            margin-bottom: 0.25rem;
            padding: 0.38rem 0.5rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def init_state() -> None:
    if "sandbox_rates" not in st.session_state:
        reset_sandbox([0.5, 0.3, 0.2])
    st.session_state.setdefault("sandbox_algo", "reduce_max")
    st.session_state.setdefault("sandbox_speed", 700)

    if "compare_rates" not in st.session_state:
        reset_compare([0.5, 0.25, 0.15, 0.1])
    st.session_state.setdefault("compare_speed", 500)

    if "game_phase" not in st.session_state:
        reset_game(idle=True)


def reset_sandbox(rates: list[float] | None = None) -> None:
    rates = list(rates if rates is not None else st.session_state.get("sandbox_rates", [0.5, 0.3, 0.2]))
    st.session_state.sandbox_rates = rates
    st.session_state.sandbox_bamboos = create_bamboos(rates)
    st.session_state.sandbox_day = 0
    st.session_state.sandbox_history = []
    st.session_state.sandbox_last_cut = None
    st.session_state.sandbox_panda_at = None
    st.session_state.sandbox_running = False


def reset_sandbox_for_current_settings() -> None:
    reset_sandbox()


def sandbox_oracle() -> Callable[[list[Bamboo]], int]:
    algorithm = st.session_state.sandbox_algo
    if algorithm == "reduce_fastest":
        return oracle_reduce_fastest(float(st.session_state.get("sandbox_x", 1.618)))
    if algorithm == "optimal":
        return oracle_optimal
    return oracle_reduce_max


def sandbox_tick() -> None:
    next_bamboos, day_makespan, target = advance_day(
        st.session_state.sandbox_bamboos,
        sandbox_oracle(),
    )
    st.session_state.sandbox_history = [*st.session_state.sandbox_history[-150:], day_makespan]
    st.session_state.sandbox_bamboos = next_bamboos
    st.session_state.sandbox_last_cut = target
    st.session_state.sandbox_panda_at = target
    st.session_state.sandbox_day += 1


def reset_compare(rates: list[float] | None = None) -> None:
    rates = list(rates if rates is not None else st.session_state.get("compare_rates", [0.5, 0.25, 0.15, 0.1]))
    st.session_state.compare_rates = rates
    st.session_state.compare_states = {
        key: {
            "bamboos": create_bamboos(rates),
            "history": [],
            "last_cut": None,
            "panda_at": None,
        }
        for key in ALGO_META
    }
    st.session_state.compare_day = 0
    st.session_state.compare_running = False


def compare_tick() -> None:
    oracles = {
        "reduce_max": oracle_reduce_max,
        "reduce_fastest": oracle_reduce_fastest(1 + 1 / math.sqrt(5)),
        "optimal": oracle_optimal,
    }
    next_states = {}
    for key, state in st.session_state.compare_states.items():
        next_bamboos, day_makespan, target = advance_day(state["bamboos"], oracles[key])
        next_states[key] = {
            "bamboos": next_bamboos,
            "history": [*state["history"][-150:], day_makespan],
            "last_cut": target,
            "panda_at": target,
        }
    st.session_state.compare_states = next_states
    st.session_state.compare_day += 1


GAME_RATES = [0.45, 0.25, 0.2, 0.1]
GAME_LIMIT = 3.2


def reset_game(idle: bool = False) -> None:
    st.session_state.game_player = create_bamboos(GAME_RATES)
    st.session_state.game_bot = create_bamboos(GAME_RATES)
    st.session_state.game_day = 0
    st.session_state.game_player_makespan = 0.0
    st.session_state.game_bot_makespan = 0.0
    st.session_state.game_player_history = []
    st.session_state.game_bot_history = []
    st.session_state.game_last_cut = None
    st.session_state.game_bot_last_cut = None
    st.session_state.game_panda_at = None
    st.session_state.game_cut_done = False
    st.session_state.game_end_reason = ""
    if idle:
        st.session_state.game_phase = "idle"
        st.session_state.game_message = ""
    else:
        st.session_state.game_phase = "playing"
        st.session_state.game_message = "Your turn: choose one bamboo stalk to trim."


def game_player_cut(index: int) -> None:
    if st.session_state.game_phase != "playing" or st.session_state.game_cut_done:
        return
    st.session_state.game_player = cut(st.session_state.game_player, index)
    st.session_state.game_last_cut = index
    st.session_state.game_panda_at = index
    st.session_state.game_cut_done = True
    st.session_state.game_message = "Good cut. End the day to advance."


def game_end_day() -> None:
    if st.session_state.game_phase != "playing":
        return

    made_cut = st.session_state.game_cut_done
    player_grown = grow(st.session_state.game_player)
    player_height = max_height(player_grown)
    st.session_state.game_player_history = [*st.session_state.game_player_history, player_height]
    st.session_state.game_player_makespan = max(
        st.session_state.game_player_makespan,
        player_height,
    )
    st.session_state.game_player = player_grown

    bot_grown = grow(st.session_state.game_bot)
    bot_target = oracle_reduce_max(bot_grown)
    bot_height = max_height(bot_grown)
    st.session_state.game_bot_history = [*st.session_state.game_bot_history, bot_height]
    st.session_state.game_bot_makespan = max(st.session_state.game_bot_makespan, bot_height)
    st.session_state.game_bot = cut(bot_grown, bot_target)
    st.session_state.game_bot_last_cut = bot_target

    st.session_state.game_day += 1
    st.session_state.game_cut_done = False
    st.session_state.game_panda_at = None
    st.session_state.game_last_cut = None

    if player_height >= GAME_LIMIT:
        reason = f"Your tallest bamboo reached {player_height:.2f}, above the {GAME_LIMIT:.1f} limit."
        st.session_state.game_phase = "over"
        st.session_state.game_end_reason = reason
        st.session_state.game_message = reason
    elif made_cut:
        st.session_state.game_message = "End of day. Your turn next."
    else:
        st.session_state.game_message = "You skipped a cut. Choose the next one carefully."


def prepare_rate_widgets(prefix: str, rates: list[float]) -> None:
    pending_key = f"{prefix}_pending_rates"
    if pending_key in st.session_state:
        pending_rates = list(st.session_state.pop(pending_key))
        for index in range(MAX_STALKS + 2):
            st.session_state.pop(f"{prefix}_rate_{index}", None)
        for index, rate in enumerate(pending_rates):
            st.session_state[f"{prefix}_rate_{index}"] = float(rate)
        return

    for index, rate in enumerate(rates):
        st.session_state.setdefault(f"{prefix}_rate_{index}", float(rate))


def queue_rate_sync(prefix: str, rates: list[float]) -> None:
    st.session_state[f"{prefix}_pending_rates"] = list(rates)


def rate_editor(prefix: str, rates: list[float], on_apply: Callable[[list[float]], None]) -> None:
    prepare_rate_widgets(prefix, rates)

    control_cols = st.columns(2)
    with control_cols[0]:
        if st.button("Add stalk", key=f"{prefix}_add", disabled=len(rates) >= MAX_STALKS, width="stretch"):
            next_rates = [1 / (len(rates) + 1)] * (len(rates) + 1)
            on_apply(next_rates)
            queue_rate_sync(prefix, next_rates)
            st.rerun()
    with control_cols[1]:
        if st.button("Remove last", key=f"{prefix}_remove", disabled=len(rates) <= 2, width="stretch"):
            next_rates = normalize_rates(rates[:-1])
            on_apply(next_rates)
            queue_rate_sync(prefix, next_rates)
            st.rerun()

    with st.form(f"{prefix}_rates_form", border=False):
        values = []
        for index in range(len(rates)):
            values.append(
                st.number_input(
                    f"b{index + 1}",
                    min_value=0.001,
                    max_value=0.999,
                    step=0.01,
                    format="%.3f",
                    key=f"{prefix}_rate_{index}",
                )
            )

        total = sum(values)
        valid = abs(total - 1.0) < 0.002 and all(value > 0 for value in values)
        st.caption(f"sum = {total:.3f} {'OK' if valid else 'must equal 1.000'}")
        submit_cols = st.columns(2)
        with submit_cols[0]:
            applied = st.form_submit_button("Apply", disabled=not valid, width="stretch")
        with submit_cols[1]:
            normalized = st.form_submit_button("Normalize", width="stretch")

    if normalized:
        next_rates = normalize_rates(values)
        on_apply(next_rates)
        queue_rate_sync(prefix, next_rates)
        st.rerun()
    if applied:
        next_rates = [float(value) for value in values]
        on_apply(next_rates)
        st.rerun()


def preset_buttons(prefix: str, on_select: Callable[[list[float]], None]) -> None:
    for preset in PRESETS:
        if st.button(preset["name"], key=f"{prefix}_preset_{preset['name']}", width="stretch"):
            rates = list(preset["rates"])
            on_select(rates)
            queue_rate_sync(prefix, rates)
            st.rerun()


def sandbox_mode() -> None:
    left, main = st.columns([0.28, 0.72], gap="large")
    with left:
        with st.container(border=True):
            panel_title("Presets")
            preset_buttons("sandbox", reset_sandbox)

        with st.container(border=True):
            panel_title("Growth rates h_i")
            rate_editor("sandbox", st.session_state.sandbox_rates, reset_sandbox)

        with st.container(border=True):
            panel_title("Algorithm")
            options = list(ALGO_META)
            st.radio(
                "Algorithm",
                options,
                format_func=lambda option: ALGO_META[option]["label"],
                key="sandbox_algo",
                label_visibility="collapsed",
                on_change=reset_sandbox_for_current_settings,
            )
            if st.session_state.sandbox_algo == "reduce_fastest":
                st.slider(
                    "Threshold x",
                    min_value=0.5,
                    max_value=3.0,
                    value=1.618,
                    step=0.001,
                    key="sandbox_x",
                )
                st.caption("Suggested reference: 1 + 1/sqrt(5) is about 1.447.")

    meta = ALGO_META[st.session_state.sandbox_algo]
    history = st.session_state.sandbox_history
    current_makespan = makespan(history)

    with main:
        with st.container(border=True):
            panel_title(f"Day {st.session_state.sandbox_day} - {meta['label']}", meta["color"])
            render_svg(
                bamboo_garden_svg(
                    st.session_state.sandbox_bamboos,
                    max(current_makespan, 2.0),
                    st.session_state.sandbox_last_cut,
                    st.session_state.sandbox_panda_at,
                )
            )
            run_cols = st.columns([1, 1, 1, 2])
            with run_cols[0]:
                if st.button(
                    "Pause" if st.session_state.sandbox_running else "Run",
                    key="sandbox_run",
                    width="stretch",
                ):
                    st.session_state.sandbox_running = not st.session_state.sandbox_running
                    st.rerun()
            with run_cols[1]:
                if st.button("+1 day", disabled=st.session_state.sandbox_running, key="sandbox_step", width="stretch"):
                    sandbox_tick()
                    st.rerun()
            with run_cols[2]:
                if st.button("Reset", key="sandbox_reset", width="stretch"):
                    reset_sandbox()
                    st.rerun()
            with run_cols[3]:
                st.slider(
                    "Speed (ms)",
                    min_value=80,
                    max_value=1200,
                    step=20,
                    key="sandbox_speed",
                )

        metric_cols = st.columns(4)
        metric_cols[0].metric("Makespan M", f"{current_makespan:.3f}")
        metric_cols[1].metric("Day d", st.session_state.sandbox_day)
        metric_cols[2].metric("Stalks n", len(st.session_state.sandbox_bamboos))
        metric_cols[3].metric("Max h_i", f"{max(st.session_state.sandbox_rates):.3f}")

        with st.container(border=True):
            panel_title("Makespan M over time", meta["color"])
            render_svg(sparkline_svg(history, meta["color"], height=64))
            st.caption("Dashed guide lines mark bounds 9, 2.62, and 2 where visible.")

    if st.session_state.sandbox_running:
        time.sleep(st.session_state.sandbox_speed / 1000)
        sandbox_tick()
        st.rerun()


def compare_mode() -> None:
    left, main = st.columns([0.28, 0.72], gap="large")
    keys = list(ALGO_META)
    leaderboard = sorted(
        (
            {
                "key": key,
                "makespan": makespan(st.session_state.compare_states[key]["history"]),
            }
            for key in keys
        ),
        key=lambda item: item["makespan"],
    )

    with left:
        with st.container(border=True):
            panel_title("Shared garden")
            rate_editor("compare", st.session_state.compare_rates, reset_compare)

        with st.container(border=True):
            panel_title("Presets")
            preset_buttons("compare", reset_compare)

        with st.container(border=True):
            leader_color = ALGO_META[leaderboard[0]["key"]]["color"] if st.session_state.compare_day > 0 else None
            panel_title("Leaderboard", leader_color)
            for rank, item in enumerate(leaderboard, start=1):
                meta = ALGO_META[item["key"]]
                st.markdown(
                    f"""
                    <div class="leader-row">
                      <span style="color:{meta['color']};font-weight:700;">{rank}. {html.escape(meta['label'])}</span>
                      <span>{item['makespan']:.2f}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.caption(f"bound <= {meta['bound']}")

    with main:
        control_cols = st.columns([1, 1, 1, 2])
        with control_cols[0]:
            if st.button(
                "Pause" if st.session_state.compare_running else "Run all",
                key="compare_run",
                width="stretch",
            ):
                st.session_state.compare_running = not st.session_state.compare_running
                st.rerun()
        with control_cols[1]:
            if st.button("+1 day", disabled=st.session_state.compare_running, key="compare_step", width="stretch"):
                compare_tick()
                st.rerun()
        with control_cols[2]:
            if st.button("Reset", key="compare_reset", width="stretch"):
                reset_compare()
                st.rerun()
        with control_cols[3]:
            st.slider(
                "Speed (ms)",
                min_value=80,
                max_value=1000,
                step=20,
                key="compare_speed",
            )

        st.caption(f"Day {st.session_state.compare_day}")
        for key in keys:
            meta = ALGO_META[key]
            state = st.session_state.compare_states[key]
            current_makespan = makespan(state["history"])
            rank = next(index for index, item in enumerate(leaderboard) if item["key"] == key)
            accent = meta["color"] if rank == 0 and st.session_state.compare_day > 0 else None

            with st.container(border=True):
                label = f"{meta['label']} - M = {current_makespan:.3f}"
                panel_title(label, accent or meta["color"])
                garden_col, spark_col = st.columns([0.72, 0.28])
                with garden_col:
                    render_svg(
                        bamboo_garden_svg(
                            state["bamboos"],
                            max(current_makespan, 2.0),
                            state["last_cut"],
                            state["panda_at"],
                        )
                    )
                with spark_col:
                    st.caption(f"bound <= {meta['bound']}")
                    render_svg(sparkline_svg(state["history"], meta["color"], height=110))

    if st.session_state.compare_running:
        time.sleep(st.session_state.compare_speed / 1000)
        compare_tick()
        st.rerun()


def game_mode() -> None:
    if st.session_state.game_phase == "idle":
        with st.container(border=True):
            panel_title("Bamboo Gardener Challenge", "#db2777")
            st.write(
                "You control the left garden. The Reduce-Max bot controls the right garden. "
                f"Any player bamboo reaching {GAME_LIMIT:.1f} ends the game."
            )
            if st.button("Start game", key="game_start", type="primary"):
                reset_game(idle=False)
                st.rerun()
        return

    score_cols = st.columns([1, 0.5, 1])
    score_cols[0].metric("You", f"{st.session_state.game_player_makespan:.3f}")
    score_cols[1].metric("Day", st.session_state.game_day)
    score_cols[2].metric("Reduce-Max bot", f"{st.session_state.game_bot_makespan:.3f}")

    message_type = "error" if st.session_state.game_phase == "over" else "success"
    getattr(st, message_type)(st.session_state.game_message)

    left, right = st.columns(2, gap="large")
    with left:
        with st.container(border=True):
            panel_title("Your garden", "#db2777")
            render_svg(
                bamboo_garden_svg(
                    st.session_state.game_player,
                    GAME_LIMIT,
                    st.session_state.game_last_cut,
                    st.session_state.game_panda_at,
                    "Choose one button below to trim a stalk.",
                )
            )
            cut_cols = st.columns(len(st.session_state.game_player))
            for index, column in enumerate(cut_cols):
                disabled = st.session_state.game_phase != "playing" or st.session_state.game_cut_done
                if column.button(f"Cut b{index + 1}", key=f"game_cut_{index}", disabled=disabled, width="stretch"):
                    game_player_cut(index)
                    st.rerun()
            if st.session_state.game_phase == "playing":
                st.caption("Cut made." if st.session_state.game_cut_done else "Waiting for your cut.")

    with right:
        with st.container(border=True):
            panel_title("Reduce-Max bot", "#1d4ed8")
            render_svg(
                bamboo_garden_svg(
                    st.session_state.game_bot,
                    GAME_LIMIT,
                    st.session_state.game_bot_last_cut,
                    st.session_state.game_bot_last_cut,
                )
            )

    history_cols = st.columns(2, gap="large")
    with history_cols[0]:
        with st.container(border=True):
            panel_title("Your makespan", "#db2777")
            render_svg(
                sparkline_svg(st.session_state.game_player_history, "#db2777", height=54, max_value=GAME_LIMIT)
            )
    with history_cols[1]:
        with st.container(border=True):
            panel_title("Bot makespan", "#1d4ed8")
            render_svg(
                sparkline_svg(st.session_state.game_bot_history, "#1d4ed8", height=54, max_value=GAME_LIMIT)
            )

    action_cols = st.columns([1, 1, 4])
    with action_cols[0]:
        if st.session_state.game_phase == "playing":
            label = "End day" if st.session_state.game_cut_done else "Skip day"
            if st.button(label, key="game_end_day", type="primary", width="stretch"):
                game_end_day()
                st.rerun()
    with action_cols[1]:
        if st.button("Play again", key="game_restart", width="stretch"):
            reset_game(idle=False)
            st.rerun()

    if st.session_state.game_phase == "over":
        winner = "You win!" if st.session_state.game_player_makespan <= st.session_state.game_bot_makespan else "Bot wins."
        st.info(winner)


def main() -> None:
    apply_global_style()
    init_state()

    st.title("Bamboo Garden Trimming")
    st.markdown(
        '<div class="app-caption">Python/Streamlit simulator for the Bamboo Garden Trimming problem.</div>',
        unsafe_allow_html=True,
    )

    mode = st.radio(
        "Mode",
        ["Sandbox", "Compare", "Game"],
        horizontal=True,
        label_visibility="collapsed",
    )

    if mode == "Sandbox":
        sandbox_mode()
    elif mode == "Compare":
        compare_mode()
    else:
        game_mode()


if __name__ == "__main__":
    main()
