from __future__ import annotations

import math
import random
from collections import Counter, defaultdict
from dataclasses import asdict, replace
from datetime import datetime, timedelta
from itertools import count
from pathlib import Path

from alpha_app.config import (
    FEED_PAGE_SIZE,
    LEGACY_REACTION_KEY_MAP,
    MOST_RELEVANT_WEIGHTS_V1,
    MUNICIPALITY_ID,
    MAX_THREAD_DEPTH,
    REACTION_KEYS,
    REACTION_WEIGHTS_V1,
)
from alpha_app.core.artifacts import PipelineArtifacts
from alpha_app.core.calibration import brier_proxy, calibrate_scores, ece_proxy, mean_entropy
from alpha_app.core.mock_engine import classify_stage1, validate_event
from alpha_app.core.proposals import PROPOSALS
from alpha_app.core.review import apply_mock_reviewer_pass
from alpha_app.domain.models import (
    CommentEvent,
    DashboardOverviewSeries,
    DashboardProposalSeries,
    DiscussionSort,
    ModerationAction,
    ModerationStatus,
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
        top_level_per_proposal: int = 100,
        seed: int = 2026,
    ) -> None:
        proposal_list = proposals or PROPOSALS
        self.proposals = {p.proposal_id: p for p in proposal_list}
        self.pending_events: list[CommentEvent] = []
        self.comments: list[CommentEvent] = []
        self.comment_index: dict[str, CommentEvent] = {}
        self.children_by_parent: dict[str, list[str]] = defaultdict(list)
        self.stage1_results: dict[str, Stage1Result] = {}
        self.stage2_insights: dict[str, Stage2Insight] = {}
        self.review_initial_rows: dict[str, list[dict[str, object]]] = {}
        self.review_final_rows: dict[str, list[dict[str, object]]] = {}
        self.review_corrections: dict[str, list[dict[str, object]]] = {}
        self.review_metrics: dict[str, dict[str, object]] = {}
        self.reaction_totals: dict[str, dict[str, int]] = defaultdict(lambda: {k: 0 for k in REACTION_KEYS})
        self.moderation_state: dict[str, dict[str, object]] = {}
        self._moderation_events: dict[str, list[dict[str, object]]] = defaultdict(list)
        self._dirty_proposals: set[str] = set()
        self._id_counter = count(1)

        self.validation_stats = {"pass": 0, "fail": 0}
        self.validation_timeline: list[dict[str, object]] = []
        self.queue_snapshots: list[dict[str, object]] = []
        self.store_snapshots: list[dict[str, object]] = []
        self.scheduler_triggers: list[dict[str, object]] = []
        self._top_level_per_proposal = max(1, int(top_level_per_proposal))
        self._seed = int(seed)
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

    def _normalize_reactions(self, reactions: dict[str, int] | None) -> dict[str, int]:
        normalized = {k: 0 for k in REACTION_KEYS}
        for key, value in (reactions or {}).items():
            canonical = key
            if canonical not in REACTION_KEYS:
                canonical = LEGACY_REACTION_KEY_MAP.get(canonical, canonical)
            if canonical in REACTION_KEYS:
                normalized[canonical] += max(0, int(value))
        return normalized

    def _reaction_scores(self, reactions: dict[str, int]) -> tuple[int, float, float]:
        total_reacts = sum(reactions.values())
        signed_raw = 0.0
        for key, count in reactions.items():
            signed_raw += REACTION_WEIGHTS_V1.get(key, 0.0) * float(count)
        signed_norm = math.tanh(signed_raw / max(1.0, float(total_reacts)))
        return total_reacts, round(signed_raw, 3), round(signed_norm, 3)

    def submit_comment(
        self,
        proposal_id: str,
        comment_text: str,
        reactions: dict[str, int] | None = None,
        *,
        author_name: str = "Resident",
        comment_id: str | None = None,
        submitted_at: datetime | None = None,
        parent_comment_id: str | None = None,
        thread_depth: int | None = None,
    ) -> CommentEvent:
        normalized_reactions = self._normalize_reactions(reactions)

        if parent_comment_id is not None:
            parent = self.comment_index.get(parent_comment_id)
            if parent is None:
                raise ValueError(f"Unknown parent_comment_id: {parent_comment_id}")
            inferred_depth = parent.thread_depth + 1
            if thread_depth is None:
                thread_depth = inferred_depth
            elif thread_depth != inferred_depth:
                raise ValueError("thread_depth must equal parent.thread_depth + 1")
        else:
            thread_depth = 0 if thread_depth is None else thread_depth

        event = CommentEvent(
            municipality_id=MUNICIPALITY_ID,
            proposal_id=proposal_id,
            comment_id=comment_id or f"c_{next(self._id_counter):05d}",
            author_name=author_name,
            comment_text=comment_text,
            reactions=normalized_reactions,
            submitted_at=submitted_at or datetime.utcnow(),
            parent_comment_id=parent_comment_id,
            thread_depth=thread_depth,
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
        self.comment_index[event.comment_id] = event
        if parent_comment_id is not None:
            self.children_by_parent[parent_comment_id].append(event.comment_id)
        for key, value in normalized_reactions.items():
            self.reaction_totals[proposal_id][key] += value
        self.moderation_state[event.comment_id] = {
            "moderation_status": "none",
            "moderation_reason": None,
            "moderated_by": None,
            "moderated_at": None,
        }
        self._dirty_proposals.add(proposal_id)
        self._snapshot_queue(processed_in_batch=0)
        self._emit_ingestion_artifacts(proposal_id)
        return event

    def seed_demo_data(self) -> None:
        if self.comments:
            return
        self.generate_mock_discussion(top_level_per_proposal=self._top_level_per_proposal, seed=self._seed)

    def _reset_generated_state(self) -> None:
        self.pending_events.clear()
        self.comments.clear()
        self.comment_index.clear()
        self.children_by_parent.clear()
        self.stage1_results.clear()
        self.stage2_insights.clear()
        self.review_initial_rows.clear()
        self.review_final_rows.clear()
        self.review_corrections.clear()
        self.review_metrics.clear()
        self.reaction_totals = defaultdict(lambda: {k: 0 for k in REACTION_KEYS})
        self.moderation_state.clear()
        self._moderation_events.clear()
        self._dirty_proposals.clear()
        self._id_counter = count(1)
        self.validation_stats = {"pass": 0, "fail": 0}
        self.validation_timeline.clear()
        self.queue_snapshots.clear()
        self.store_snapshots.clear()
        self.scheduler_triggers.clear()

    def generate_mock_discussion(self, top_level_per_proposal: int = 100, seed: int = 2026) -> None:
        self._reset_generated_state()
        rng = random.Random(seed)
        base = datetime(2026, 1, 15, 8, 0, 0)
        authors = ["Μαρία", "Νίκος", "Ελένη", "Γιώργος", "Άννα", "Σοφία", "Δημήτρης", "Κατερίνα", "Ιωάννης", "Αλέξης"]
        stance_templates = {
            "support": [
                "Στηρίζω αυτή την πρόταση γιατί βελτιώνει την καθημερινή κινητικότητα και τη ζωή στην πόλη.",
                "Πολύ θετική κατεύθυνση, αρκεί να υπάρχουν διαφάνεια και σαφή στάδια υλοποίησης.",
                "Καλή δημόσια παρέμβαση, αν διασφαλιστούν συντήρηση και ασφάλεια.",
            ],
            "against": [
                "Διαφωνώ αν δεν υπάρχουν πρώτα εναλλακτικές λύσεις κυκλοφορίας.",
                "Αυτό μοιάζει ριψοκίνδυνο για την πρόσβαση και τη λειτουργία των τοπικών επιχειρήσεων.",
                "Φοβάμαι ότι θα αποτύχει χωρίς σοβαρές λεπτομέρειες υλοποίησης.",
            ],
            "mixed": [
                "Συμφωνώ ως ιδέα, αλλά χρειάζονται σαφή χρονοδιαγράμματα και μετρήσιμοι στόχοι.",
                "Ενδιαφέρουσα πρόταση, όμως το αποτέλεσμα θα κριθεί από την ποιότητα υλοποίησης.",
                "Στήριξη με όρους: τεκμηρίωση, λογοδοσία και δικαιοσύνη.",
            ],
            "irony": [
                "Ναι βέβαια, αφού όλες οι προηγούμενες υποσχέσεις εφαρμόστηκαν τέλεια /s.",
                "Τέλεια, άλλη μία μαγική λύση χωρίς καθυστερήσεις, φυσικά.",
            ],
            "harsh_evidence": [
                "Ο σχεδιασμός είναι προβληματικός· τα στοιχεία των αναφορών δείχνουν ανεπαρκή χωρητικότητα.",
                "Η σκληρή αλήθεια είναι ότι οι αναλογίες του κόστους δεν βγαίνουν και τα δημοσιευμένα νούμερα δεν συμφωνούν.",
            ],
            "offtopic": [
                "Άσχετο με την πρόταση: σήμερα η κίνηση ήταν χαοτική και τα λεωφορεία άργησαν πολύ.",
                "Δεν αφορά άμεσα την πρόταση, αλλά ο νυχτερινός θόρυβος στη γειτονιά αυξάνεται συνεχώς.",
            ],
        }
        proposal_context = {
            "deth_park": "πάρκο και πράσινο",
            "nikis_pedestrian": "παραλιακή πεζοδρόμηση",
            "metro_west": "επέκταση μετρό δυτικά",
        }
        reply_prob = {1: 0.45, 2: 0.20, 3: 0.08}

        def build_reactions(kind: str) -> dict[str, int]:
            if kind == "support":
                return {"like": rng.randint(6, 40), "love": rng.randint(5, 30), "wow": rng.randint(1, 12), "angry": rng.randint(0, 4), "sad": rng.randint(0, 3), "dislike": rng.randint(0, 5)}
            if kind == "against":
                return {"like": rng.randint(1, 12), "love": rng.randint(0, 6), "wow": rng.randint(0, 6), "angry": rng.randint(4, 24), "sad": rng.randint(2, 14), "dislike": rng.randint(5, 22)}
            if kind == "irony":
                return {"like": rng.randint(0, 10), "love": rng.randint(0, 8), "wow": rng.randint(2, 12), "angry": rng.randint(1, 16), "sad": rng.randint(0, 8), "dislike": rng.randint(1, 12)}
            if kind == "harsh_evidence":
                return {"like": rng.randint(3, 20), "love": rng.randint(1, 10), "wow": rng.randint(1, 9), "angry": rng.randint(2, 18), "sad": rng.randint(1, 12), "dislike": rng.randint(2, 15)}
            if kind == "offtopic":
                return {"like": rng.randint(0, 8), "love": rng.randint(0, 6), "wow": rng.randint(0, 5), "angry": rng.randint(0, 8), "sad": rng.randint(0, 7), "dislike": rng.randint(0, 7)}
            return {"like": rng.randint(2, 18), "love": rng.randint(1, 12), "wow": rng.randint(0, 8), "angry": rng.randint(0, 10), "sad": rng.randint(0, 9), "dislike": rng.randint(0, 9)}

        def pick_kind() -> str:
            roll = rng.random()
            if roll < 0.28:
                return "support"
            if roll < 0.54:
                return "against"
            if roll < 0.76:
                return "mixed"
            if roll < 0.84:
                return "irony"
            if roll < 0.92:
                return "harsh_evidence"
            return "offtopic"

        def build_text(kind: str, proposal_id: str) -> str:
            prefix = proposal_context.get(proposal_id, "δημοτική πρόταση")
            phrase = rng.choice(stance_templates[kind])
            return f"[{prefix}] {phrase}"

        def add_replies(parent: CommentEvent, proposal_id: str, depth: int, ts: datetime) -> None:
            if depth > MAX_THREAD_DEPTH:
                return
            if rng.random() > reply_prob.get(depth, 0.0):
                return
            n_replies = 1 + (1 if rng.random() < 0.35 else 0)
            for idx in range(n_replies):
                kind = pick_kind()
                reply_ts = ts + timedelta(minutes=2 + idx + rng.randint(0, 4))
                reply = self.submit_comment(
                    proposal_id=proposal_id,
                    comment_text=f"Απάντηση: {build_text(kind, proposal_id)}",
                    reactions=build_reactions(kind),
                    author_name=rng.choice(authors),
                    submitted_at=reply_ts,
                    parent_comment_id=parent.comment_id,
                    thread_depth=depth,
                )
                add_replies(reply, proposal_id, depth + 1, reply_ts)

        for proposal_idx, proposal_id in enumerate(self.proposals):
            offset = proposal_idx * 20_000
            for i in range(top_level_per_proposal):
                kind = pick_kind()
                ts = base + timedelta(minutes=offset + i * 7 + rng.randint(0, 4))
                top = self.submit_comment(
                    proposal_id=proposal_id,
                    comment_text=build_text(kind, proposal_id),
                    reactions=build_reactions(kind),
                    author_name=rng.choice(authors),
                    submitted_at=ts,
                    parent_comment_id=None,
                    thread_depth=0,
                )
                add_replies(top, proposal_id, depth=1, ts=ts)

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
            result = self._enrich_stage1_result(classify_stage1(event))
            self.stage1_results[event.comment_id] = result
        return len(batch)

    def _can_auto_action(self, result: Stage1Result) -> bool:
        toxicity = float(result.agent_scores.get("toxicity", 0.0))
        profanity = float(result.agent_scores.get("profanity", 0.0))
        # Guardrail: profanity-only signal cannot force automatic suppression.
        if profanity > 0 and toxicity < 0.55:
            return True
        if toxicity >= 0.75:
            return False
        if toxicity >= 0.55 and result.offense_target in {"individual", "group"}:
            return False
        return True

    def _enrich_stage1_result(self, result: Stage1Result) -> Stage1Result:
        calibrated = calibrate_scores(result.agent_scores)
        max_prob = max(calibrated.values()) if calibrated else result.confidence
        entropy = mean_entropy(calibrated, heads={"sentiment", "stance", "irony", "toxicity", "emotion"})
        toxicity = float(calibrated.get("toxicity", result.agent_scores.get("toxicity", 0.0)))
        irony_conflict = bool(
            result.irony_flag
            and (
                (result.sentiment == "positive" and result.stance == "against")
                or (result.sentiment == "negative" and result.stance == "for")
            )
        )
        stance_sentiment_conflict = bool(
            (result.sentiment == "positive" and result.stance == "against")
            or (result.sentiment == "negative" and result.stance == "for")
        )

        abstain_flags = {
            "low_confidence": max_prob < 0.55,
            "high_entropy": entropy > 0.95,
            "irony_conflict": irony_conflict,
            "offense_gray_zone": 0.45 <= toxicity <= 0.65,
            "policy_block": not self._can_auto_action(result),
        }
        review_reason_codes = [f"REVIEW_{k.upper()}" for k, enabled in abstain_flags.items() if enabled]
        conflict_flags: list[str] = []
        if irony_conflict:
            conflict_flags.append("irony_sentiment_stance_conflict")
        if stance_sentiment_conflict:
            conflict_flags.append("sentiment_stance_conflict")

        return replace(
            result,
            calibrated_scores=calibrated,
            abstain_flags=abstain_flags,
            conflict_flags=conflict_flags,
            review_reason_codes=review_reason_codes,
        )

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
            support_ratio = 0.0 if total_reactions == 0 else round((reactions["like"] + reactions["love"]) / total_reactions, 2)
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

    def _sort_score(self, comment: CommentEvent, sort: DiscussionSort, newest_ts: float) -> tuple[float, float, float]:
        total_reacts, signed_raw, signed_norm = self._reaction_scores(comment.reactions)
        comment_ts = comment.submitted_at.timestamp()
        if sort == "newest":
            return (comment_ts, total_reacts, abs(signed_raw))
        if sort == "most_reacted":
            return (float(total_reacts), comment_ts, abs(signed_raw))

        hours_ago = max(0.0, (newest_ts - comment_ts) / 3600.0)
        recency_score = 1.0 / (1.0 + hours_ago / 24.0)
        engagement_score = min(1.0, total_reacts / 40.0)
        polarity_score = min(1.0, abs(signed_norm))
        relevance = (
            MOST_RELEVANT_WEIGHTS_V1["engagement"] * engagement_score
            + MOST_RELEVANT_WEIGHTS_V1["polarity"] * polarity_score
            + MOST_RELEVANT_WEIGHTS_V1["recency"] * recency_score
        )
        return (relevance, float(total_reacts), comment_ts)

    def _feed_candidates(
        self,
        proposal_id: str,
        *,
        include_replies: bool,
        filters: dict[str, object] | None,
    ) -> list[CommentEvent]:
        self._ensure_fresh(proposal_id)
        flt = filters or {}
        show_hidden = bool(flt.get("show_hidden", False))
        view = str(flt.get("view", "all"))
        candidates = [c for c in self.comments if c.proposal_id == proposal_id]

        if not include_replies or view == "top_level":
            candidates = [c for c in candidates if c.thread_depth == 0]
        if view == "needs_review":
            candidates = [c for c in candidates if (self.stage1_results.get(c.comment_id) and self.stage1_results[c.comment_id].review_reason_codes)]
        if not show_hidden:
            candidates = [c for c in candidates if self.moderation_state.get(c.comment_id, {}).get("moderation_status") != "hidden"]
        return candidates

    def discussion_total_count(
        self,
        proposal_id: str,
        *,
        include_replies: bool = True,
        filters: dict[str, object] | None = None,
    ) -> int:
        return len(self._feed_candidates(proposal_id, include_replies=include_replies, filters=filters))

    def discussion_feed(
        self,
        proposal_id: str,
        sort: DiscussionSort = "most_reacted",
        include_replies: bool = True,
        page: int = 1,
        page_size: int = FEED_PAGE_SIZE,
        filters: dict[str, object] | None = None,
    ) -> list[dict[str, object]]:
        candidates = self._feed_candidates(proposal_id, include_replies=include_replies, filters=filters)
        selected_ids = {c.comment_id for c in candidates}
        if not candidates:
            return []

        newest_ts = max(c.submitted_at.timestamp() for c in candidates)

        def sorted_ids(comment_ids: list[str]) -> list[str]:
            return sorted(comment_ids, key=lambda cid: self._sort_score(self.comment_index[cid], sort, newest_ts), reverse=True)

        top_ids = [c.comment_id for c in candidates if c.parent_comment_id is None or c.parent_comment_id not in selected_ids]
        ordered: list[str] = []

        def visit(comment_id: str) -> None:
            ordered.append(comment_id)
            if not include_replies:
                return
            child_ids = [cid for cid in self.children_by_parent.get(comment_id, []) if cid in selected_ids]
            for child_id in sorted_ids(child_ids):
                visit(child_id)

        for root_id in sorted_ids(top_ids):
            visit(root_id)

        page = max(1, int(page))
        page_size = max(1, int(page_size))
        start = (page - 1) * page_size
        end = start + page_size
        rows: list[dict[str, object]] = []

        for comment_id in ordered[start:end]:
            comment = self.comment_index[comment_id]
            result = self.stage1_results.get(comment_id)
            total_reacts, signed_raw, signed_norm = self._reaction_scores(comment.reactions)
            state = self.moderation_state.get(comment_id, {"moderation_status": "none", "moderation_reason": None, "moderated_by": None, "moderated_at": None})
            rows.append(
                {
                    "comment_id": comment.comment_id,
                    "proposal_id": comment.proposal_id,
                    "parent_comment_id": comment.parent_comment_id,
                    "thread_depth": comment.thread_depth,
                    "author_name": comment.author_name,
                    "submitted_at": comment.submitted_at.strftime("%Y-%m-%d %H:%M"),
                    "comment_text": comment.comment_text,
                    "reaction_breakdown": dict(comment.reactions),
                    "total_reacts": total_reacts,
                    "signed_score_raw": signed_raw,
                    "signed_score_norm": signed_norm,
                    "reply_count": len(self.children_by_parent.get(comment.comment_id, [])),
                    "sentiment": result.sentiment if result else "neutral",
                    "stance": result.stance if result else "neutral",
                    "quality": result.argument_quality_score if result else 0.0,
                    "irony_flag": result.irony_flag if result else False,
                    "emotion_scores": dict(result.emotion_scores) if result else {},
                    "emotion_intensity": float(result.emotion_intensity) if result else 0.0,
                    "toxicity_score": float(result.agent_scores.get("toxicity", 0.0)) if result else 0.0,
                    "civility_score": float(result.agent_scores.get("civility", 0.0)) if result else 0.0,
                    "profanity_score": float(result.agent_scores.get("profanity", 0.0)) if result else 0.0,
                    "review_reason_codes": list(result.review_reason_codes) if result else [],
                    "conflict_flags": list(result.conflict_flags) if result else [],
                    "abstain_flags": dict(result.abstain_flags) if result else {},
                    "moderation_status": state["moderation_status"],
                    "moderation_reason": state["moderation_reason"],
                    "moderated_by": state["moderated_by"],
                    "moderated_at": state["moderated_at"],
                }
            )
        return rows

    def apply_moderation_action(
        self,
        comment_id: str,
        action: ModerationAction,
        actor: str,
        reason: str,
    ) -> dict[str, object]:
        if comment_id not in self.comment_index:
            raise ValueError(f"Unknown comment_id: {comment_id}")
        comment = self.comment_index[comment_id]
        previous = self.moderation_state.get(comment_id, {"moderation_status": "none", "moderation_reason": None, "moderated_by": None, "moderated_at": None})
        next_status: ModerationStatus = {"flag": "flagged", "hide": "hidden", "escalate": "escalated"}[action]
        now_iso = datetime.utcnow().isoformat(timespec="seconds")
        updated = {
            "moderation_status": next_status,
            "moderation_reason": reason.strip() or action,
            "moderated_by": actor,
            "moderated_at": now_iso,
        }
        self.moderation_state[comment_id] = updated
        self._moderation_events[comment.proposal_id].append(
            {
                "comment_id": comment_id,
                "proposal_id": comment.proposal_id,
                "action": action,
                "previous_status": previous["moderation_status"],
                "new_status": next_status,
                "reason": updated["moderation_reason"],
                "actor": actor,
                "created_at": now_iso,
            }
        )
        return dict(updated)

    def moderation_log(self, proposal_id: str) -> list[dict[str, object]]:
        return list(self._moderation_events.get(proposal_id, []))

    def proposal_action_metrics(self, proposal_id: str) -> dict[str, object]:
        self._ensure_fresh(proposal_id)
        comments = [c for c in self.comments if c.proposal_id == proposal_id]
        results = [self.stage1_results[c.comment_id] for c in comments if c.comment_id in self.stage1_results]
        if not comments:
            return {
                "participation_volume": 0,
                "support_opposition_index": 0.0,
                "civility_risk_rate": 0.0,
                "review_queue_pressure": 0.0,
                "top_concern_clusters": [],
            }

        top_level_count = len([c for c in comments if c.thread_depth == 0])
        reactions = self.reaction_totals[proposal_id]
        total_reacts, signed_raw, signed_norm = self._reaction_scores(reactions)
        civility_risk = len([r for r in results if float(r.agent_scores.get("toxicity", 0.0)) >= 0.45])
        review_need = len([r for r in results if r.review_reason_codes])
        tags = Counter()
        for result in results:
            for tag in result.tags:
                tags.update([tag])
        return {
            "participation_volume": top_level_count,
            "support_opposition_index": round(signed_norm, 3),
            "support_opposition_raw": signed_raw,
            "total_reacts": total_reacts,
            "civility_risk_rate": round(civility_risk / max(1, len(results)), 3),
            "review_queue_pressure": round(review_need / max(1, len(results)), 3),
            "top_concern_clusters": [{"topic": topic, "count": count} for topic, count in tags.most_common(5)],
        }

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
            support_ratio = 0.0 if total_reactions == 0 else (reactions["like"] + reactions["love"]) / total_reactions

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

        emotion_distribution: Counter[str] = Counter()
        abstain_counter: Counter[str] = Counter()
        conflict_counter: Counter[str] = Counter()
        all_calibrated: list[dict[str, float]] = []
        for result in results:
            if result.agent_labels.get("emotion"):
                emotion_distribution.update([str(result.agent_labels["emotion"])])
            for flag, enabled in result.abstain_flags.items():
                if enabled:
                    abstain_counter.update([flag])
            for conflict in result.conflict_flags:
                conflict_counter.update([conflict])
            if result.calibrated_scores:
                all_calibrated.append(result.calibrated_scores)

        agent_outputs = [{"agent": agent, "label": label, "count": count} for (agent, label), count in sorted(label_counts.items())]

        classifier_agents = {"sentiment", "stance", "profanity", "toxicity", "relevance"}
        llm_agents = {"emotion", "irony", "argument_quality", "civility", "structure", "evidence", "clarity"}
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
        calibration_rows: list[dict[str, object]] = []
        if all_calibrated:
            merged: dict[str, list[float]] = defaultdict(list)
            for row in all_calibrated:
                for head, value in row.items():
                    merged[head].append(float(value))
            for head, values in merged.items():
                head_scores = {f"sample_{idx:04d}": val for idx, val in enumerate(values)}
                calibration_rows.append(
                    {
                        "head": head,
                        "ece_proxy": ece_proxy(head_scores),
                        "brier_proxy": brier_proxy(head_scores),
                        "avg_confidence": round(sum(values) / max(1, len(values)), 4),
                    }
                )
        abstain_rows = [{"reason": reason, "count": count} for reason, count in abstain_counter.items()]
        conflict_rows = [{"conflict": name, "count": count} for name, count in conflict_counter.items()]
        emotion_rows = [{"emotion": emotion, "count": count} for emotion, count in emotion_distribution.items()]

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
            "calibration_metrics": calibration_rows or [{"head": "none", "ece_proxy": 0.0, "brier_proxy": 0.0, "avg_confidence": 0.0}],
            "abstain_summary": abstain_rows or [{"reason": "none", "count": 0}],
            "conflict_summary": conflict_rows or [{"conflict": "none", "count": 0}],
            "emotion_distribution": emotion_rows or [{"emotion": "neutral", "count": 0}],
            "api_validation": [{"outcome": "pass", "count": self.validation_stats["pass"]}, {"outcome": "fail", "count": self.validation_stats["fail"]}],
            "queue_timeline": self.queue_snapshots,
            "bypass_vs_nlp": bypass_vs_nlp,
            "store_volume": self.store_snapshots,
            "store_freshness": freshness_rows,
            "scheduler_triggers": self.scheduler_triggers,
        }

    def comments_for_proposal(self, proposal_id: str) -> list[dict[str, object]]:
        rows = self.discussion_feed(
            proposal_id,
            sort="newest",
            include_replies=True,
            page=1,
            page_size=100000,
            filters={"show_hidden": True},
        )
        return [
            {
                "comment_id": row["comment_id"],
                "author_name": row["author_name"],
                "submitted_at": row["submitted_at"],
                "comment_text": row["comment_text"],
                "reactions_total": row["total_reacts"],
                "sentiment": row["sentiment"],
                "stance": row["stance"],
                "quality": row["quality"],
                "thread_depth": row["thread_depth"],
                "parent_comment_id": row["parent_comment_id"],
                "moderation_status": row["moderation_status"],
            }
            for row in rows
        ]

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



