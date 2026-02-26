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
    overview_sentiment_fig,
    overview_service_fig,
    overview_trend_fig,
    proposal_quality_fig,
    proposal_reaction_velocity_fig,
    proposal_sentiment_stance_fig,
    proposal_topic_fig,
)
from alpha_app.ui.state import get_pipeline
from alpha_app.ui.theme import apply_theme

st.set_page_config(page_title="Πιλοτική Πλατφόρμα Συμμετοχής", page_icon="🏛️", layout="wide")
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
    st.title("Είσοδος στην εφαρμογή")
    st.caption("Απλή προστασία πρόσβασης για online demo.")
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


def section_title(title: str, tip: str) -> None:
    safe_tip = html.escape(tip, quote=True)
    st.markdown(
        f"<div class='section-title'>{title}<span class='info-icon' title='{safe_tip}'>i</span></div>",
        unsafe_allow_html=True,
    )


st.title(f"{MUNICIPALITY_NAME} - Πιλοτική Πλατφόρμα Προτάσεων")
st.caption("Κάρτες προτάσεων, αυτόματη προσομοίωση ανάλυσης και πίνακες μόνο με γραφήματα.")
top_auth_left, top_auth_right = st.columns([6, 1])
with top_auth_right:
    if st.button("Αποσύνδεση", use_container_width=True):
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
                    <span class="chip">{card.comments_total} σχόλια</span>
                    <span class="chip">{card.total_reactions} αντιδράσεις</span>
                    <span class="chip">θετική τάση {int(card.support_ratio*100)}%</span>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Άνοιγμα κάρτας", key=f"open_{card.proposal_id}", use_container_width=True):
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
    st.subheader(f"{proposal.title} - Αναλυτική κάρτα πρότασης")
    top1, top2, top3 = st.columns([1.2, 1, 1])
    with top1:
        st.image(proposal.image_url, use_container_width=True)
    with top2:
        st.metric("Έναρξη", proposal.start_date.isoformat())
        st.metric("Λήξη", proposal.end_date.isoformat())
        st.metric("Κατάσταση", STATUS_LABELS[proposal.status])
    with top3:
        st.metric("Προϋπολογισμός (EUR)", f"{proposal.budget_eur:,.0f}")
        st.markdown("**Περιοχές που επηρεάζονται**")
        for area in proposal.affected_areas:
            st.markdown(f"- {area}")

    st.markdown(f"**Δήμος:** {MUNICIPALITY_NAME}")
    st.markdown(f"**Περιγραφή:** {proposal.long_description}")
    st.markdown("**Σύνδεσμοι**")
    for link in proposal.links:
        st.markdown(f"- [{link.label}]({link.url})")

    rleft, rright = st.columns([1, 1.8])
    with rleft:
        reacts_df = pd.DataFrame({"αντίδραση": list(expanded.reactions.keys()), "πλήθος": list(expanded.reactions.values())})
        section_title(
            "Γράφημα αντιδράσεων",
            "Δείχνει πόσες αντιδράσεις πήρε η πρόταση ανά τύπο. Έτσι βλέπεις αν η συζήτηση είναι κυρίως υποστηρικτική ή αρνητική.",
        )
        reaction_fig = px.bar(reacts_df, x="αντίδραση", y="πλήθος", title="Αντιδράσεις πρότασης")
        st.plotly_chart(reaction_fig, use_container_width=True)
    with rright:
        comments = pipeline.comments_for_proposal(proposal_id)
        if comments:
            st.markdown("**Ροή σχολίων**")
            for row in comments:
                with st.container(border=True):
                    st.markdown(f"**{row['author_name']}** · {row['submitted_at']}")
                    st.markdown(row["comment_text"])
                    st.caption(
                        f"Συναίσθημα: {row['sentiment']} | Στάση: {row['stance']} | "
                        f"Ποιότητα: {row['quality']:.2f} | Αντιδράσεις: {row['reactions_total']}"
                    )

    all_services = sorted({s for feature in proposal.map_polygon_geojson["features"] for s in feature["properties"]["services"]})
    default_services = st.session_state.get("service_filter") or all_services
    selected_services = st.multiselect(
        "Φίλτρο υπηρεσιών στον χάρτη",
        options=all_services,
        default=default_services,
        format_func=lambda x: SERVICE_LABELS.get(x, x),
    )
    st.session_state["service_filter"] = selected_services
    map_rows = _service_rows(expanded, selected_services)
    if map_rows:
        section_title(
            "Χάρτης επηρεαζόμενων περιοχών",
            "Οι πολύγωνες περιοχές δείχνουν πού επηρεάζεται η πόλη από την πρόταση. Με το φίλτρο υπηρεσιών βλέπεις μόνο τις σχετικές επιδράσεις.",
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
                tooltip={"text": "{area}\nυπηρεσίες: {services}"},
                map_style=None,
            ),
            use_container_width=True,
        )


