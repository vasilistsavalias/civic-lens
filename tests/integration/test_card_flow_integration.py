from __future__ import annotations

from alpha_app.core.pipeline import AlphaPipeline
from alpha_app.core.proposals import PROPOSALS


def test_card_open_triggers_recompute_only_for_target_proposal() -> None:
    pipeline = AlphaPipeline(proposals=PROPOSALS)
    p1_before = pipeline.open_card("deth_park").insight.generated_at
    p2_before = pipeline.open_card("metro_west").insight.generated_at

    pipeline.submit_comment(
        proposal_id="deth_park",
        comment_text="Ναι στο πάρκο, με προσοχή στην κυκλοφορία.",
        reactions={"likes": 4, "support": 3, "angry": 0, "laugh": 0},
    )

    p1_after = pipeline.open_card("deth_park").insight.generated_at
    p2_after = pipeline.open_card("metro_west").insight.generated_at

    assert p1_after >= p1_before
    assert p2_after == p2_before

