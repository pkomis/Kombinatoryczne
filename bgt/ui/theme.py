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
            --surface: #fffdf8;
            --surface-hover: #f8efe0;
            --surface-muted: #ede6d8;
            --focus: #d8841c;
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
        .stApp,
        .stApp label,
        .stApp p,
        .stApp span,
        .stApp div {
            color: var(--ink);
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
            background: var(--surface);
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
        [data-testid="stVerticalBlockBorderWrapper"],
        [data-testid="stExpander"],
        form {
            background: rgba(255, 253, 248, 0.45) !important;
            border-color: var(--rule) !important;
        }
        [data-testid="stVerticalBlockBorderWrapper"] > div,
        [data-testid="stExpander"] > div,
        form > div {
            background: transparent !important;
        }
        div[data-testid="stButton"] > button,
        div[data-testid="stFormSubmitButton"] > button,
        button[data-testid^="baseButton"] {
            background: var(--surface) !important;
            background-color: var(--surface) !important;
            border: 1px solid var(--rule) !important;
            border-radius: 4px;
            color: var(--ink) !important;
            min-height: 2.1rem;
            transition: background 120ms ease, border-color 120ms ease, color 120ms ease;
        }
        div[data-testid="stButton"] > button *,
        div[data-testid="stFormSubmitButton"] > button *,
        button[data-testid^="baseButton"] * {
            color: inherit !important;
        }
        div[data-testid="stButton"] > button:hover:not(:disabled),
        div[data-testid="stFormSubmitButton"] > button:hover:not(:disabled),
        button[data-testid^="baseButton"]:hover:not(:disabled) {
            background: var(--surface-hover) !important;
            background-color: var(--surface-hover) !important;
            border-color: var(--focus) !important;
            color: var(--ink) !important;
        }
        div[data-testid="stButton"] > button:focus:not(:disabled),
        div[data-testid="stFormSubmitButton"] > button:focus:not(:disabled),
        button[data-testid^="baseButton"]:focus:not(:disabled) {
            border-color: var(--focus) !important;
            box-shadow: 0 0 0 2px rgba(216, 132, 28, 0.18) !important;
            color: var(--ink) !important;
        }
        div[data-testid="stButton"] > button:disabled,
        div[data-testid="stFormSubmitButton"] > button:disabled,
        button[data-testid^="baseButton"]:disabled {
            background: var(--surface-muted) !important;
            border-color: #ded7ca !important;
            color: #8b8f96 !important;
            opacity: 1 !important;
        }
        button[kind="primary"],
        button[data-testid="baseButton-primary"] {
            background: #1a7a3a !important;
            background-color: #1a7a3a !important;
            border-color: #1a7a3a !important;
            color: #fffdf8 !important;
        }
        button[kind="primary"]:hover:not(:disabled),
        button[data-testid="baseButton-primary"]:hover:not(:disabled) {
            background: #12622d !important;
            background-color: #12622d !important;
            border-color: #12622d !important;
            color: #fffdf8 !important;
        }
        [data-baseweb="input"],
        [data-baseweb="select"],
        [data-testid="stNumberInput"] input {
            background: var(--surface) !important;
            background-color: var(--surface) !important;
            border-color: var(--rule) !important;
            color: var(--ink) !important;
        }
        [data-baseweb="input"] > div,
        [data-baseweb="select"] > div {
            background: var(--surface) !important;
            background-color: var(--surface) !important;
            border-color: var(--rule) !important;
        }
        [data-baseweb="input"] input,
        [data-baseweb="select"] input,
        [data-baseweb="select"] span {
            background: transparent !important;
            background-color: transparent !important;
            color: var(--ink) !important;
        }
        [data-baseweb="input"]:focus-within,
        [data-baseweb="select"]:focus-within {
            border-color: var(--focus) !important;
            box-shadow: 0 0 0 2px rgba(216, 132, 28, 0.18) !important;
        }
        div[data-testid="stRadio"] label {
            color: var(--ink) !important;
            font-size: 0.88rem;
        }
        .leader-row {
            align-items: center;
            background: var(--surface);
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