def render_dashboards(selected_proposal_id: str | None) -> None:
    st.divider()
    st.subheader("Πίνακες ελέγχου (μόνο γραφήματα)")
    mode = st.radio("Λειτουργία", ["basic", "advanced"], horizontal=True, index=0)
    target = selected_proposal_id or pipeline.get_card_summaries()[0].proposal_id
    services = st.session_state.get("service_filter") or []
    overview_series, proposal_series = pipeline.build_dashboard_data(mode=mode, proposal_id=target, service_filter=services)

    overview_tab, proposal_tab = st.tabs(["Συνολική εικόνα", "Ανά πρόταση"])
    with overview_tab:
        st.markdown(f"<div class='insight-line'>{overview_series.insight_line}</div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            section_title(
                "Σύγκριση προτάσεων",
                "Συγκρίνει προτάσεις σε σχόλια, αντιδράσεις και βαθμό υποστήριξης. Σε βοηθά να δεις ποια πρόταση συγκεντρώνει μεγαλύτερη συμμετοχή.",
            )
            st.plotly_chart(overview_comparison_fig(overview_series), use_container_width=True)
        with c2:
            section_title(
                "Συναίσθημα ανά πρόταση",
                "Δείχνει αν τα σχόλια είναι κυρίως θετικά, ουδέτερα ή αρνητικά. Έτσι φαίνεται η γενική στάση του κοινού.",
            )
            st.plotly_chart(overview_sentiment_fig(overview_series), use_container_width=True)
        c3, c4 = st.columns(2)
        with c3:
            section_title(
                "Εξέλιξη σχολίων στον χρόνο",
                "Δείχνει πότε αυξάνεται ή μειώνεται η συζήτηση. Είναι χρήσιμο για εντοπισμό περιόδων έντασης.",
            )
            st.plotly_chart(overview_trend_fig(overview_series), use_container_width=True)
        with c4:
            section_title(
                "Επίδραση ανά υπηρεσία",
                "Δείχνει ποιες δημοτικές υπηρεσίες επηρεάζονται περισσότερο από τις προτάσεις.",
            )
            st.plotly_chart(overview_service_fig(overview_series), use_container_width=True)

    with proposal_tab:
        st.markdown(f"<div class='insight-line'>{proposal_series.insight_line}</div>", unsafe_allow_html=True)
        p1, p2 = st.columns(2)
        with p1:
            section_title(
                "Συναίσθημα και στάση",
                "Συνδυάζει το αν οι πολίτες γράφουν θετικά/αρνητικά και αν είναι υπέρ ή κατά της πρότασης.",
            )
            st.plotly_chart(proposal_sentiment_stance_fig(proposal_series), use_container_width=True)
        with p2:
            section_title(
                "Ρυθμός αντιδράσεων",
                "Δείχνει πόσες αντιδράσεις μαζεύονται ανά χρονική στιγμή και βοηθά να βρεθούν κορυφώσεις ενδιαφέροντος.",
            )
            st.plotly_chart(proposal_reaction_velocity_fig(proposal_series), use_container_width=True)
        p3, p4 = st.columns(2)
        with p3:
            section_title(
                "Κυρίαρχα θέματα",
                "Δείχνει ποια θέματα εμφανίζονται πιο συχνά στα σχόλια της συγκεκριμένης πρότασης.",
            )
            st.plotly_chart(proposal_topic_fig(proposal_series), use_container_width=True)
        with p4:
            section_title(
                "Ποιότητα επιχειρημάτων",
                "Δείχνει πόσο τεκμηριωμένα είναι τα σχόλια. Υψηλότερες τιμές σημαίνουν πιο αναλυτικές τοποθετήσεις.",
            )
            st.plotly_chart(proposal_quality_fig(proposal_series, advanced=(mode == "advanced")), use_container_width=True)

    st.divider()
    st.subheader("Γραφήματα κάλυψης αρχιτεκτονικής (mockup)")
    arch = pipeline.architecture_metrics()
    a1, a2 = st.columns(2)
    with a1:
        section_title(
            "Αποτελέσματα ανά πράκτορα",
            "Δείχνει τι παράγει κάθε πράκτορας (συναίσθημα, στάση, ειρωνεία, ποιότητα). Με αυτό βλέπεις ότι όλα τα κομμάτια Stage 1 έχουν ορατό output.",
        )
        st.plotly_chart(arch_agent_outputs_fig(arch["agent_outputs"]), use_container_width=True)
    with a2:
        section_title(
            "Βεβαιότητα ανά πράκτορα",
            "Συγκρίνει πόσο σίγουρος είναι κάθε πράκτορας στις εκτιμήσεις του. Βοηθά στον εντοπισμό αβέβαιων περιοχών.",
        )
        st.plotly_chart(arch_agent_confidence_fig(arch["agent_confidence"]), use_container_width=True)
    a3, a4 = st.columns(2)
    with a3:
        section_title(
            "Κατανομή φόρτου: ταξινομητές vs LLM",
            "Δείχνει πόση δουλειά αναλαμβάνουν οι κλασικοί ταξινομητές και πόση τα LLM mockups.",
        )
        st.plotly_chart(arch_classifier_vs_llm_fig(arch["classifier_vs_llm"]), use_container_width=True)
    with a4:
        section_title(
            "Έλεγχοι εγκυρότητας API",
            "Δείχνει πόσα αιτήματα περνούν ή απορρίπτονται από το αρχικό validation στάδιο.",
        )
        st.plotly_chart(arch_api_validation_fig(arch["api_validation"]), use_container_width=True)
    a5, a6 = st.columns(2)
    with a5:
        section_title(
            "Ουρά: βάθος και ρυθμός",
            "Το βάθος δείχνει πόσα περιμένουν στην ουρά, ενώ ο ρυθμός δείχνει πόσα επεξεργάζονται ανά κύκλο.",
        )
        st.plotly_chart(arch_queue_timeline_fig(arch["queue_timeline"]), use_container_width=True)
    with a6:
        section_title(
            "Παράκαμψη αντιδράσεων vs NLP",
            "Συγκρίνει την άμεση ροή αντιδράσεων με τη ροή που περνά από NLP ανάλυση.",
        )
        st.plotly_chart(arch_bypass_vs_nlp_fig(arch["bypass_vs_nlp"]), use_container_width=True)
    a7, a8 = st.columns(2)
    with a7:
        section_title(
            "Όγκος αποθήκευσης",
            "Δείχνει πώς γεμίζουν οι δύο αποθήκες: ανά σχόλιο και ανά συνοπτική πρόταση.",
        )
        st.plotly_chart(arch_store_volume_fig(arch["store_volume"]), use_container_width=True)
    with a8:
        section_title(
            "Φρεσκάδα και καθυστέρηση dashboard",
            "Δείχνει πόσο πρόσφατα είναι τα δεδομένα και πόση καθυστέρηση υπάρχει μέχρι να εμφανιστούν στο dashboard.",
        )
        st.plotly_chart(arch_store_freshness_fig(arch["store_freshness"]), use_container_width=True)
    section_title(
        "Προγραμματισμένα triggers",
        "Δείχνει πόσες φορές θα ενεργοποιούνταν οι αναλύσεις με κανόνες ανά πλήθος σχολίων ή χρονικό διάστημα.",
    )
    st.plotly_chart(arch_scheduler_trigger_fig(arch["scheduler_triggers"]), use_container_width=True)


render_cards()
selected = st.session_state.get("selected_proposal_id")
if selected:
    render_expanded_post(selected)
render_dashboards(selected)
