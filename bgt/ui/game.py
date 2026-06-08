from __future__ import annotations

import streamlit as st

from bgt.algorithms import oracle_reduce_max
from bgt.config import GAME_LIMIT, GAME_RATES
from bgt.core import create_bamboos, cut, grow, max_height
from bgt.ui.components import panel_title, render_svg
from bgt.visuals import bamboo_garden_svg, sparkline_svg


def init_game_state() -> None:
    if "game_phase" not in st.session_state:
        reset_game(idle=True)


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

