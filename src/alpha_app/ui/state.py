from __future__ import annotations

import streamlit as st

from alpha_app.core.pipeline import AlphaPipeline


def get_pipeline() -> AlphaPipeline:
    if "alpha_pipeline" not in st.session_state:
        st.session_state["alpha_pipeline"] = AlphaPipeline()
    return st.session_state["alpha_pipeline"]

