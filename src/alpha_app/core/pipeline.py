from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import datetime
from itertools import count

from alpha_app.config import MUNICIPALITY_ID, REACTION_KEYS
from alpha_app.core.mock_engine import classify_stage1, validate_event
from alpha_app.core.proposals import PROPOSALS, SEEDED_COMMENTS
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
    def __init__(self, proposals: list[Proposal] | None = None) -> None:
        proposal_list = proposals or PROPOSALS
        self.proposals = {p.proposal_id: p for p in proposal_list}
        self.pending_events: list[CommentEvent] = []
        self.comments: list[CommentEvent] = []
        self.stage1_results: dict[str, Stage1Result] = {}
        self.stage2_insights: dict[str, Stage2Insight] = {}
        self.reaction_totals: dict[str, dict[str, int]] = defaultdict(lambda: {k: 0 for k in REACTION_KEYS})
        self._dirty_proposals: set[str] = set()
        self._id_counter = count(1)

        self.validation_stats = {"pass": 0, "fail": 0}
        self.validation_timeline: list[dict[str, object]] = []
        self.queue_snapshots: list[dict[str, object]] = []
        self.store_snapshots: list[dict[str, object]] = []
        self.scheduler_triggers: list[dict[str, object]] = []
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
            self.stage2_insights[proposal_id] = self._build_insight(proposal_id)
            self._compute_scheduler_for(proposal_id)
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

    def _build_insight(self, proposal_id: str) -> Stage2Insight:
        scoped = [r for r in self.stage1_results.values() if r.proposal_id == proposal_id]
        topic_counter: Counter[str] = Counter()
        for result in scoped:
            topic_counter.update(result.tags)
        top_topics = [topic for topic, _ in topic_counter.most_common(5)] or ["general_feedback"]

        sentiment_counts = Counter(result.sentiment for result in scoped)
        dominant = sentiment_counts.most_common(1)[0][0] if sentiment_counts else "neutral"
        avg_quality = sum(r.argument_quality_score for r in scoped) / len(scoped) if scoped else 0.0

        trend_summary = f"Κυρίαρχο συναίσθημα: {dominant}. Μέση ποιότητα επιχειρημάτων: {avg_quality:.2f}."
        executive_summary = (
            f"Η πρόταση '{self.proposals[proposal_id].title}' συγκεντρώνει {len(scoped)} σχόλια με κύρια θέματα: "
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

        for pid, proposal in self.proposals.items():
            comments = [c for c in self.comments if c.proposal_id == pid]
            results = [self.stage1_results[c.comment_id] for c in comments if c.comment_id in self.stage1_results]
            reactions = self.reaction_totals[pid]
            total_reactions = sum(reactions.values())
            support_ratio = 0.0 if total_reactions == 0 else (reactions["likes"] + reactions["support"]) / total_reactions

            comparison_rows.append({"proposal_id": pid, "title": proposal.title, "comments_total": len(comments), "total_reactions": total_reactions, "support_ratio": round(support_ratio, 2)})

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

        overview = DashboardOverviewSeries(
            proposal_comparison=comparison_rows,
            sentiment_by_proposal=sentiment_rows,
            trend_points=trend_rows,
            service_impact=service_rows,
            insight_line="Overview: highest participation appears in mobility-heavy proposals.",
        )

        scoped_comments = [c for c in self.comments if c.proposal_id == target_id]
        scoped_results = [self.stage1_results[c.comment_id] for c in scoped_comments if c.comment_id in self.stage1_results]
        sentiment_dist = Counter(r.sentiment for r in scoped_results)
        stance_dist = Counter(r.stance for r in scoped_results)
        topic_counter: Counter[str] = Counter()
        for result in scoped_results:
            topic_counter.update(result.tags)

        reaction_velocity = []
        for comment in sorted(scoped_comments, key=lambda c: c.submitted_at):
            reaction_velocity.append({"timestamp": comment.submitted_at.strftime("%Y-%m-%d %H:%M"), "total_reacts": sum(comment.reactions.values())})

        proposal_series = DashboardProposalSeries(
            proposal_id=target_id,
            sentiment_distribution=[{"label": k, "count": v} for k, v in sentiment_dist.items()],
            stance_distribution=[{"label": k, "count": v} for k, v in stance_dist.items()],
            reaction_velocity=reaction_velocity,
            topic_prevalence=[{"topic": k, "count": v} for k, v in topic_counter.most_common(8)],
            argument_quality_distribution=[{"comment_id": r.comment_id, "score": r.argument_quality_score} for r in scoped_results],
            insight_line=("Proposal insight: advanced view enabled." if mode == "advanced" else "Proposal insight: basic KPI view."),
        )
        return overview, proposal_series

    def architecture_metrics(self) -> dict[str, list[dict[str, object]]]:
        results = list(self.stage1_results.values())
        irony_counts = Counter("irony_true" if r.irony_flag else "irony_false" for r in results)
        sentiment_counts = Counter(r.sentiment for r in results)
        stance_counts = Counter(r.stance for r in results)

        agent_outputs = []
        for label, count in sentiment_counts.items():
            agent_outputs.append({"agent": "sentiment", "label": label, "count": count})
        for label, count in stance_counts.items():
            agent_outputs.append({"agent": "stance", "label": label, "count": count})
        for label, count in irony_counts.items():
            agent_outputs.append({"agent": "irony", "label": label, "count": count})
        for r in results:
            agent_outputs.append({"agent": "argument_quality", "label": "score_bin", "count": int(r.argument_quality_score * 10)})

        agent_confidence = []
        for r in results:
            agent_confidence.append({"agent": "sentiment", "value": r.confidence})
            agent_confidence.append({"agent": "stance", "value": max(0.4, r.confidence - 0.05)})
            agent_confidence.append({"agent": "irony", "value": 0.78 if r.irony_flag else 0.62})
            agent_confidence.append({"agent": "argument_quality", "value": r.argument_quality_score})

        classifier_vs_llm = [
            {"family": "classifier", "workload": len(results) * 2, "avg_confidence": round(sum(x["value"] for x in agent_confidence if x["agent"] in {"sentiment", "stance"}) / max(1, len([x for x in agent_confidence if x["agent"] in {"sentiment", "stance"}])), 2)},
            {"family": "llm", "workload": len(results) * 2, "avg_confidence": round(sum(x["value"] for x in agent_confidence if x["agent"] in {"irony", "argument_quality"}) / max(1, len([x for x in agent_confidence if x["agent"] in {"irony", "argument_quality"}])), 2)},
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

