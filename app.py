from __future__ import annotations

import streamlit as st

import bootstrap_path  # noqa: F401
from alpha_app import config as app_config
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

FEED_PAGE_SIZE = int(getattr(app_config, "FEED_PAGE_SIZE", 25))
MUNICIPALITY_NAME = str(getattr(app_config, "MUNICIPALITY_NAME", "Δήμος"))
REACTION_LABELS = dict(
    getattr(
        app_config,
        "REACTION_LABELS",
        {
            "like": "Μου αρέσει",
            "dislike": "Δεν μου αρέσει",
            "love": "Τέλειο",
            "angry": "Θυμός",
            "sad": "Λύπη",
            "wow": "Έκπληξη",
        },
    )
)
STATUS_LABELS = dict(
    getattr(
        app_config,
        "STATUS_LABELS",
        {
            "planned": "Σχεδιασμένο",
            "active": "Ενεργό",
            "delayed": "Καθυστερημένο",
            "completed": "Ολοκληρωμένο",
        },
    )
)

st.set_page_config(page_title="Civic Lens", page_icon="🏛️", layout="wide")
apply_theme()

AUTH_USER = "datalabcivictest"
AUTH_PASSWORD = "datalabcivictest"

if "selected_proposal_id" not in st.session_state:
    st.session_state["selected_proposal_id"] = None
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False


def _info_title(title: str, tip: str) -> None:
    safe_tip = tip.replace("'", "&#39;")
    st.markdown(
        f"<div class='section-title'>{title}<span class='info-icon' title='{safe_tip}'>i</span></div>",
        unsafe_allow_html=True,
    )


def render_login() -> None:
    st.title("Είσοδος στην πλατφόρμα")
    st.caption("Προστασία πρόσβασης για παρουσίαση blueprint.")
    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Χρήστης")
        password = st.text_input("Κωδικός", type="password")
        submit = st.form_submit_button("Σύνδεση", use_container_width=True)
    if submit:
        if username == AUTH_USER and password == AUTH_PASSWORD:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Λάθος στοιχεία πρόσβασης.")


if not st.session_state["authenticated"]:
    render_login()
    st.stop()

pipeline = get_pipeline()


def render_cards() -> None:
    st.subheader("Αναρτήσεις Δήμου")
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
                    <span class="chip">{STATUS_LABELS.get(card.status, card.status)}</span>
                    <span class="chip">{card.comments_total} σχόλια</span>
                    <span class="chip">{card.total_reactions} αντιδράσεις</span>
                    <span class="chip">υποστήριξη {int(card.support_ratio * 100)}%</span>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Άνοιγμα ανάρτησης", key=f"open_{card.proposal_id}", use_container_width=True):
                st.session_state["selected_proposal_id"] = card.proposal_id


def _reaction_text(breakdown: dict[str, int]) -> str:
    parts: list[str] = []
    for key, label in REACTION_LABELS.items():
        value = int(breakdown.get(key, 0))
        if value > 0:
            parts.append(f"{label}: {value}")
    return " | ".join(parts) if parts else "Χωρίς αντιδράσεις"


def _render_municipal_post(expanded) -> None:
    proposal = expanded.proposal
    with st.container(border=True):
        st.markdown(f"### Ανάρτηση Δήμου: {proposal.title}")
        c1, c2 = st.columns([1.1, 1.8], gap="large")
        with c1:
            st.image(proposal.image_url, use_container_width=True)
        with c2:
            st.caption(f"{MUNICIPALITY_NAME} · Δημοσίευση πολιτικής πρότασης")
            st.markdown(proposal.long_description)
            st.caption(
                f"Περίοδος: {proposal.start_date.isoformat()} έως {proposal.end_date.isoformat()} · "
                f"Προϋπολογισμός: {proposal.budget_eur:,.0f} EUR"
            )
            st.markdown("**Σύνδεσμοι**")
            for link in proposal.links:
                st.markdown(f"- [{link.label}]({link.url})")


