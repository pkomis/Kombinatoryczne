import streamlit as st


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

