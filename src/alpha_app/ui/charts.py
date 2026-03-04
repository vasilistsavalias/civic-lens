from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from alpha_app.domain.models import DashboardOverviewSeries, DashboardProposalSeries


def overview_comparison_fig(series: DashboardOverviewSeries) -> go.Figure:
    df = pd.DataFrame(series.proposal_comparison)
    if df.empty:
        return go.Figure()
    melted = df.melt(
        id_vars=["title"],
        value_vars=["comments_total", "total_reactions", "support_ratio"],
        var_name="metric",
        value_name="value",
    )
    return px.bar(
        melted,
        x="title",
        y="value",
        color="metric",
        barmode="group",
        title="Σύγκριση προτάσεων",
        labels={"title": "Πρόταση", "value": "Τιμή", "metric": "Μετρική"},
    )


def overview_sentiment_fig(series: DashboardOverviewSeries) -> go.Figure:
    df = pd.DataFrame(series.sentiment_by_proposal)
    if df.empty:
        return go.Figure()
    return px.bar(
        df,
        x="title",
        y="count",
        color="sentiment",
        barmode="stack",
        title="Συναίσθημα ανά πρόταση",
        labels={"title": "Πρόταση", "count": "Πλήθος σχολίων", "sentiment": "Συναίσθημα"},
    )


def overview_trend_fig(series: DashboardOverviewSeries) -> go.Figure:
    df = pd.DataFrame(series.trend_points)
    if df.empty:
        return go.Figure()
    return px.line(
        df,
        x="date",
        y="comments",
        color="title",
        markers=True,
        title="Εξέλιξη σχολίων στον χρόνο",
        labels={"date": "Ημερομηνία", "comments": "Πλήθος σχολίων", "title": "Πρόταση"},
    )


def overview_service_fig(series: DashboardOverviewSeries) -> go.Figure:
    df = pd.DataFrame(series.service_impact)
    if df.empty:
        return go.Figure()
    return px.bar(
        df,
        x="service",
        y="impact",
        color="title",
        barmode="group",
        title="Επίδραση ανά υπηρεσία",
        labels={"service": "Υπηρεσία", "impact": "Επηρεαζόμενα σχόλια", "title": "Πρόταση"},
    )


def proposal_sentiment_stance_fig(series: DashboardProposalSeries) -> go.Figure:
    sdf = pd.DataFrame(series.sentiment_distribution)
    tdf = pd.DataFrame(series.stance_distribution)
    fig = go.Figure()
    if not sdf.empty:
        fig.add_bar(name="Sentiment", x=sdf["label"], y=sdf["count"])
    if not tdf.empty:
        fig.add_bar(name="Stance", x=tdf["label"], y=tdf["count"])
    fig.update_layout(barmode="group", title="Κατανομή συναισθήματος και στάσης", xaxis_title="Κατηγορία", yaxis_title="Πλήθος")
    return fig


def proposal_reaction_velocity_fig(series: DashboardProposalSeries) -> go.Figure:
    df = pd.DataFrame(series.reaction_velocity)
    if df.empty:
        return go.Figure()
    return px.bar(
        df,
        x="timestamp",
        y="total_reacts",
        title="Ρυθμός αντιδράσεων στον χρόνο",
        labels={"timestamp": "Χρόνος", "total_reacts": "Σύνολο αντιδράσεων"},
    )


def proposal_topic_fig(series: DashboardProposalSeries) -> go.Figure:
    df = pd.DataFrame(series.topic_prevalence)
    if df.empty:
        return go.Figure()
    return px.bar(df, x="topic", y="count", title="Κυρίαρχα θέματα", labels={"topic": "Θέμα", "count": "Πλήθος"})


def proposal_quality_fig(series: DashboardProposalSeries, advanced: bool) -> go.Figure:
    df = pd.DataFrame(series.argument_quality_distribution)
    if df.empty:
        return go.Figure()
    if advanced:
        return px.violin(df, y="score", box=True, points="all", title="Κατανομή ποιότητας επιχειρημάτων (προχωρημένο)", labels={"score": "Βαθμολογία"})
    return px.box(df, y="score", points="all", title="Κατανομή ποιότητας επιχειρημάτων", labels={"score": "Βαθμολογία"})


def arch_agent_outputs_fig(rows: list[dict[str, object]]) -> go.Figure:
    df = pd.DataFrame(rows)
    if df.empty:
        return go.Figure()
    return px.bar(df, x="agent", y="count", color="label", barmode="group", title="Αποτελέσματα ανά πράκτορα", labels={"agent": "Πράκτορας", "count": "Πλήθος", "label": "Κατηγορία"})


def arch_agent_confidence_fig(rows: list[dict[str, object]]) -> go.Figure:
    df = pd.DataFrame(rows)
    if df.empty:
        return go.Figure()
    return px.box(df, x="agent", y="value", points="all", title="Βαθμός βεβαιότητας ανά πράκτορα", labels={"agent": "Πράκτορας", "value": "Βεβαιότητα"})


