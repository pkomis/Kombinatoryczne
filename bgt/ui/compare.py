from __future__ import annotations

import html
import math
import time

import streamlit as st

from bgt.algorithms import MakespanTwoOracle, oracle_reduce_fastest, oracle_reduce_max
from bgt.config import ALGO_META
from bgt.core import advance_day, create_bamboos, makespan
from bgt.ui.components import panel_title, preset_buttons, rate_editor, render_svg
from bgt.visuals import bamboo_garden_svg, sparkline_svg


def init_compare_state() -> None:
    if "compare_rates" not in st.session_state:
        reset_compare([0.5, 0.25, 0.15, 0.1])
    st.session_state.setdefault("compare_speed", 500)
    if "compare_makespan_two_oracle" not in st.session_state:
        st.session_state.compare_makespan_two_oracle = MakespanTwoOracle(st.session_state.compare_rates)


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
    st.session_state.compare_makespan_two_oracle = MakespanTwoOracle(rates)


def compare_tick() -> None:
    oracles = {
        "reduce_max": oracle_reduce_max,
        "reduce_fastest": oracle_reduce_fastest(1 + 1 / math.sqrt(5)),
        "makespan_two": st.session_state.compare_makespan_two_oracle,
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
