from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import datetime
from itertools import count
from pathlib import Path

from alpha_app.config import MUNICIPALITY_ID, REACTION_KEYS
from alpha_app.core.artifacts import PipelineArtifacts
from alpha_app.core.mock_engine import classify_stage1, validate_event
from alpha_app.core.proposals import PROPOSALS, SEEDED_COMMENTS
from alpha_app.core.review import apply_mock_reviewer_pass
from alpha_app.domain.models import (
    CommentEvent,
    DashboardOverviewSeries,
    DashboardProposalSeries,
    Proposal,
    ProposalCardViewModel,
    ProposalExpandedViewModel,
    Stage1Result,
    Stage2Insight,
)


class AlphaPipeline:
    def __init__(
        self,
        proposals: list[Proposal] | None = None,
        *,
        emit_artifacts: bool = False,
        artifact_root: Path | str | None = None,
        run_id: str | None = None,
    ) -> None:
        proposal_list = proposals or PROPOSALS
        self.proposals = {p.proposal_id: p for p in proposal_list}
        self.pending_events: list[CommentEvent] = []
        self.comments: list[CommentEvent] = []
        self.stage1_results: dict[str, Stage1Result] = {}
        self.stage2_insights: dict[str, Stage2Insight] = {}
        self.review_initial_rows: dict[str, list[dict[str, object]]] = {}
        self.review_final_rows: dict[str, list[dict[str, object]]] = {}
        self.review_corrections: dict[str, list[dict[str, object]]] = {}
        self.review_metrics: dict[str, dict[str, object]] = {}
        self.reaction_totals: dict[str, dict[str, int]] = defaultdict(lambda: {k: 0 for k in REACTION_KEYS})
        self._dirty_proposals: set[str] = set()
        self._id_counter = count(1)

        self.validation_stats = {"pass": 0, "fail": 0}
        self.validation_timeline: list[dict[str, object]] = []
        self.queue_snapshots: list[dict[str, object]] = []
        self.store_snapshots: list[dict[str, object]] = []
        self.scheduler_triggers: list[dict[str, object]] = []
        self._artifact_store = PipelineArtifacts(root=artifact_root, run_id=run_id) if emit_artifacts else None
        self.seed_demo_data()

    def _snapshot_queue(self, processed_in_batch: int = 0) -> None:
        self.queue_snapshots.append(
            {
                "timestamp": datetime.utcnow().isoformat(timespec="seconds"),
                "depth": len(self.pending_events),
                "throughput": processed_in_batch,
            }
        )

    def _snapshot_store(self) -> None:
        self.store_snapshots.append(
            {
                "timestamp": datetime.utcnow().isoformat(timespec="seconds"),
                "stage1_count": len(self.stage1_results),
                "stage2_count": len(self.stage2_insights),
            }
        )

    def submit_comment(
        self,
        proposal_id: str,
        comment_text: str,
        reactions: dict[str, int] | None = None,
        *,
        author_name: str = "Κάτοικος",
        comment_id: str | None = None,
        submitted_at: datetime | None = None,
    ) -> CommentEvent:
        normalized_reactions = {k: max(0, int((reactions or {}).get(k, 0))) for k in REACTION_KEYS}
        event = CommentEvent(
            municipality_id=MUNICIPALITY_ID,
            proposal_id=proposal_id,
            comment_id=comment_id or f"c_{next(self._id_counter):04d}",
            author_name=author_name,
            comment_text=comment_text,
            reactions=normalized_reactions,
            submitted_at=submitted_at or datetime.utcnow(),
        )
        try:
            validate_event(event, set(self.proposals))
            self.validation_stats["pass"] += 1
            self.validation_timeline.append({"timestamp": datetime.utcnow().isoformat(timespec="seconds"), "outcome": "pass"})
        except ValueError:
            self.validation_stats["fail"] += 1
            self.validation_timeline.append({"timestamp": datetime.utcnow().isoformat(timespec="seconds"), "outcome": "fail"})
            raise

        self.pending_events.append(event)
        self.comments.append(event)
        for key, value in normalized_reactions.items():
            self.reaction_totals[proposal_id][key] += value
        self._dirty_proposals.add(proposal_id)
        self._snapshot_queue(processed_in_batch=0)
        self._emit_ingestion_artifacts(proposal_id)
        return event

    def seed_demo_data(self) -> None:
        if self.comments:
            return
        for proposal_id, entries in SEEDED_COMMENTS.items():
            for entry in entries:
                self.submit_comment(
                    proposal_id=proposal_id,
                    comment_text=str(entry["text"]),
                    reactions=dict(entry["reactions"]),
                    author_name=str(entry["author"]),
                    submitted_at=entry["submitted_at"],  # type: ignore[arg-type]
                )
        for proposal_id in self.proposals:
            self._ensure_fresh(proposal_id)
        self._snapshot_store()

    def _compute_scheduler_for(self, proposal_id: str) -> None:
        comments = [c for c in self.comments if c.proposal_id == proposal_id]
        n_comment_triggers = len(comments) // 3
        interval_triggers = len({c.submitted_at.strftime("%Y-%m-%d") for c in comments})
        self.scheduler_triggers = [r for r in self.scheduler_triggers if r["proposal_id"] != proposal_id]
        self.scheduler_triggers.append({"proposal_id": proposal_id, "rule": "N_comments", "count": n_comment_triggers})
        self.scheduler_triggers.append({"proposal_id": proposal_id, "rule": "time_interval", "count": interval_triggers})

    def _ensure_fresh(self, proposal_id: str) -> None:
        if proposal_id not in self.stage2_insights or proposal_id in self._dirty_proposals:
            processed = self._process_pending_for_proposal(proposal_id)
            comments = [comment for comment in self.comments if comment.proposal_id == proposal_id]
            by_id = {result.comment_id: result for result in self.stage1_results.values() if result.proposal_id == proposal_id}
            ordered_results = [by_id[comment.comment_id] for comment in comments if comment.comment_id in by_id]
            initial_rows, final_rows, corrections, metrics = apply_mock_reviewer_pass(proposal_id, comments, ordered_results)
            self.review_initial_rows[proposal_id] = initial_rows
            self.review_final_rows[proposal_id] = final_rows
            self.review_corrections[proposal_id] = corrections
            self.review_metrics[proposal_id] = metrics
            self.stage2_insights[proposal_id] = self._build_insight(proposal_id, reviewed_rows=final_rows)
            self._compute_scheduler_for(proposal_id)
            self._emit_analysis_artifacts(proposal_id)
            self._dirty_proposals.discard(proposal_id)
            self._snapshot_queue(processed_in_batch=processed)
            self._snapshot_store()

    def _process_pending_for_proposal(self, proposal_id: str) -> int:
        keep: list[CommentEvent] = []
        batch: list[CommentEvent] = []
        for event in self.pending_events:
            if event.proposal_id == proposal_id:
                batch.append(event)
            else:
                keep.append(event)
        self.pending_events = keep

        for event in batch:
            result = classify_stage1(event)
            self.stage1_results[event.comment_id] = result
        return len(batch)

    def _build_insight(self, proposal_id: str, *, reviewed_rows: list[dict[str, object]]) -> Stage2Insight:
        topic_counter: Counter[str] = Counter(
            str(row["topic_context"]) for row in reviewed_rows if row.get("topic_context") and row["topic_context"] != "other"
        )
        top_topics = [topic for topic, _ in topic_counter.most_common(5)] or ["general_feedback"]

        sentiment_counts = Counter(str(row.get("sentiment", "neutral")) for row in reviewed_rows)
        dominant = sentiment_counts.most_common(1)[0][0] if sentiment_counts else "neutral"
        avg_quality = (
            sum(float(row.get("argument_quality_score", 0.0)) for row in reviewed_rows) / len(reviewed_rows)
            if reviewed_rows
            else 0.0
        )

        trend_summary = f"Dominant sentiment: {dominant}. Average argument quality: {avg_quality:.2f}."
        executive_summary = (
            f"Proposal '{self.proposals[proposal_id].title}' includes {len(reviewed_rows)} reviewed comments with top topics: "
            f"{', '.join(top_topics)}."
        )
        return Stage2Insight(
            municipality_id=MUNICIPALITY_ID,
            proposal_id=proposal_id,
            topics=top_topics,
            trend_summary=trend_summary,
            executive_summary=executive_summary,
            generated_at=datetime.utcnow(),
        )

    def open_card(self, proposal_id: str) -> ProposalExpandedViewModel:
        self._ensure_fresh(proposal_id)
        proposal = self.proposals[proposal_id]
        comments = sorted([c for c in self.comments if c.proposal_id == proposal_id], key=lambda c: c.submitted_at, reverse=True)
        stage1 = [self.stage1_results[c.comment_id] for c in comments if c.comment_id in self.stage1_results]
        insight = self.stage2_insights[proposal_id]
        return ProposalExpandedViewModel(proposal=proposal, comments=comments, reactions=self.reaction_totals[proposal_id], stage1_results=stage1, insight=insight)

    def get_card_summaries(self) -> list[ProposalCardViewModel]:
        cards: list[ProposalCardViewModel] = []
        for proposal_id, proposal in self.proposals.items():
            self._ensure_fresh(proposal_id)
            comments = [c for c in self.comments if c.proposal_id == proposal_id]
            reactions = self.reaction_totals[proposal_id]
            total_reactions = sum(reactions.values())
            support_ratio = 0.0 if total_reactions == 0 else round((reactions["likes"] + reactions["support"]) / total_reactions, 2)
            cards.append(
                ProposalCardViewModel(
                    proposal_id=proposal_id,
                    title=proposal.title,
                    status=proposal.status,
                    short_description=proposal.short_description,
                    image_url=proposal.image_url,
                    comments_total=len(comments),
                    total_reactions=total_reactions,
                    support_ratio=support_ratio,
                )
            )
        return cards

    def build_dashboard_data(
        self,
        mode: str = "basic",
        proposal_id: str | None = None,
        service_filter: list[str] | None = None,
    ) -> tuple[DashboardOverviewSeries, DashboardProposalSeries]:
        for pid in self.proposals:
            self._ensure_fresh(pid)

        target_id = proposal_id or next(iter(self.proposals))
        service_filter = service_filter or []

        comparison_rows: list[dict[str, object]] = []
        sentiment_rows: list[dict[str, object]] = []
        trend_rows: list[dict[str, object]] = []
        service_rows: list[dict[str, object]] = []
        quality_rows: list[dict[str, object]] = []

        for pid, proposal in self.proposals.items():
            comments = [c for c in self.comments if c.proposal_id == pid]
            results = [self.stage1_results[c.comment_id] for c in comments if c.comment_id in self.stage1_results]
            reviewed = self.review_final_rows.get(pid, [])
            reactions = self.reaction_totals[pid]
            total_reactions = sum(reactions.values())
            support_ratio = 0.0 if total_reactions == 0 else (reactions["likes"] + reactions["support"]) / total_reactions

            comparison_rows.append({"proposal_id": pid, "title": proposal.title, "comments_total": len(comments), "total_reactions": total_reactions, "support_ratio": round(support_ratio, 2)})

            if reviewed:
                sentiment_counts = Counter(str(row.get("sentiment", "neutral")) for row in reviewed)
            else:
                sentiment_counts = Counter(r.sentiment for r in results)
            for label in ["positive", "neutral", "negative"]:
                sentiment_rows.append({"title": proposal.title, "sentiment": label, "count": sentiment_counts.get(label, 0)})

            by_day: dict[str, int] = defaultdict(int)
            for comment in comments:
                day = comment.submitted_at.strftime("%Y-%m-%d")
                by_day[day] += 1
            for day, count in sorted(by_day.items()):
                trend_rows.append({"date": day, "title": proposal.title, "comments": count})

            for service in proposal.affected_services:
                if service_filter and service not in service_filter:
                    continue
                service_rows.append({"service": service, "title": proposal.title, "impact": len(comments)})
            quality_metric = self.review_metrics.get(pid, {})
            if quality_metric:
                quality_rows.append(
                    {
                        "proposal_id": pid,
                        "title": proposal.title,
                        "correction_rate": float(quality_metric.get("correction_rate", 0.0)),
                        "unresolved_rate": float(quality_metric.get("unresolved_rate", 0.0)),
                        "avg_review_lag_sec": float(quality_metric.get("avg_review_lag_sec", 0.0)),
                    }
                )

        overview = DashboardOverviewSeries(
            proposal_comparison=comparison_rows,
            sentiment_by_proposal=sentiment_rows,
            trend_points=trend_rows,
            service_impact=service_rows,
            quality_telemetry=quality_rows,
            insight_line="Overview: highest participation appears in mobility-heavy proposals.",
        )

        scoped_comments = [c for c in self.comments if c.proposal_id == target_id]
        scoped_results = [self.stage1_results[c.comment_id] for c in scoped_comments if c.comment_id in self.stage1_results]
        reviewed_target = self.review_final_rows.get(target_id, [])
        sentiment_dist = Counter(str(row.get("sentiment", "neutral")) for row in reviewed_target) if reviewed_target else Counter(r.sentiment for r in scoped_results)
        stance_dist = Counter(r.stance for r in scoped_results)
        topic_counter: Counter[str] = Counter()
        if reviewed_target:
            for row in reviewed_target:
                topic = str(row.get("topic_context", ""))
                if topic and topic != "other":
                    topic_counter.update([topic])
        else:
            for result in scoped_results:
                topic_counter.update(result.tags)

        reaction_velocity = []
        for comment in sorted(scoped_comments, key=lambda c: c.submitted_at):
            reaction_velocity.append({"timestamp": comment.submitted_at.strftime("%Y-%m-%d %H:%M"), "total_reacts": sum(comment.reactions.values())})

        metrics = self.review_metrics.get(target_id, {})
        indicator_rates = metrics.get("indicator_rates", {}) if isinstance(metrics, dict) else {}
        correction_by_indicator = [{"indicator": str(k), "correction_rate": float(v)} for k, v in dict(indicator_rates).items()]
        review_state_mix = []
        if metrics:
            review_state_mix = [
                {"state": "corrected", "count": int(metrics.get("corrected_items", 0))},
                {"state": "unchanged", "count": int(metrics.get("unchanged_items", 0))},
                {"state": "unresolved", "count": int(metrics.get("unresolved_items", 0))},
            ]
        review_lag_points = [{"comment_id": str(row.get("comment_id", "")), "lag_sec": float(row.get("review_lag_sec", 0.0))} for row in reviewed_target]

        proposal_series = DashboardProposalSeries(
            proposal_id=target_id,
            sentiment_distribution=[{"label": k, "count": v} for k, v in sentiment_dist.items()],
            stance_distribution=[{"label": k, "count": v} for k, v in stance_dist.items()],
            reaction_velocity=reaction_velocity,
            topic_prevalence=[{"topic": k, "count": v} for k, v in topic_counter.most_common(8)],
            argument_quality_distribution=[{"comment_id": r.comment_id, "score": r.argument_quality_score} for r in scoped_results],
            correction_by_indicator=correction_by_indicator,
            review_state_mix=review_state_mix,
            review_lag_points=review_lag_points,
            insight_line=("Proposal insight: advanced view enabled." if mode == "advanced" else "Proposal insight: basic KPI view."),
        )
        self._emit_visual_artifacts(target_id, mode=mode, overview=overview, proposal=proposal_series)
        return overview, proposal_series

    def architecture_metrics(self) -> dict[str, list[dict[str, object]]]:
        results = list(self.stage1_results.values())
        label_counts: Counter[tuple[str, str]] = Counter()
        agent_confidence: list[dict[str, object]] = []

        for result in results:
            if result.agent_labels:
                for agent, label in result.agent_labels.items():
                    label_counts[(agent, str(label))] += 1
            else:
                label_counts[("sentiment", result.sentiment)] += 1
                label_counts[("stance", result.stance)] += 1
                label_counts[("irony", "ironic" if result.irony_flag else "non_ironic")] += 1
                label_counts[("argument_quality", f"bin_{int(result.argument_quality_score * 10)}")] += 1

            if result.agent_scores:
                for agent, value in result.agent_scores.items():
                    agent_confidence.append({"agent": agent, "value": float(value)})
            else:
                agent_confidence.append({"agent": "sentiment", "value": result.confidence})
                agent_confidence.append({"agent": "stance", "value": max(0.4, result.confidence - 0.05)})
                agent_confidence.append({"agent": "irony", "value": 0.78 if result.irony_flag else 0.62})
                agent_confidence.append({"agent": "argument_quality", "value": result.argument_quality_score})

        agent_outputs = [{"agent": agent, "label": label, "count": count} for (agent, label), count in sorted(label_counts.items())]

        classifier_agents = {"sentiment", "stance", "profanity", "toxicity", "relevance"}
        llm_agents = {"irony", "argument_quality", "civility", "structure", "evidence"}
        classifier_values = [float(x["value"]) for x in agent_confidence if str(x["agent"]) in classifier_agents]
        llm_values = [float(x["value"]) for x in agent_confidence if str(x["agent"]) in llm_agents]

        classifier_vs_llm = [
            {
                "family": "classifier",
                "workload": len(classifier_values),
                "avg_confidence": round(sum(classifier_values) / max(1, len(classifier_values)), 2),
            },
            {
                "family": "llm",
                "workload": len(llm_values),
                "avg_confidence": round(sum(llm_values) / max(1, len(llm_values)), 2),
            },
        ]

        bypass_vs_nlp = []
        cumulative_comments = 0
        for idx, snap in enumerate(self.store_snapshots):
            cumulative_comments = min(len(self.comments), cumulative_comments + 1)
            bypass_vs_nlp.append(
                {
                    "timestamp": snap["timestamp"],
                    "reaction_bypass_events": cumulative_comments,
                    "nlp_events": min(len(results), (idx + 1)),
                }
            )

        freshness_rows = []
        now = datetime.utcnow()
        for pid, insight in self.stage2_insights.items():
            proposal_comments = [c for c in self.comments if c.proposal_id == pid]
            if proposal_comments:
                latest_comment = max(proposal_comments, key=lambda c: c.submitted_at).submitted_at
                pipeline_lag = max(0.0, (insight.generated_at - latest_comment).total_seconds())
            else:
                pipeline_lag = 0.0
            freshness_rows.append(
                {
                    "proposal_id": pid,
                    "freshness_age_sec": max(0.0, (now - insight.generated_at).total_seconds()),
                    "pipeline_lag_sec": pipeline_lag,
                }
            )

        return {
            "agent_outputs": agent_outputs,
            "agent_confidence": agent_confidence,
            "classifier_vs_llm": classifier_vs_llm,
            "api_validation": [{"outcome": "pass", "count": self.validation_stats["pass"]}, {"outcome": "fail", "count": self.validation_stats["fail"]}],
            "queue_timeline": self.queue_snapshots,
            "bypass_vs_nlp": bypass_vs_nlp,
            "store_volume": self.store_snapshots,
            "store_freshness": freshness_rows,
            "scheduler_triggers": self.scheduler_triggers,
        }

    def comments_for_proposal(self, proposal_id: str) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        by_comment = {r.comment_id: r for r in self.stage1_results.values() if r.proposal_id == proposal_id}
        for comment in sorted([c for c in self.comments if c.proposal_id == proposal_id], key=lambda c: c.submitted_at, reverse=True):
            result = by_comment.get(comment.comment_id)
            rows.append(
                {
                    "author_name": comment.author_name,
                    "submitted_at": comment.submitted_at.strftime("%Y-%m-%d %H:%M"),
                    "comment_text": comment.comment_text,
                    "reactions_total": sum(comment.reactions.values()),
                    "sentiment": result.sentiment if result else "neutral",
                    "stance": result.stance if result else "neutral",
                    "quality": result.argument_quality_score if result else 0.0,
                }
            )
        return rows

    def dashboard_payload(self, mode: str = "basic") -> dict[str, object]:
        overview, proposal_series = self.build_dashboard_data(mode=mode)
        return {"overview": asdict(overview), "proposal": asdict(proposal_series)}

    @property
    def artifact_run_id(self) -> str | None:
        if not self._artifact_store:
            return None
        return self._artifact_store.run_id

    @property
    def artifact_root(self) -> str | None:
        if not self._artifact_store:
            return None
        return str(self._artifact_store.root)

    def validate_artifact_contract(self, proposal_id: str) -> list[str]:
        if not self._artifact_store:
            return []
        return self._artifact_store.missing_contract_files(proposal_id)

    def read_analysis_initial_from_artifacts(self, proposal_id: str) -> list[dict[str, object]]:
        if not self._artifact_store:
            return []
        return self._artifact_store.read_json(proposal_id, "analysis/initial/stage1_results.json")

    def read_analysis_final_from_artifacts(self, proposal_id: str) -> list[dict[str, object]]:
        if not self._artifact_store:
            return []
        return self._artifact_store.read_json(proposal_id, "analysis/final/stage1_results.json")

    def read_corrections_from_artifacts(self, proposal_id: str) -> list[dict[str, object]]:
        if not self._artifact_store:
            return []
        return self._artifact_store.read_json(proposal_id, "analysis/final/corrections.json")

    def read_review_metrics_from_artifacts(self, proposal_id: str) -> dict[str, object]:
        if not self._artifact_store:
            return {}
        return self._artifact_store.read_json(proposal_id, "analysis/final/review_metrics.json")

    def read_visual_payload_from_artifacts(self, proposal_id: str, *, mode: str = "basic") -> dict[str, object]:
        if not self._artifact_store:
            return {}
        return self._artifact_store.read_json(proposal_id, f"analysis/visuals/dashboard_{mode}.json")

    def _emit_ingestion_artifacts(self, proposal_id: str) -> None:
        if not self._artifact_store:
            return
        comments = [comment for comment in self.comments if comment.proposal_id == proposal_id]
        self._artifact_store.write_ingestion_artifacts(proposal_id, comments)

    def _emit_analysis_artifacts(self, proposal_id: str) -> None:
        if not self._artifact_store:
            return
        initial_rows = self.review_initial_rows.get(proposal_id, [])
        final_rows = self.review_final_rows.get(proposal_id, [])
        corrections = self.review_corrections.get(proposal_id, [])
        review_metrics = self.review_metrics.get(proposal_id, {})
        insight = self.stage2_insights[proposal_id]
        self._artifact_store.write_analysis_artifacts(
            proposal_id,
            initial_rows=initial_rows,
            final_rows=final_rows,
            corrections=corrections,
            review_metrics=review_metrics,
            insight=insight,
        )

    def _emit_visual_artifacts(
        self,
        proposal_id: str,
        *,
        mode: str,
        overview: DashboardOverviewSeries,
        proposal: DashboardProposalSeries,
    ) -> None:
        if not self._artifact_store:
            return
        self._artifact_store.write_visual_payload(
            proposal_id,
            mode=mode,
            overview=overview,
            proposal=proposal,
        )



