from __future__ import annotations

from datetime import datetime

import pytest

from alpha_app.config import MAX_THREAD_DEPTH
from alpha_app.core.pipeline import AlphaPipeline
from alpha_app.core.proposals import PROPOSALS


def _small_pipeline() -> AlphaPipeline:
    return AlphaPipeline(proposals=PROPOSALS, top_level_per_proposal=12, seed=42)


def test_generator_creates_expected_top_level_volume_per_proposal() -> None:
    pipeline = _small_pipeline()
    for proposal_id in pipeline.proposals:
        top_level = [c for c in pipeline.comments if c.proposal_id == proposal_id and c.thread_depth == 0]
        assert len(top_level) == 12


def test_legacy_reactions_are_mapped_to_new_schema() -> None:
    pipeline = AlphaPipeline(proposals=PROPOSALS, top_level_per_proposal=1, seed=7)
    proposal_id = next(iter(pipeline.proposals))
    event = pipeline.submit_comment(
        proposal_id=proposal_id,
        comment_text="legacy reaction mapping",
        reactions={"likes": 2, "support": 3, "laugh": 1, "angry": 4},
        submitted_at=datetime(2026, 2, 25, 10, 0, 0),
    )
    assert event.reactions["like"] == 2
    assert event.reactions["love"] == 3
    assert event.reactions["wow"] == 1
    assert event.reactions["angry"] == 4


def test_thread_depth_cap_is_enforced() -> None:
    pipeline = AlphaPipeline(proposals=PROPOSALS, top_level_per_proposal=1, seed=9)
    proposal_id = next(iter(pipeline.proposals))
    top = pipeline.submit_comment(
        proposal_id=proposal_id,
        comment_text="top",
        reactions={"like": 1},
        submitted_at=datetime(2026, 2, 25, 11, 0, 0),
    )

    parent = top
    for depth in range(1, MAX_THREAD_DEPTH + 1):
        parent = pipeline.submit_comment(
            proposal_id=proposal_id,
            comment_text=f"depth {depth}",
            reactions={"like": 1},
            submitted_at=datetime(2026, 2, 25, 11, depth, 0),
            parent_comment_id=parent.comment_id,
            thread_depth=depth,
        )

    with pytest.raises(ValueError):
        pipeline.submit_comment(
            proposal_id=proposal_id,
            comment_text="too deep",
            reactions={"like": 1},
            submitted_at=datetime(2026, 2, 25, 11, 59, 0),
            parent_comment_id=parent.comment_id,
            thread_depth=MAX_THREAD_DEPTH + 1,
        )


def test_discussion_feed_most_reacted_is_sorted_descending() -> None:
    pipeline = AlphaPipeline(proposals=PROPOSALS, top_level_per_proposal=6, seed=14)
    proposal_id = next(iter(pipeline.proposals))
    rows = pipeline.discussion_feed(
        proposal_id,
        sort="most_reacted",
        include_replies=False,
        page=1,
        page_size=20,
        filters={"show_hidden": True},
    )
    totals = [int(row["total_reacts"]) for row in rows]
    assert totals == sorted(totals, reverse=True)


def test_feed_pagination_is_stable_and_non_overlapping() -> None:
    pipeline = AlphaPipeline(proposals=PROPOSALS, top_level_per_proposal=10, seed=21)
    proposal_id = next(iter(pipeline.proposals))
    page1 = pipeline.discussion_feed(
        proposal_id,
        sort="most_reacted",
        include_replies=False,
        page=1,
        page_size=5,
        filters={"show_hidden": True},
    )
    page2 = pipeline.discussion_feed(
        proposal_id,
        sort="most_reacted",
        include_replies=False,
        page=2,
        page_size=5,
        filters={"show_hidden": True},
    )
    assert page1
    assert page2
    ids_1 = {row["comment_id"] for row in page1}
    ids_2 = {row["comment_id"] for row in page2}
    assert ids_1.isdisjoint(ids_2)


def test_moderation_actions_update_state_and_audit_log() -> None:
    pipeline = AlphaPipeline(proposals=PROPOSALS, top_level_per_proposal=4, seed=12)
    proposal_id = next(iter(pipeline.proposals))
    row = pipeline.discussion_feed(
        proposal_id,
        sort="most_reacted",
        include_replies=False,
        page=1,
        page_size=1,
        filters={"show_hidden": True},
    )[0]

    state = pipeline.apply_moderation_action(str(row["comment_id"]), "escalate", "supervisor", "high-risk thread")
    assert state["moderation_status"] == "escalated"

    events = pipeline.moderation_log(proposal_id)
    assert events
    assert events[-1]["comment_id"] == row["comment_id"]
    assert events[-1]["action"] == "escalate"
