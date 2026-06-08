from __future__ import annotations

import html
from typing import Callable

import streamlit as st

from bgt.config import MAX_STALKS, PRESETS
from bgt.core import normalize_rates


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
