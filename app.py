from __future__ import annotations

import html

import pandas as pd
import plotly.express as px
import pydeck as pdk
import streamlit as st

import bootstrap_path  # noqa: F401
from alpha_app.config import MUNICIPALITY_NAME, SERVICE_LABELS, STATUS_LABELS
from alpha_app.domain.models import ProposalExpandedViewModel
from alpha_app.ui.charts import (
    arch_agent_confidence_fig,
    arch_agent_outputs_fig,
    arch_api_validation_fig,
    arch_bypass_vs_nlp_fig,
    arch_classifier_vs_llm_fig,
    arch_queue_timeline_fig,
    arch_scheduler_trigger_fig,
    arch_store_freshness_fig,
    arch_store_volume_fig,
    overview_comparison_fig,
    overview_quality_fig,
    overview_sentiment_fig,
    overview_service_fig,
    overview_trend_fig,
    proposal_correction_rates_fig,
    proposal_quality_fig,
    proposal_reaction_velocity_fig,
    proposal_review_lag_fig,
    proposal_review_state_mix_fig,
    proposal_sentiment_stance_fig,
    proposal_topic_fig,
)
from alpha_app.ui.state import get_pipeline
from alpha_app.ui.theme import apply_theme

st.set_page_config(page_title="Î Î¹Î»Î¿Ï„Î¹ÎºÎ® Î Î»Î±Ï„Ï†ÏŒÏÎ¼Î± Î£Ï…Î¼Î¼ÎµÏ„Î¿Ï‡Î®Ï‚", page_icon="ðŸ›ï¸", layout="wide")
apply_theme()

AUTH_USER = "datalabcivictest"
AUTH_PASSWORD = "datalabcivictest"

if "selected_proposal_id" not in st.session_state:
    st.session_state["selected_proposal_id"] = None
if "service_filter" not in st.session_state:
    st.session_state["service_filter"] = []
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False


def render_login() -> None:
    st.title("Î•Î¯ÏƒÎ¿Î´Î¿Ï‚ ÏƒÏ„Î·Î½ ÎµÏ†Î±ÏÎ¼Î¿Î³Î®")
    st.caption("Î‘Ï€Î»Î® Ï€ÏÎ¿ÏƒÏ„Î±ÏƒÎ¯Î± Ï€ÏÏŒÏƒÎ²Î±ÏƒÎ·Ï‚ Î³Î¹Î± online demo.")
    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Î§ÏÎ®ÏƒÏ„Î·Ï‚")
        password = st.text_input("ÎšÏ‰Î´Î¹ÎºÏŒÏ‚", type="password")
        submit = st.form_submit_button("Î£ÏÎ½Î´ÎµÏƒÎ·", use_container_width=True)
    if submit:
        if username == AUTH_USER and password == AUTH_PASSWORD:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Î›Î¬Î¸Î¿Ï‚ ÏƒÏ„Î¿Î¹Ï‡ÎµÎ¯Î± Ï€ÏÏŒÏƒÎ²Î±ÏƒÎ·Ï‚.")


if not st.session_state["authenticated"]:
    render_login()
    st.stop()

pipeline = get_pipeline()


def section_title(title: str, tip: str) -> None:
    safe_tip = html.escape(tip, quote=True)
    st.markdown(
        f"<div class='section-title'>{title}<span class='info-icon' title='{safe_tip}'>i</span></div>",
        unsafe_allow_html=True,
    )