def arch_classifier_vs_llm_fig(rows: list[dict[str, object]]) -> go.Figure:
    df = pd.DataFrame(rows)
    if df.empty:
        return go.Figure()
    return px.bar(df, x="family", y="workload", color="family", title="Κατανομή φόρτου: ταξινομητές vs LLM", labels={"family": "Οικογένεια", "workload": "Φόρτος"})


def arch_api_validation_fig(rows: list[dict[str, object]]) -> go.Figure:
    df = pd.DataFrame(rows)
    if df.empty:
        return go.Figure()
    return px.pie(df, names="outcome", values="count", title="Αποτελέσματα ελέγχου API")


def arch_queue_timeline_fig(rows: list[dict[str, object]]) -> go.Figure:
    df = pd.DataFrame(rows)
    if df.empty:
        return go.Figure()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["timestamp"], y=df["depth"], mode="lines+markers", name="Queue Depth"))
    fig.add_trace(go.Bar(x=df["timestamp"], y=df["throughput"], name="Throughput"))
    fig.update_layout(title="Ουρά: βάθος και ρυθμός επεξεργασίας", xaxis_title="Χρόνος", yaxis_title="Πλήθος")
    return fig


def arch_bypass_vs_nlp_fig(rows: list[dict[str, object]]) -> go.Figure:
    df = pd.DataFrame(rows)
    if df.empty:
        return go.Figure()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["timestamp"], y=df["reaction_bypass_events"], mode="lines+markers", name="Reaction Bypass"))
    fig.add_trace(go.Scatter(x=df["timestamp"], y=df["nlp_events"], mode="lines+markers", name="NLP Pipeline"))
    fig.update_layout(title="Παράκαμψη αντιδράσεων vs NLP διαδρομή", xaxis_title="Χρόνος", yaxis_title="Πλήθος")
    return fig


def arch_store_volume_fig(rows: list[dict[str, object]]) -> go.Figure:
    df = pd.DataFrame(rows)
    if df.empty:
        return go.Figure()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["timestamp"], y=df["stage1_count"], mode="lines+markers", name="Per-Comment Store"))
    fig.add_trace(go.Scatter(x=df["timestamp"], y=df["stage2_count"], mode="lines+markers", name="Dashboard Store"))
    fig.update_layout(title="Όγκος αποθήκευσης στον χρόνο", xaxis_title="Χρόνος", yaxis_title="Πλήθος εγγραφών")
    return fig


def arch_store_freshness_fig(rows: list[dict[str, object]]) -> go.Figure:
    df = pd.DataFrame(rows)
    if df.empty:
        return go.Figure()
    melted = df.melt(id_vars=["proposal_id"], value_vars=["freshness_age_sec", "pipeline_lag_sec"], var_name="metric", value_name="seconds")
    return px.bar(
        melted,
        x="proposal_id",
        y="seconds",
        color="metric",
        barmode="group",
        title="Φρεσκάδα και καθυστέρηση δεδομένων dashboard",
        labels={"proposal_id": "Πρόταση", "seconds": "Δευτερόλεπτα", "metric": "Μετρική"},
    )


def arch_scheduler_trigger_fig(rows: list[dict[str, object]]) -> go.Figure:
    df = pd.DataFrame(rows)
    if df.empty:
        return go.Figure()
    return px.bar(
        df,
        x="proposal_id",
        y="count",
        color="rule",
        barmode="group",
        title="Προγραμματισμένα triggers (mockup)",
        labels={"proposal_id": "Πρόταση", "count": "Πλήθος triggers", "rule": "Κανόνας"},
    )


def overview_quality_fig(series: DashboardOverviewSeries) -> go.Figure:
    df = pd.DataFrame(series.quality_telemetry)
    if df.empty:
        return go.Figure()
    melted = df.melt(
        id_vars=["title"],
        value_vars=["correction_rate", "unresolved_rate"],
        var_name="metric",
        value_name="value",
    )
    return px.bar(
        melted,
        x="title",
        y="value",
        color="metric",
        barmode="group",
        title="Review quality metrics per proposal",
        labels={"title": "Proposal", "value": "Rate", "metric": "Metric"},
    )


def proposal_correction_rates_fig(series: DashboardProposalSeries) -> go.Figure:
    df = pd.DataFrame(series.correction_by_indicator)
    if df.empty:
        return go.Figure()
    return px.bar(
        df,
        x="indicator",
        y="correction_rate",
        title="Correction rate by indicator",
        labels={"indicator": "Indicator", "correction_rate": "Correction Rate"},
    )


def proposal_review_state_mix_fig(series: DashboardProposalSeries) -> go.Figure:
    df = pd.DataFrame(series.review_state_mix)
    if df.empty:
        return go.Figure()
    return px.pie(df, names="state", values="count", title="Review state mix")


def proposal_review_lag_fig(series: DashboardProposalSeries) -> go.Figure:
    df = pd.DataFrame(series.review_lag_points)
    if df.empty:
        return go.Figure()
    return px.bar(
        df,
        x="comment_id",
        y="lag_sec",
        title="Review lag per comment",
        labels={"comment_id": "Comment", "lag_sec": "Lag (sec)"},
    )