def render_discussion_workspace(proposal_id: str) -> None:
    expanded = pipeline.open_card(proposal_id)
    page_key = f"feed_page_{proposal_id}"
    if page_key not in st.session_state:
        st.session_state[page_key] = 1

    _render_municipal_post(expanded)

    sort_options = {
        "Πιο δημοφιλή": "most_reacted",
        "Νεότερα": "newest",
        "Πιο σχετικά": "most_relevant",
    }
    view_options = {
        "Όλα": "all",
        "Μόνο αρχικά σχόλια": "top_level",
        "Χρειάζονται έλεγχο": "needs_review",
    }

    c1, c2, c3, c4 = st.columns([1.2, 1.2, 1.0, 1.0])
    with c1:
        sort_label = st.selectbox("Ταξινόμηση", list(sort_options.keys()), index=0, key=f"sort_{proposal_id}")
    with c2:
        view_label = st.selectbox("Προβολή", list(view_options.keys()), index=0, key=f"view_{proposal_id}")
    with c3:
        include_replies = st.toggle("Εμφάνιση απαντήσεων", value=True, key=f"replies_{proposal_id}")
    with c4:
        if st.button("Επαναφορά σελίδας", key=f"reset_page_{proposal_id}", use_container_width=True):
            st.session_state[page_key] = 1
            st.rerun()

    active_filters = {"view": view_options[view_label], "show_hidden": False}
    rows = pipeline.discussion_feed(
        proposal_id,
        sort=sort_options[sort_label],  # type: ignore[arg-type]
        include_replies=include_replies,
        page=1,
        page_size=st.session_state[page_key] * FEED_PAGE_SIZE,
        filters=active_filters,
    )
    total_rows = pipeline.discussion_total_count(proposal_id, include_replies=include_replies, filters=active_filters)
    author_by_id = {row["comment_id"]: row["author_name"] for row in rows}
    row_by_id = {str(row["comment_id"]): row for row in rows}
    children_by_parent: dict[str, list[str]] = {}
    for row in rows:
        cid = str(row["comment_id"])
        parent = row["parent_comment_id"]
        if parent is not None:
            children_by_parent.setdefault(str(parent), []).append(cid)
    root_ids = [str(row["comment_id"]) for row in rows if row["parent_comment_id"] is None or str(row["parent_comment_id"]) not in row_by_id]

    left, right = st.columns([2.0, 1.0], gap="large")
    with left:
        st.markdown("#### Συζήτηση κατοίκων")
        st.caption(f"Εμφανίζονται {len(rows)} από {total_rows} σχόλια/απαντήσεις")
        def render_node(comment_id: str) -> None:
            row = row_by_id[comment_id]
            depth = int(row["thread_depth"])
            parent_id = row["parent_comment_id"]
            parent_author = author_by_id.get(str(parent_id), "κάτοικο") if parent_id else None
            margin_left = depth * 24
            st.markdown(f"<div style='margin-left:{margin_left}px'>", unsafe_allow_html=True)
            with st.container(border=True):
                if parent_id:
                    st.caption(f"↳ Απάντηση σε σχόλιο του/της {parent_author}")
                st.markdown(
                    f"**{row['author_name']}** · {row['submitted_at']} · "
                    f"αντιδράσεις: `{row['total_reacts']}` · ένταση: `{row['signed_score_raw']}`"
                )
                st.write(row["comment_text"])
                st.caption(_reaction_text(row["reaction_breakdown"]))
                reasons = ", ".join(row["review_reason_codes"]) if row["review_reason_codes"] else "Καμία"
                st.caption(
                    f"Συναίσθημα: {row['sentiment']} | Στάση: {row['stance']} | "
                    f"Ποιότητα: {row['quality']:.2f} | Λόγοι ελέγχου: {reasons}"
                )
                with st.expander("Ανάλυση σχολίου", expanded=False):
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
            child_ids = children_by_parent.get(comment_id, [])
            if child_ids:
                with st.expander(f"Απαντήσεις ({len(child_ids)})", expanded=False):
                    for child_id in child_ids:
                        render_node(child_id)
            st.markdown("</div>", unsafe_allow_html=True)

        for root_id in root_ids:
            render_node(root_id)

        if len(rows) < total_rows:
            if st.button("Φόρτωση περισσότερων", key=f"load_more_{proposal_id}", use_container_width=True):
                st.session_state[page_key] += 1
                st.rerun()

    with right:
        st.markdown("#### Πρακτική εικόνα πρότασης")
        metrics = pipeline.proposal_action_metrics(proposal_id)
        m1, m2 = st.columns(2)
        m1.metric("Αρχικά σχόλια", int(metrics["participation_volume"]))
        m2.metric("Σύνολο αντιδράσεων", int(metrics["total_reacts"]))
        m3, m4 = st.columns(2)
        m3.metric("Δείκτης στήριξης/αντίθεσης", f"{float(metrics['support_opposition_index']):.2f}")
        m4.metric("Ακατέργαστος δείκτης", f"{float(metrics['support_opposition_raw']):.1f}")
        m5, m6 = st.columns(2)
        m5.metric("Κίνδυνος τοξικότητας", f"{float(metrics['civility_risk_rate']) * 100:.1f}%")
        m6.metric("Πίεση ελέγχου", f"{float(metrics['review_queue_pressure']) * 100:.1f}%")

        st.markdown("**Κυρίαρχες ανησυχίες**")
        clusters = metrics.get("top_concern_clusters", [])
        if clusters:
            for item in clusters:
                st.markdown(f"- `{item['topic']}` ({item['count']})")
        else:
            st.caption("Δεν υπάρχουν ακόμα σαφείς συστάδες.")