st.title(f"{MUNICIPALITY_NAME} - Î Î¹Î»Î¿Ï„Î¹ÎºÎ® Î Î»Î±Ï„Ï†ÏŒÏÎ¼Î± Î ÏÎ¿Ï„Î¬ÏƒÎµÏ‰Î½")
st.caption("ÎšÎ¬ÏÏ„ÎµÏ‚ Ï€ÏÎ¿Ï„Î¬ÏƒÎµÏ‰Î½, Î±Ï…Ï„ÏŒÎ¼Î±Ï„Î· Ï€ÏÎ¿ÏƒÎ¿Î¼Î¿Î¯Ï‰ÏƒÎ· Î±Î½Î¬Î»Ï…ÏƒÎ·Ï‚ ÎºÎ±Î¹ Ï€Î¯Î½Î±ÎºÎµÏ‚ Î¼ÏŒÎ½Î¿ Î¼Îµ Î³ÏÎ±Ï†Î®Î¼Î±Ï„Î±.")
top_auth_left, top_auth_right = st.columns([6, 1])
with top_auth_right:
    if st.button("Î‘Ï€Î¿ÏƒÏÎ½Î´ÎµÏƒÎ·", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()


def render_cards() -> None:
    cards = pipeline.get_card_summaries()
    cols = st.columns(3, gap="large")
    for idx, card in enumerate(cards):
        with cols[idx]:
            st.markdown(
                f"""
                <div class="proposal-card">
                  <div class="proposal-title">{card.title}</div>
                  <div class="proposal-caption">{card.short_description}</div>
                  <div style="margin-top:0.65rem;">
                    <span class="chip">{STATUS_LABELS[card.status]}</span>
                    <span class="chip">{card.comments_total} ÏƒÏ‡ÏŒÎ»Î¹Î±</span>
                    <span class="chip">{card.total_reactions} Î±Î½Ï„Î¹Î´ÏÎ¬ÏƒÎµÎ¹Ï‚</span>
                    <span class="chip">Î¸ÎµÏ„Î¹ÎºÎ® Ï„Î¬ÏƒÎ· {int(card.support_ratio*100)}%</span>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Î†Î½Î¿Î¹Î³Î¼Î± ÎºÎ¬ÏÏ„Î±Ï‚", key=f"open_{card.proposal_id}", use_container_width=True):
                st.session_state["selected_proposal_id"] = card.proposal_id


def _service_rows(expanded: ProposalExpandedViewModel, selected_services: list[str]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for feature in expanded.proposal.map_polygon_geojson["features"]:
        services: list[str] = feature["properties"]["services"]
        if selected_services and not any(service in services for service in selected_services):
            continue
        rows.append(
            {
                "polygon": feature["geometry"]["coordinates"][0],
                "area": feature["properties"]["area"],
                "services": ", ".join(SERVICE_LABELS.get(s, s) for s in services),
                "service_count": len(services),
            }
        )
    return rows


def render_expanded_post(proposal_id: str) -> None:
    expanded = pipeline.open_card(proposal_id)
    proposal = expanded.proposal

    st.divider()
    st.subheader(f"{proposal.title} - Î‘Î½Î±Î»Ï…Ï„Î¹ÎºÎ® ÎºÎ¬ÏÏ„Î± Ï€ÏÏŒÏ„Î±ÏƒÎ·Ï‚")
    top1, top2, top3 = st.columns([1.2, 1, 1])
    with top1:
        st.image(proposal.image_url, use_container_width=True)
    with top2:
        st.metric("ÎˆÎ½Î±ÏÎ¾Î·", proposal.start_date.isoformat())
        st.metric("Î›Î®Î¾Î·", proposal.end_date.isoformat())
        st.metric("ÎšÎ±Ï„Î¬ÏƒÏ„Î±ÏƒÎ·", STATUS_LABELS[proposal.status])
    with top3:
        st.metric("Î ÏÎ¿Ï‹Ï€Î¿Î»Î¿Î³Î¹ÏƒÎ¼ÏŒÏ‚ (EUR)", f"{proposal.budget_eur:,.0f}")
        st.markdown("**Î ÎµÏÎ¹Î¿Ï‡Î­Ï‚ Ï€Î¿Ï… ÎµÏ€Î·ÏÎµÎ¬Î¶Î¿Î½Ï„Î±Î¹**")
        for area in proposal.affected_areas:
            st.markdown(f"- {area}")

    st.markdown(f"**Î”Î®Î¼Î¿Ï‚:** {MUNICIPALITY_NAME}")
    st.markdown(f"**Î ÎµÏÎ¹Î³ÏÎ±Ï†Î®:** {proposal.long_description}")
    st.markdown("**Î£ÏÎ½Î´ÎµÏƒÎ¼Î¿Î¹**")
    for link in proposal.links:
        st.markdown(f"- [{link.label}]({link.url})")

    rleft, rright = st.columns([1, 1.8])
    with rleft:
        reacts_df = pd.DataFrame({"Î±Î½Ï„Î¯Î´ÏÎ±ÏƒÎ·": list(expanded.reactions.keys()), "Ï€Î»Î®Î¸Î¿Ï‚": list(expanded.reactions.values())})
        section_title(
            "Î“ÏÎ¬Ï†Î·Î¼Î± Î±Î½Ï„Î¹Î´ÏÎ¬ÏƒÎµÏ‰Î½",
            "Î”ÎµÎ¯Ï‡Î½ÎµÎ¹ Ï€ÏŒÏƒÎµÏ‚ Î±Î½Ï„Î¹Î´ÏÎ¬ÏƒÎµÎ¹Ï‚ Ï€Î®ÏÎµ Î· Ï€ÏÏŒÏ„Î±ÏƒÎ· Î±Î½Î¬ Ï„ÏÏ€Î¿. ÎˆÏ„ÏƒÎ¹ Î²Î»Î­Ï€ÎµÎ¹Ï‚ Î±Î½ Î· ÏƒÏ…Î¶Î®Ï„Î·ÏƒÎ· ÎµÎ¯Î½Î±Î¹ ÎºÏ…ÏÎ¯Ï‰Ï‚ Ï…Ï€Î¿ÏƒÏ„Î·ÏÎ¹ÎºÏ„Î¹ÎºÎ® Î® Î±ÏÎ½Î·Ï„Î¹ÎºÎ®.",
        )
        reaction_fig = px.bar(reacts_df, x="Î±Î½Ï„Î¯Î´ÏÎ±ÏƒÎ·", y="Ï€Î»Î®Î¸Î¿Ï‚", title="Î‘Î½Ï„Î¹Î´ÏÎ¬ÏƒÎµÎ¹Ï‚ Ï€ÏÏŒÏ„Î±ÏƒÎ·Ï‚")
        st.plotly_chart(reaction_fig, use_container_width=True)
    with rright:
        comments = pipeline.comments_for_proposal(proposal_id)
        if comments:
            st.markdown("**Î¡Î¿Î® ÏƒÏ‡Î¿Î»Î¯Ï‰Î½**")
            for row in comments:
                with st.container(border=True):
                    st.markdown(f"**{row['author_name']}** Â· {row['submitted_at']}")
                    st.markdown(row["comment_text"])
                    st.caption(
                        f"Î£Ï…Î½Î±Î¯ÏƒÎ¸Î·Î¼Î±: {row['sentiment']} | Î£Ï„Î¬ÏƒÎ·: {row['stance']} | "
                        f"Î Î¿Î¹ÏŒÏ„Î·Ï„Î±: {row['quality']:.2f} | Î‘Î½Ï„Î¹Î´ÏÎ¬ÏƒÎµÎ¹Ï‚: {row['reactions_total']}"
                    )

    all_services = sorted({s for feature in proposal.map_polygon_geojson["features"] for s in feature["properties"]["services"]})
    default_services = st.session_state.get("service_filter") or all_services
    selected_services = st.multiselect(
        "Î¦Î¯Î»Ï„ÏÎ¿ Ï…Ï€Î·ÏÎµÏƒÎ¹ÏŽÎ½ ÏƒÏ„Î¿Î½ Ï‡Î¬ÏÏ„Î·",
        options=all_services,
        default=default_services,
        format_func=lambda x: SERVICE_LABELS.get(x, x),
    )
    st.session_state["service_filter"] = selected_services
    map_rows = _service_rows(expanded, selected_services)
    if map_rows:
        section_title(
            "Î§Î¬ÏÏ„Î·Ï‚ ÎµÏ€Î·ÏÎµÎ±Î¶ÏŒÎ¼ÎµÎ½Ï‰Î½ Ï€ÎµÏÎ¹Î¿Ï‡ÏŽÎ½",
            "ÎŸÎ¹ Ï€Î¿Î»ÏÎ³Ï‰Î½ÎµÏ‚ Ï€ÎµÏÎ¹Î¿Ï‡Î­Ï‚ Î´ÎµÎ¯Ï‡Î½Î¿Ï…Î½ Ï€Î¿Ï ÎµÏ€Î·ÏÎµÎ¬Î¶ÎµÏ„Î±Î¹ Î· Ï€ÏŒÎ»Î· Î±Ï€ÏŒ Ï„Î·Î½ Ï€ÏÏŒÏ„Î±ÏƒÎ·. ÎœÎµ Ï„Î¿ Ï†Î¯Î»Ï„ÏÎ¿ Ï…Ï€Î·ÏÎµÏƒÎ¹ÏŽÎ½ Î²Î»Î­Ï€ÎµÎ¹Ï‚ Î¼ÏŒÎ½Î¿ Ï„Î¹Ï‚ ÏƒÏ‡ÎµÏ„Î¹ÎºÎ­Ï‚ ÎµÏ€Î¹Î´ÏÎ¬ÏƒÎµÎ¹Ï‚.",
        )
        map_df = pd.DataFrame(map_rows)
        layer = pdk.Layer(
            "PolygonLayer",
            data=map_df,
            get_polygon="polygon",
            get_fill_color="[40 + 25 * service_count, 120, 210, 140]",
            get_line_color=[20, 60, 110],
            pickable=True,
        )
        view_state = pdk.ViewState(latitude=40.635, longitude=22.94, zoom=11.2, pitch=30)
        st.pydeck_chart(
            pdk.Deck(
                layers=[layer],
                initial_view_state=view_state,
                tooltip={"text": "{area}\nÏ…Ï€Î·ÏÎµÏƒÎ¯ÎµÏ‚: {services}"},
                map_style=None,
            ),
            use_container_width=True,
        )


def render_dashboards(selected_proposal_id: str | None) -> None:
    st.divider()
    st.subheader("Î Î¯Î½Î±ÎºÎµÏ‚ ÎµÎ»Î­Î³Ï‡Î¿Ï… (Î¼ÏŒÎ½Î¿ Î³ÏÎ±Ï†Î®Î¼Î±Ï„Î±)")
    mode = st.radio("Î›ÎµÎ¹Ï„Î¿Ï…ÏÎ³Î¯Î±", ["basic", "advanced"], horizontal=True, index=0)
    target = selected_proposal_id or pipeline.get_card_summaries()[0].proposal_id
    services = st.session_state.get("service_filter") or []
    overview_series, proposal_series = pipeline.build_dashboard_data(mode=mode, proposal_id=target, service_filter=services)

    overview_tab, proposal_tab = st.tabs(["Î£Ï…Î½Î¿Î»Î¹ÎºÎ® ÎµÎ¹ÎºÏŒÎ½Î±", "Î‘Î½Î¬ Ï€ÏÏŒÏ„Î±ÏƒÎ·"])
    with overview_tab:
        st.markdown(f"<div class='insight-line'>{overview_series.insight_line}</div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            section_title(
                "Î£ÏÎ³ÎºÏÎ¹ÏƒÎ· Ï€ÏÎ¿Ï„Î¬ÏƒÎµÏ‰Î½",
                "Î£Ï…Î³ÎºÏÎ¯Î½ÎµÎ¹ Ï€ÏÎ¿Ï„Î¬ÏƒÎµÎ¹Ï‚ ÏƒÎµ ÏƒÏ‡ÏŒÎ»Î¹Î±, Î±Î½Ï„Î¹Î´ÏÎ¬ÏƒÎµÎ¹Ï‚ ÎºÎ±Î¹ Î²Î±Î¸Î¼ÏŒ Ï…Ï€Î¿ÏƒÏ„Î®ÏÎ¹Î¾Î·Ï‚. Î£Îµ Î²Î¿Î·Î¸Î¬ Î½Î± Î´ÎµÎ¹Ï‚ Ï€Î¿Î¹Î± Ï€ÏÏŒÏ„Î±ÏƒÎ· ÏƒÏ…Î³ÎºÎµÎ½Ï„ÏÏŽÎ½ÎµÎ¹ Î¼ÎµÎ³Î±Î»ÏÏ„ÎµÏÎ· ÏƒÏ…Î¼Î¼ÎµÏ„Î¿Ï‡Î®.",
            )
            st.plotly_chart(overview_comparison_fig(overview_series), use_container_width=True)
        with c2:
            section_title(
                "Î£Ï…Î½Î±Î¯ÏƒÎ¸Î·Î¼Î± Î±Î½Î¬ Ï€ÏÏŒÏ„Î±ÏƒÎ·",
                "Î”ÎµÎ¯Ï‡Î½ÎµÎ¹ Î±Î½ Ï„Î± ÏƒÏ‡ÏŒÎ»Î¹Î± ÎµÎ¯Î½Î±Î¹ ÎºÏ…ÏÎ¯Ï‰Ï‚ Î¸ÎµÏ„Î¹ÎºÎ¬, Î¿Ï…Î´Î­Ï„ÎµÏÎ± Î® Î±ÏÎ½Î·Ï„Î¹ÎºÎ¬. ÎˆÏ„ÏƒÎ¹ Ï†Î±Î¯Î½ÎµÏ„Î±Î¹ Î· Î³ÎµÎ½Î¹ÎºÎ® ÏƒÏ„Î¬ÏƒÎ· Ï„Î¿Ï… ÎºÎ¿Î¹Î½Î¿Ï.",
            )
            st.plotly_chart(overview_sentiment_fig(overview_series), use_container_width=True)
        c3, c4 = st.columns(2)
        with c3:
            section_title(
                "Î•Î¾Î­Î»Î¹Î¾Î· ÏƒÏ‡Î¿Î»Î¯Ï‰Î½ ÏƒÏ„Î¿Î½ Ï‡ÏÏŒÎ½Î¿",
                "Î”ÎµÎ¯Ï‡Î½ÎµÎ¹ Ï€ÏŒÏ„Îµ Î±Ï…Î¾Î¬Î½ÎµÏ„Î±Î¹ Î® Î¼ÎµÎ¹ÏŽÎ½ÎµÏ„Î±Î¹ Î· ÏƒÏ…Î¶Î®Ï„Î·ÏƒÎ·. Î•Î¯Î½Î±Î¹ Ï‡ÏÎ®ÏƒÎ¹Î¼Î¿ Î³Î¹Î± ÎµÎ½Ï„Î¿Ï€Î¹ÏƒÎ¼ÏŒ Ï€ÎµÏÎ¹ÏŒÎ´Ï‰Î½ Î­Î½Ï„Î±ÏƒÎ·Ï‚.",
            )
            st.plotly_chart(overview_trend_fig(overview_series), use_container_width=True)
        with c4:
            section_title(
                "Î•Ï€Î¯Î´ÏÎ±ÏƒÎ· Î±Î½Î¬ Ï…Ï€Î·ÏÎµÏƒÎ¯Î±",
                "Î”ÎµÎ¯Ï‡Î½ÎµÎ¹ Ï€Î¿Î¹ÎµÏ‚ Î´Î·Î¼Î¿Ï„Î¹ÎºÎ­Ï‚ Ï…Ï€Î·ÏÎµÏƒÎ¯ÎµÏ‚ ÎµÏ€Î·ÏÎµÎ¬Î¶Î¿Î½Ï„Î±Î¹ Ï€ÎµÏÎ¹ÏƒÏƒÏŒÏ„ÎµÏÎ¿ Î±Ï€ÏŒ Ï„Î¹Ï‚ Ï€ÏÎ¿Ï„Î¬ÏƒÎµÎ¹Ï‚.",
            )
            st.plotly_chart(overview_service_fig(overview_series), use_container_width=True)
        section_title(
            "Review quality overview",
            "Displays correction and unresolved rates per proposal from the mock reviewer pass.",
        )
        st.plotly_chart(overview_quality_fig(overview_series), use_container_width=True)

    with proposal_tab:
        st.markdown(f"<div class='insight-line'>{proposal_series.insight_line}</div>", unsafe_allow_html=True)
        p1, p2 = st.columns(2)
        with p1:
            section_title(
                "Î£Ï…Î½Î±Î¯ÏƒÎ¸Î·Î¼Î± ÎºÎ±Î¹ ÏƒÏ„Î¬ÏƒÎ·",
                "Î£Ï…Î½Î´Ï…Î¬Î¶ÎµÎ¹ Ï„Î¿ Î±Î½ Î¿Î¹ Ï€Î¿Î»Î¯Ï„ÎµÏ‚ Î³ÏÎ¬Ï†Î¿Ï…Î½ Î¸ÎµÏ„Î¹ÎºÎ¬/Î±ÏÎ½Î·Ï„Î¹ÎºÎ¬ ÎºÎ±Î¹ Î±Î½ ÎµÎ¯Î½Î±Î¹ Ï…Ï€Î­Ï Î® ÎºÎ±Ï„Î¬ Ï„Î·Ï‚ Ï€ÏÏŒÏ„Î±ÏƒÎ·Ï‚.",
            )
            st.plotly_chart(proposal_sentiment_stance_fig(proposal_series), use_container_width=True)
        with p2:
            section_title(
                "Î¡Ï…Î¸Î¼ÏŒÏ‚ Î±Î½Ï„Î¹Î´ÏÎ¬ÏƒÎµÏ‰Î½",
                "Î”ÎµÎ¯Ï‡Î½ÎµÎ¹ Ï€ÏŒÏƒÎµÏ‚ Î±Î½Ï„Î¹Î´ÏÎ¬ÏƒÎµÎ¹Ï‚ Î¼Î±Î¶ÎµÏÎ¿Î½Ï„Î±Î¹ Î±Î½Î¬ Ï‡ÏÎ¿Î½Î¹ÎºÎ® ÏƒÏ„Î¹Î³Î¼Î® ÎºÎ±Î¹ Î²Î¿Î·Î¸Î¬ Î½Î± Î²ÏÎµÎ¸Î¿ÏÎ½ ÎºÎ¿ÏÏ…Ï†ÏŽÏƒÎµÎ¹Ï‚ ÎµÎ½Î´Î¹Î±Ï†Î­ÏÎ¿Î½Ï„Î¿Ï‚.",
            )
            st.plotly_chart(proposal_reaction_velocity_fig(proposal_series), use_container_width=True)
        p3, p4 = st.columns(2)
        with p3:
            section_title(
                "ÎšÏ…ÏÎ¯Î±ÏÏ‡Î± Î¸Î­Î¼Î±Ï„Î±",
                "Î”ÎµÎ¯Ï‡Î½ÎµÎ¹ Ï€Î¿Î¹Î± Î¸Î­Î¼Î±Ï„Î± ÎµÎ¼Ï†Î±Î½Î¯Î¶Î¿Î½Ï„Î±Î¹ Ï€Î¹Î¿ ÏƒÏ…Ï‡Î½Î¬ ÏƒÏ„Î± ÏƒÏ‡ÏŒÎ»Î¹Î± Ï„Î·Ï‚ ÏƒÏ…Î³ÎºÎµÎºÏÎ¹Î¼Î­Î½Î·Ï‚ Ï€ÏÏŒÏ„Î±ÏƒÎ·Ï‚.",
            )
            st.plotly_chart(proposal_topic_fig(proposal_series), use_container_width=True)
        with p4:
            section_title(
                "Î Î¿Î¹ÏŒÏ„Î·Ï„Î± ÎµÏ€Î¹Ï‡ÎµÎ¹ÏÎ·Î¼Î¬Ï„Ï‰Î½",
                "Î”ÎµÎ¯Ï‡Î½ÎµÎ¹ Ï€ÏŒÏƒÎ¿ Ï„ÎµÎºÎ¼Î·ÏÎ¹Ï‰Î¼Î­Î½Î± ÎµÎ¯Î½Î±Î¹ Ï„Î± ÏƒÏ‡ÏŒÎ»Î¹Î±. Î¥ÏˆÎ·Î»ÏŒÏ„ÎµÏÎµÏ‚ Ï„Î¹Î¼Î­Ï‚ ÏƒÎ·Î¼Î±Î¯Î½Î¿Ï…Î½ Ï€Î¹Î¿ Î±Î½Î±Î»Ï…Ï„Î¹ÎºÎ­Ï‚ Ï„Î¿Ï€Î¿Î¸ÎµÏ„Î®ÏƒÎµÎ¹Ï‚.",
            )
            st.plotly_chart(proposal_quality_fig(proposal_series, advanced=(mode == "advanced")), use_container_width=True)
        p5, p6 = st.columns(2)
        with p5:
            section_title(
                "Review corrections",
                "Shows correction rate by indicator for the mock reviewer workflow.",
            )
            st.plotly_chart(proposal_correction_rates_fig(proposal_series), use_container_width=True)
        with p6:
            section_title(
                "Review state mix",
                "Distribution of corrected, unchanged, and unresolved review outcomes.",
            )
            st.plotly_chart(proposal_review_state_mix_fig(proposal_series), use_container_width=True)
        section_title(
            "Review lag per comment",
            "Synthetic lag between submission and review finalization for each comment.",
        )
        st.plotly_chart(proposal_review_lag_fig(proposal_series), use_container_width=True)

    st.divider()
    st.subheader("Î“ÏÎ±Ï†Î®Î¼Î±Ï„Î± ÎºÎ¬Î»Ï…ÏˆÎ·Ï‚ Î±ÏÏ‡Î¹Ï„ÎµÎºÏ„Î¿Î½Î¹ÎºÎ®Ï‚ (mockup)")
    arch = pipeline.architecture_metrics()
    a1, a2 = st.columns(2)
    with a1:
        section_title(
            "Î‘Ï€Î¿Ï„ÎµÎ»Î­ÏƒÎ¼Î±Ï„Î± Î±Î½Î¬ Ï€ÏÎ¬ÎºÏ„Î¿ÏÎ±",
            "Î”ÎµÎ¯Ï‡Î½ÎµÎ¹ Ï„Î¹ Ï€Î±ÏÎ¬Î³ÎµÎ¹ ÎºÎ¬Î¸Îµ Ï€ÏÎ¬ÎºÏ„Î¿ÏÎ±Ï‚ (ÏƒÏ…Î½Î±Î¯ÏƒÎ¸Î·Î¼Î±, ÏƒÏ„Î¬ÏƒÎ·, ÎµÎ¹ÏÏ‰Î½ÎµÎ¯Î±, Ï€Î¿Î¹ÏŒÏ„Î·Ï„Î±). ÎœÎµ Î±Ï…Ï„ÏŒ Î²Î»Î­Ï€ÎµÎ¹Ï‚ ÏŒÏ„Î¹ ÏŒÎ»Î± Ï„Î± ÎºÎ¿Î¼Î¼Î¬Ï„Î¹Î± Stage 1 Î­Ï‡Î¿Ï…Î½ Î¿ÏÎ±Ï„ÏŒ output.",
        )
        st.plotly_chart(arch_agent_outputs_fig(arch["agent_outputs"]), use_container_width=True)
    with a2:
        section_title(
            "Î’ÎµÎ²Î±Î¹ÏŒÏ„Î·Ï„Î± Î±Î½Î¬ Ï€ÏÎ¬ÎºÏ„Î¿ÏÎ±",
            "Î£Ï…Î³ÎºÏÎ¯Î½ÎµÎ¹ Ï€ÏŒÏƒÎ¿ ÏƒÎ¯Î³Î¿Ï…ÏÎ¿Ï‚ ÎµÎ¯Î½Î±Î¹ ÎºÎ¬Î¸Îµ Ï€ÏÎ¬ÎºÏ„Î¿ÏÎ±Ï‚ ÏƒÏ„Î¹Ï‚ ÎµÎºÏ„Î¹Î¼Î®ÏƒÎµÎ¹Ï‚ Ï„Î¿Ï…. Î’Î¿Î·Î¸Î¬ ÏƒÏ„Î¿Î½ ÎµÎ½Ï„Î¿Ï€Î¹ÏƒÎ¼ÏŒ Î±Î²Î­Î²Î±Î¹Ï‰Î½ Ï€ÎµÏÎ¹Î¿Ï‡ÏŽÎ½.",
        )
        st.plotly_chart(arch_agent_confidence_fig(arch["agent_confidence"]), use_container_width=True)
    a3, a4 = st.columns(2)
    with a3:
        section_title(
            "ÎšÎ±Ï„Î±Î½Î¿Î¼Î® Ï†ÏŒÏÏ„Î¿Ï…: Ï„Î±Î¾Î¹Î½Î¿Î¼Î·Ï„Î­Ï‚ vs LLM",
            "Î”ÎµÎ¯Ï‡Î½ÎµÎ¹ Ï€ÏŒÏƒÎ· Î´Î¿Ï…Î»ÎµÎ¹Î¬ Î±Î½Î±Î»Î±Î¼Î²Î¬Î½Î¿Ï…Î½ Î¿Î¹ ÎºÎ»Î±ÏƒÎ¹ÎºÎ¿Î¯ Ï„Î±Î¾Î¹Î½Î¿Î¼Î·Ï„Î­Ï‚ ÎºÎ±Î¹ Ï€ÏŒÏƒÎ· Ï„Î± LLM mockups.",
        )
        st.plotly_chart(arch_classifier_vs_llm_fig(arch["classifier_vs_llm"]), use_container_width=True)
    with a4:
        section_title(
            "ÎˆÎ»ÎµÎ³Ï‡Î¿Î¹ ÎµÎ³ÎºÏ…ÏÏŒÏ„Î·Ï„Î±Ï‚ API",
            "Î”ÎµÎ¯Ï‡Î½ÎµÎ¹ Ï€ÏŒÏƒÎ± Î±Î¹Ï„Î®Î¼Î±Ï„Î± Ï€ÎµÏÎ½Î¿ÏÎ½ Î® Î±Ï€Î¿ÏÏÎ¯Ï€Ï„Î¿Î½Ï„Î±Î¹ Î±Ï€ÏŒ Ï„Î¿ Î±ÏÏ‡Î¹ÎºÏŒ validation ÏƒÏ„Î¬Î´Î¹Î¿.",
        )
        st.plotly_chart(arch_api_validation_fig(arch["api_validation"]), use_container_width=True)
    a5, a6 = st.columns(2)
    with a5:
        section_title(
            "ÎŸÏ…ÏÎ¬: Î²Î¬Î¸Î¿Ï‚ ÎºÎ±Î¹ ÏÏ…Î¸Î¼ÏŒÏ‚",
            "Î¤Î¿ Î²Î¬Î¸Î¿Ï‚ Î´ÎµÎ¯Ï‡Î½ÎµÎ¹ Ï€ÏŒÏƒÎ± Ï€ÎµÏÎ¹Î¼Î­Î½Î¿Ï…Î½ ÏƒÏ„Î·Î½ Î¿Ï…ÏÎ¬, ÎµÎ½ÏŽ Î¿ ÏÏ…Î¸Î¼ÏŒÏ‚ Î´ÎµÎ¯Ï‡Î½ÎµÎ¹ Ï€ÏŒÏƒÎ± ÎµÏ€ÎµÎ¾ÎµÏÎ³Î¬Î¶Î¿Î½Ï„Î±Î¹ Î±Î½Î¬ ÎºÏÎºÎ»Î¿.",
        )
        st.plotly_chart(arch_queue_timeline_fig(arch["queue_timeline"]), use_container_width=True)
    with a6:
        section_title(
            "Î Î±ÏÎ¬ÎºÎ±Î¼ÏˆÎ· Î±Î½Ï„Î¹Î´ÏÎ¬ÏƒÎµÏ‰Î½ vs NLP",
            "Î£Ï…Î³ÎºÏÎ¯Î½ÎµÎ¹ Ï„Î·Î½ Î¬Î¼ÎµÏƒÎ· ÏÎ¿Î® Î±Î½Ï„Î¹Î´ÏÎ¬ÏƒÎµÏ‰Î½ Î¼Îµ Ï„Î· ÏÎ¿Î® Ï€Î¿Ï… Ï€ÎµÏÎ½Î¬ Î±Ï€ÏŒ NLP Î±Î½Î¬Î»Ï…ÏƒÎ·.",
        )
        st.plotly_chart(arch_bypass_vs_nlp_fig(arch["bypass_vs_nlp"]), use_container_width=True)
    a7, a8 = st.columns(2)
    with a7:
        section_title(
            "ÎŒÎ³ÎºÎ¿Ï‚ Î±Ï€Î¿Î¸Î®ÎºÎµÏ…ÏƒÎ·Ï‚",
            "Î”ÎµÎ¯Ï‡Î½ÎµÎ¹ Ï€ÏŽÏ‚ Î³ÎµÎ¼Î¯Î¶Î¿Ï…Î½ Î¿Î¹ Î´ÏÎ¿ Î±Ï€Î¿Î¸Î®ÎºÎµÏ‚: Î±Î½Î¬ ÏƒÏ‡ÏŒÎ»Î¹Î¿ ÎºÎ±Î¹ Î±Î½Î¬ ÏƒÏ…Î½Î¿Ï€Ï„Î¹ÎºÎ® Ï€ÏÏŒÏ„Î±ÏƒÎ·.",
        )
        st.plotly_chart(arch_store_volume_fig(arch["store_volume"]), use_container_width=True)
    with a8:
        section_title(
            "Î¦ÏÎµÏƒÎºÎ¬Î´Î± ÎºÎ±Î¹ ÎºÎ±Î¸Ï…ÏƒÏ„Î­ÏÎ·ÏƒÎ· dashboard",
            "Î”ÎµÎ¯Ï‡Î½ÎµÎ¹ Ï€ÏŒÏƒÎ¿ Ï€ÏÏŒÏƒÏ†Î±Ï„Î± ÎµÎ¯Î½Î±Î¹ Ï„Î± Î´ÎµÎ´Î¿Î¼Î­Î½Î± ÎºÎ±Î¹ Ï€ÏŒÏƒÎ· ÎºÎ±Î¸Ï…ÏƒÏ„Î­ÏÎ·ÏƒÎ· Ï…Ï€Î¬ÏÏ‡ÎµÎ¹ Î¼Î­Ï‡ÏÎ¹ Î½Î± ÎµÎ¼Ï†Î±Î½Î¹ÏƒÏ„Î¿ÏÎ½ ÏƒÏ„Î¿ dashboard.",
        )
        st.plotly_chart(arch_store_freshness_fig(arch["store_freshness"]), use_container_width=True)
    section_title(
        "Î ÏÎ¿Î³ÏÎ±Î¼Î¼Î±Ï„Î¹ÏƒÎ¼Î­Î½Î± triggers",
        "Î”ÎµÎ¯Ï‡Î½ÎµÎ¹ Ï€ÏŒÏƒÎµÏ‚ Ï†Î¿ÏÎ­Ï‚ Î¸Î± ÎµÎ½ÎµÏÎ³Î¿Ï€Î¿Î¹Î¿ÏÎ½Ï„Î±Î½ Î¿Î¹ Î±Î½Î±Î»ÏÏƒÎµÎ¹Ï‚ Î¼Îµ ÎºÎ±Î½ÏŒÎ½ÎµÏ‚ Î±Î½Î¬ Ï€Î»Î®Î¸Î¿Ï‚ ÏƒÏ‡Î¿Î»Î¯Ï‰Î½ Î® Ï‡ÏÎ¿Î½Î¹ÎºÏŒ Î´Î¹Î¬ÏƒÏ„Î·Î¼Î±.",
    )
    st.plotly_chart(arch_scheduler_trigger_fig(arch["scheduler_triggers"]), use_container_width=True)


render_cards()
selected = st.session_state.get("selected_proposal_id")
if selected:
    render_expanded_post(selected)
render_dashboards(selected)


