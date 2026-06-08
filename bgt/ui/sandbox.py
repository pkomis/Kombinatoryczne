from __future__ import annotations

import time

import streamlit as st

from bgt.algorithms import MakespanTwoOracle, oracle_reduce_fastest, oracle_reduce_max
from bgt.config import ALGO_META
from bgt.core import Oracle, advance_day, create_bamboos, makespan
from bgt.ui.components import panel_title, preset_buttons, rate_editor, render_svg
from bgt.visuals import bamboo_garden_svg, sparkline_svg


def init_sandbox_state() -> None:
    if "sandbox_rates" not in st.session_state:
        reset_sandbox([0.5, 0.3, 0.2])
    if st.session_state.get("sandbox_algo") == "optimal":
        st.session_state.sandbox_algo = "makespan_two"
    st.session_state.setdefault("sandbox_algo", "reduce_max")
    st.session_state.setdefault("sandbox_speed", 700)
    if "sandbox_makespan_two_oracle" not in st.session_state:
        st.session_state.sandbox_makespan_two_oracle = MakespanTwoOracle(st.session_state.sandbox_rates)


def reset_sandbox(rates: list[float] | None = None) -> None:
    rates = list(rates if rates is not None else st.session_state.get("sandbox_rates", [0.5, 0.3, 0.2]))
    st.session_state.sandbox_rates = rates
    st.session_state.sandbox_bamboos = create_bamboos(rates)
    st.session_state.sandbox_day = 0
    st.session_state.sandbox_history = []
    st.session_state.sandbox_last_cut = None
    st.session_state.sandbox_panda_at = None
    st.session_state.sandbox_running = False
    st.session_state.sandbox_makespan_two_oracle = MakespanTwoOracle(rates)


def reset_sandbox_for_current_settings() -> None:
    reset_sandbox()


def sandbox_oracle() -> Oracle:
    algorithm = st.session_state.sandbox_algo
    if algorithm == "reduce_fastest":
        return oracle_reduce_fastest(float(st.session_state.get("sandbox_x", 1.618)))
    if algorithm == "makespan_two":
        return st.session_state.sandbox_makespan_two_oracle
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
            elif st.session_state.sandbox_algo == "makespan_two":
                st.caption(
                    "Dyadic schedule: round rates down to powers of 1/2, "
                    "then reserve periodic cuts. Guaranteed M <= 2."
                )

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