def _plot_with_info(title: str, tip: str, fig) -> None:
    _info_title(title, tip)
    st.plotly_chart(fig, width="stretch")


def render_analysis_tabs(proposal_id: str) -> None:
    overview, proposal_series = pipeline.build_dashboard_data(mode="basic", proposal_id=proposal_id)
    overview_adv, proposal_adv = pipeline.build_dashboard_data(mode="advanced", proposal_id=proposal_id)

    tab_discussion, tab_analysis, tab_advanced, tab_dev = st.tabs(["Συζήτηση", "Ανάλυση", "Προχωρημένα", "Τεχνικά (Dev)"])

    with tab_discussion:
        render_discussion_workspace(proposal_id)

    with tab_analysis:
        st.markdown("#### Βασικά διαγράμματα απόφασης")
        a1, a2 = st.columns(2)
        with a1:
            _plot_with_info(
                "Συναίσθημα και στάση",
                "Δείχνει αν οι τοποθετήσεις είναι υπέρ/κατά και με ποιο συναισθηματικό πρόσημο.",
                proposal_sentiment_stance_fig(proposal_series),
            )
        with a2:
            _plot_with_info(
                "Κυρίαρχα θέματα",
                "Τα πιο συχνά θέματα της συζήτησης για την τρέχουσα ανάρτηση.",
                proposal_topic_fig(proposal_series),
            )
        a3, a4 = st.columns(2)
        with a3:
            _plot_with_info(
                "Ποιότητα επιχειρημάτων",
                "Κατανομή ποιότητας σχολίων με βάση τεκμηρίωση/δομή/σαφήνεια.",
                proposal_quality_fig(proposal_series, advanced=False),
            )
        with a4:
            _plot_with_info(
                "Κατάσταση ελέγχου",
                "Ποιο ποσοστό σχολίων έμεινε ως έχει, διορθώθηκε ή χρειάζεται περαιτέρω έλεγχο.",
                proposal_review_state_mix_fig(proposal_series),
            )

    with tab_advanced:
        st.markdown("#### Εκτεταμένα διαγράμματα")
        b1, b2 = st.columns(2)
        with b1:
            _plot_with_info("Σύγκριση προτάσεων", "Σύγκριση συμμετοχής/αντιδράσεων/στήριξης ανά πρόταση.", overview_comparison_fig(overview_adv))
        with b2:
            _plot_with_info("Συναίσθημα ανά πρόταση", "Κατανομή θετικών/ουδέτερων/αρνητικών σχολίων ανά πρόταση.", overview_sentiment_fig(overview_adv))
        b3, b4 = st.columns(2)
        with b3:
            _plot_with_info("Εξέλιξη στον χρόνο", "Πώς αλλάζει ο όγκος σχολίων ανά ημέρα.", overview_trend_fig(overview_adv))
        with b4:
            _plot_with_info("Επίδραση υπηρεσιών", "Ποιες υπηρεσίες επηρεάζονται περισσότερο από τη συζήτηση.", overview_service_fig(overview_adv))
        b5, b6 = st.columns(2)
        with b5:
            _plot_with_info("Ρυθμός αντιδράσεων", "Δείχνει ένταση και χρονισμό αντιδράσεων ανά σχόλιο.", proposal_reaction_velocity_fig(proposal_adv))
        with b6:
            _plot_with_info("Διορθώσεις ανά δείκτη", "Σε ποια πεδία η διαδικασία ελέγχου κάνει περισσότερες διορθώσεις.", proposal_correction_rates_fig(proposal_adv))
        b7, b8 = st.columns(2)
        with b7:
            _plot_with_info("Καθυστέρηση ελέγχου", "Χρόνος μέχρι την τελική κατάσταση ανά σχόλιο.", proposal_review_lag_fig(proposal_adv))
        with b8:
            _plot_with_info("Ποιότητα review", "Συγκεντρωτικοί δείκτες ποιότητας του review ανά πρόταση.", overview_quality_fig(overview_adv))

    with tab_dev:
        st.markdown("#### Τεχνική τηλεμετρία αρχιτεκτονικής")
        arch = pipeline.architecture_metrics()
        d1, d2 = st.columns(2)
        with d1:
            _plot_with_info("Έξοδοι πρακτόρων", "Ποια labels παράγουν οι πράκτορες stage-1.", arch_agent_outputs_fig(arch["agent_outputs"]))
        with d2:
            _plot_with_info("Βεβαιότητα πρακτόρων", "Κατανομή confidence ανά πράκτορα.", arch_agent_confidence_fig(arch["agent_confidence"]))
        d3, d4 = st.columns(2)
        with d3:
            _plot_with_info("Classifier vs LLM", "Ισορροπία φόρτου και confidence ανά οικογένεια.", arch_classifier_vs_llm_fig(arch["classifier_vs_llm"]))
        with d4:
            _plot_with_info("Έλεγχος API", "Περασμένα/αποτυχημένα validation events.", arch_api_validation_fig(arch["api_validation"]))
        d5, d6 = st.columns(2)
        with d5:
            _plot_with_info("Ουρά επεξεργασίας", "Βάθος ουράς και throughput ανά βήμα.", arch_queue_timeline_fig(arch["queue_timeline"]))
        with d6:
            _plot_with_info("Bypass vs NLP", "Σύγκριση διαδρομών event processing.", arch_bypass_vs_nlp_fig(arch["bypass_vs_nlp"]))
        d7, d8 = st.columns(2)
        with d7:
            _plot_with_info("Όγκος αποθήκευσης", "Πλήθος εγγραφών stage-1/stage-2 στον χρόνο.", arch_store_volume_fig(arch["store_volume"]))
        with d8:
            _plot_with_info("Φρεσκάδα δεδομένων", "Καθυστέρηση από παραγωγή insight έως dashboard.", arch_store_freshness_fig(arch["store_freshness"]))
        d9, d10 = st.columns(2)
        with d9:
            _plot_with_info("Scheduler triggers", "Πότε θα ενεργοποιούνταν κανόνες εκτέλεσης.", arch_scheduler_trigger_fig(arch["scheduler_triggers"]))
        with d10:
            _plot_with_info("Calibration", "ECE/Brier proxies ανά head.", arch_calibration_fig(arch["calibration_metrics"]))
        d11, d12 = st.columns(2)
        with d11:
            _plot_with_info("Abstain λόγοι", "Γιατί στέλνουμε δείγματα σε ανθρώπινο review.", arch_abstain_summary_fig(arch["abstain_summary"]))
        with d12:
            _plot_with_info("Συγκρούσεις σημάτων", "Περιπτώσεις αντίφασης μεταξύ heads.", arch_conflict_summary_fig(arch["conflict_summary"]))
        _plot_with_info("Κατανομή συναισθημάτων", "Ποιο συναίσθημα κυριαρχεί στο σύνολο σχολίων.", arch_emotion_distribution_fig(arch["emotion_distribution"]))


st.title(f"{MUNICIPALITY_NAME} - Πλατφόρμα Δημόσιας Διαβούλευσης")
st.caption("Blueprint mockup: δημοτική ανάρτηση, νήμα σχολίων/απαντήσεων και πρακτική ανάλυση.")
_, top_right = st.columns([6, 1])
with top_right:
    if st.button("Αποσύνδεση", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()

render_cards()
selected = st.session_state.get("selected_proposal_id")
if selected:
    render_analysis_tabs(selected)
else:
    st.info("Άνοιξε μία ανάρτηση για να δεις πλήρη συζήτηση, απαντήσεις και ανάλυση.")
