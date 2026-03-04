from __future__ import annotations

import streamlit as st

import bootstrap_path  # noqa: F401
from alpha_app.config import FEED_PAGE_SIZE, MUNICIPALITY_NAME, REACTION_LABELS, STATUS_LABELS
from alpha_app.ui.charts import (
    arch_abstain_summary_fig,
    arch_agent_confidence_fig,
    arch_agent_outputs_fig,
    arch_api_validation_fig,
    arch_bypass_vs_nlp_fig,
    arch_calibration_fig,
    arch_classifier_vs_llm_fig,
    arch_conflict_summary_fig,
    arch_emotion_distribution_fig,
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

st.set_page_config(page_title="Civic Lens", page_icon="🏛️", layout="wide")
apply_theme()

AUTH_USER = "datalabcivictest"
AUTH_PASSWORD = "datalabcivictest"

if "selected_proposal_id" not in st.session_state:
    st.session_state["selected_proposal_id"] = None
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "auth_user" not in st.session_state:
    st.session_state["auth_user"] = AUTH_USER


def render_login() -> None:
    st.title("Civic Lens Login")
    st.caption("Demo authentication for supervisor view.")
    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Sign in", use_container_width=True)
    if submit:
        if username == AUTH_USER and password == AUTH_PASSWORD:
            st.session_state["authenticated"] = True
            st.session_state["auth_user"] = username
            st.rerun()
        else:
            st.error("Invalid credentials.")


if not st.session_state["authenticated"]:
    render_login()
    st.stop()

pipeline = get_pipeline()


def render_cards() -> None:
    st.subheader("Proposal Cards")
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
                    <span class="chip">{card.comments_total} comments</span>
                    <span class="chip">{card.total_reactions} reactions</span>
                    <span class="chip">support {int(card.support_ratio * 100)}%</span>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Open", key=f"open_{card.proposal_id}", use_container_width=True):
                st.session_state["selected_proposal_id"] = card.proposal_id


def _reaction_text(breakdown: dict[str, int]) -> str:
    parts: list[str] = []
    for key, label in REACTION_LABELS.items():
        value = int(breakdown.get(key, 0))
        if value > 0:
            parts.append(f"{label} {value}")
    return " | ".join(parts) if parts else "No reactions"


def render_discussion_workspace(proposal_id: str) -> None:
    expanded = pipeline.open_card(proposal_id)
    proposal = expanded.proposal
    page_key = f"feed_page_{proposal_id}"
    if page_key not in st.session_state:
        st.session_state[page_key] = 1

    st.markdown(f"### {proposal.title}")
    st.caption(proposal.short_description)

    control_left, control_right = st.columns([2.2, 1.0])
    with control_left:
        c1, c2, c3, c4 = st.columns([1.0, 1.0, 1.0, 1.1])
        with c1:
            sort = st.selectbox("Sort", ["most_reacted", "newest", "most_relevant"], index=0, key=f"sort_{proposal_id}")
        with c2:
            view = st.selectbox("View", ["all", "top_level", "needs_review"], index=0, key=f"view_{proposal_id}")
        with c3:
            include_replies = st.toggle("Include replies", value=True, key=f"replies_{proposal_id}")
        with c4:
            show_hidden = st.toggle("Show hidden", value=False, key=f"hidden_{proposal_id}")
    with control_right:
        st.write("")
        if st.button("Reset pagination", key=f"reset_page_{proposal_id}", use_container_width=True):
            st.session_state[page_key] = 1
            st.rerun()

    active_filters = {"view": view, "show_hidden": show_hidden}
    loaded_rows = pipeline.discussion_feed(
        proposal_id,
        sort=sort,  # type: ignore[arg-type]
        include_replies=include_replies,
        page=1,
        page_size=st.session_state[page_key] * FEED_PAGE_SIZE,
        filters=active_filters,
    )
    total_rows = pipeline.discussion_total_count(proposal_id, include_replies=include_replies, filters=active_filters)

    left, right = st.columns([1.95, 1.05], gap="large")
    with left:
        st.markdown("#### Discussion Feed")
        st.caption(f"Loaded {len(loaded_rows)} / {total_rows} rows")

        for row in loaded_rows:
            depth = int(row["thread_depth"])
            margin_left = depth * 24
            status_chip = row["moderation_status"]
            reasons = ", ".join(row["review_reason_codes"]) if row["review_reason_codes"] else "None"
            st.markdown(f"<div style='margin-left:{margin_left}px'>", unsafe_allow_html=True)
            with st.container(border=True):
                st.markdown(
                    f"**{row['author_name']}** · {row['submitted_at']} · status: `{status_chip}` · reacts: `{row['total_reacts']}` · raw score: `{row['signed_score_raw']}`"
                )
                st.write(row["comment_text"])
                st.caption(_reaction_text(row["reaction_breakdown"]))
                st.caption(
                    f"Sentiment: {row['sentiment']} | Stance: {row['stance']} | Quality: {row['quality']:.2f} | Review reasons: {reasons}"
                )

                with st.expander("Analysis details", expanded=False):
                    st.write(
                        {
                            "emotion_scores": row["emotion_scores"],
                            "emotion_intensity": row["emotion_intensity"],
                            "irony_flag": row["irony_flag"],
                            "toxicity_score": row["toxicity_score"],
                            "civility_score": row["civility_score"],
                            "profanity_score": row["profanity_score"],
                            "conflict_flags": row["conflict_flags"],
                            "abstain_flags": row["abstain_flags"],
                        }
                    )

                reason_key = f"reason_{row['comment_id']}"
                default_reason = f"Supervisor {row['moderation_status']} action"
                reason = st.text_input("Action reason", key=reason_key, value=default_reason, label_visibility="collapsed")
                a1, a2, a3 = st.columns(3)
                with a1:
                    if st.button("Flag", key=f"flag_{row['comment_id']}", use_container_width=True):
                        pipeline.apply_moderation_action(str(row["comment_id"]), "flag", st.session_state["auth_user"], reason)
                        st.rerun()
                with a2:
                    if st.button("Hide", key=f"hide_{row['comment_id']}", use_container_width=True):
                        pipeline.apply_moderation_action(str(row["comment_id"]), "hide", st.session_state["auth_user"], reason)
                        st.rerun()
                with a3:
                    if st.button("Escalate", key=f"esc_{row['comment_id']}", use_container_width=True):
                        pipeline.apply_moderation_action(str(row["comment_id"]), "escalate", st.session_state["auth_user"], reason)
                        st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        if len(loaded_rows) < total_rows:
            if st.button("Load more", key=f"load_more_{proposal_id}", use_container_width=True):
                st.session_state[page_key] += 1
                st.rerun()

    with right:
        st.markdown("#### Action Panel")
        metrics = pipeline.proposal_action_metrics(proposal_id)
        m1, m2 = st.columns(2)
        m1.metric("Top-level comments", int(metrics["participation_volume"]))
        m2.metric("Total reactions", int(metrics["total_reacts"]))
        m3, m4 = st.columns(2)
        m3.metric("Support-opposition index", f"{float(metrics['support_opposition_index']):.2f}")
        m4.metric("Raw reaction score", f"{float(metrics['support_opposition_raw']):.1f}")
        m5, m6 = st.columns(2)
        m5.metric("Civility risk rate", f"{float(metrics['civility_risk_rate']) * 100:.1f}%")
        m6.metric("Review queue pressure", f"{float(metrics['review_queue_pressure']) * 100:.1f}%")

        st.markdown("**Top concern clusters**")
        top_clusters = metrics.get("top_concern_clusters", [])
        if top_clusters:
            for item in top_clusters:
                st.markdown(f"- `{item['topic']}` ({item['count']})")
        else:
            st.caption("No clusters yet.")

        st.markdown("**Moderation log (latest)**")
        events = list(reversed(pipeline.moderation_log(proposal_id)))[:12]
        if events:
            for event in events:
                st.caption(
                    f"{event['created_at']} · {event['action']} · {event['previous_status']} -> {event['new_status']} · {event['actor']}"
                )
        else:
            st.caption("No moderation actions yet.")


def render_analysis_tabs(proposal_id: str) -> None:
    overview, proposal_series = pipeline.build_dashboard_data(mode="basic", proposal_id=proposal_id)
    overview_adv, proposal_adv = pipeline.build_dashboard_data(mode="advanced", proposal_id=proposal_id)

    tab_discussion, tab_analysis, tab_advanced, tab_dev = st.tabs(["Discussion", "Analysis", "Advanced", "Dev"])

    with tab_discussion:
        render_discussion_workspace(proposal_id)

    with tab_analysis:
        st.markdown("#### Practical analysis")
        a1, a2 = st.columns(2)
        with a1:
            st.plotly_chart(proposal_sentiment_stance_fig(proposal_series), width="stretch")
        with a2:
            st.plotly_chart(proposal_topic_fig(proposal_series), width="stretch")
        a3, a4 = st.columns(2)
        with a3:
            st.plotly_chart(proposal_quality_fig(proposal_series, advanced=False), width="stretch")
        with a4:
            st.plotly_chart(proposal_review_state_mix_fig(proposal_series), width="stretch")

    with tab_advanced:
        st.markdown("#### Extended charts")
        b1, b2 = st.columns(2)
        with b1:
            st.plotly_chart(overview_comparison_fig(overview_adv), width="stretch")
        with b2:
            st.plotly_chart(overview_sentiment_fig(overview_adv), width="stretch")
        b3, b4 = st.columns(2)
        with b3:
            st.plotly_chart(overview_trend_fig(overview_adv), width="stretch")
        with b4:
            st.plotly_chart(overview_service_fig(overview_adv), width="stretch")
        b5, b6 = st.columns(2)
        with b5:
            st.plotly_chart(proposal_reaction_velocity_fig(proposal_adv), width="stretch")
        with b6:
            st.plotly_chart(proposal_correction_rates_fig(proposal_adv), width="stretch")
        b7, b8 = st.columns(2)
        with b7:
            st.plotly_chart(proposal_review_lag_fig(proposal_adv), width="stretch")
        with b8:
            st.plotly_chart(overview_quality_fig(overview_adv), width="stretch")

    with tab_dev:
        st.markdown("#### Architecture telemetry (dev only)")
        arch = pipeline.architecture_metrics()
        d1, d2 = st.columns(2)
        with d1:
            st.plotly_chart(arch_agent_outputs_fig(arch["agent_outputs"]), width="stretch")
        with d2:
            st.plotly_chart(arch_agent_confidence_fig(arch["agent_confidence"]), width="stretch")
        d3, d4 = st.columns(2)
        with d3:
            st.plotly_chart(arch_classifier_vs_llm_fig(arch["classifier_vs_llm"]), width="stretch")
        with d4:
            st.plotly_chart(arch_api_validation_fig(arch["api_validation"]), width="stretch")
        d5, d6 = st.columns(2)
        with d5:
            st.plotly_chart(arch_queue_timeline_fig(arch["queue_timeline"]), width="stretch")
        with d6:
            st.plotly_chart(arch_bypass_vs_nlp_fig(arch["bypass_vs_nlp"]), width="stretch")
        d7, d8 = st.columns(2)
        with d7:
            st.plotly_chart(arch_store_volume_fig(arch["store_volume"]), width="stretch")
        with d8:
            st.plotly_chart(arch_store_freshness_fig(arch["store_freshness"]), width="stretch")
        d9, d10 = st.columns(2)
        with d9:
            st.plotly_chart(arch_scheduler_trigger_fig(arch["scheduler_triggers"]), width="stretch")
        with d10:
            st.plotly_chart(arch_calibration_fig(arch["calibration_metrics"]), width="stretch")
        d11, d12 = st.columns(2)
        with d11:
            st.plotly_chart(arch_abstain_summary_fig(arch["abstain_summary"]), width="stretch")
        with d12:
            st.plotly_chart(arch_conflict_summary_fig(arch["conflict_summary"]), width="stretch")
        st.plotly_chart(arch_emotion_distribution_fig(arch["emotion_distribution"]), width="stretch")


st.title(f"{MUNICIPALITY_NAME} - Civic Lens")
st.caption("Discussion-first moderation and analysis console (mock++ deterministic mode).")
top_left, top_right = st.columns([6, 1])
with top_right:
    if st.button("Logout", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()

render_cards()
selected = st.session_state.get("selected_proposal_id")
if selected:
    render_analysis_tabs(selected)
else:
    st.info("Open a proposal card to inspect discussion and analysis.")
