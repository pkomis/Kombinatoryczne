import streamlit as st

from bgt.ui.compare import compare_mode, init_compare_state
from bgt.ui.game import game_mode, init_game_state
from bgt.ui.sandbox import init_sandbox_state, sandbox_mode
from bgt.ui.theme import apply_global_style


def init_state() -> None:
    init_sandbox_state()
    init_compare_state()
    init_game_state()


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
