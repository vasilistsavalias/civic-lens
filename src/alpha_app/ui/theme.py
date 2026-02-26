from __future__ import annotations

import streamlit as st


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background: radial-gradient(1200px 500px at 20% -10%, #eef6ff 0%, #f7fbff 45%, #ffffff 100%);
        }
        .block-container {
            padding-top: 1.3rem;
            padding-bottom: 2rem;
            max-width: 1240px;
        }
        .proposal-card {
            border: 1px solid #d6e2f0;
            border-radius: 20px;
            background: linear-gradient(180deg, #ffffff 0%, #f4f8fd 100%);
            padding: 0.9rem 1rem;
            min-height: 220px;
            box-shadow: 0 10px 25px rgba(32, 74, 135, 0.08);
        }
        .proposal-title {
            font-weight: 700;
            color: #11273f;
            margin-bottom: 0.3rem;
            font-size: 1.06rem;
        }
        .proposal-caption {
            color: #3f5268;
            font-size: 0.92rem;
            line-height: 1.35;
        }
        .chip {
            display: inline-block;
            padding: 0.25rem 0.55rem;
            border-radius: 999px;
            border: 1px solid #c8d7e8;
            margin-right: 0.4rem;
            margin-top: 0.25rem;
            background: #f5f9ff;
            color: #274b72;
            font-size: 0.78rem;
        }
        .insight-line {
            border-left: 4px solid #2e77d0;
            background: #eff6ff;
            color: #244567;
            padding: 0.55rem 0.7rem;
            border-radius: 10px;
            margin: 0.25rem 0 0.85rem 0;
            font-size: 0.9rem;
        }
        .section-title {
            font-weight: 700;
            color: #1f3f63;
            margin: 0.2rem 0 0.45rem 0;
            font-size: 1rem;
        }
        .info-icon {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 18px;
            height: 18px;
            border-radius: 999px;
            font-size: 0.75rem;
            background: #e9f3ff;
            color: #1f5da0;
            border: 1px solid #bdd7f5;
            margin-left: 6px;
            cursor: help;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
