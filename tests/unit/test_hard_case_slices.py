from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from alpha_app.core.pipeline import AlphaPipeline
from alpha_app.core.proposals import PROPOSALS


def test_hard_case_slices_behave_as_expected() -> None:
    fixture_path = Path(__file__).parents[1] / "fixtures" / "hard_cases" / "cases.json"
    cases = json.loads(fixture_path.read_text(encoding="utf-8"))
    pipeline = AlphaPipeline(proposals=PROPOSALS)

    for idx, case in enumerate(cases):
        event = pipeline.submit_comment(
            proposal_id=case["proposal_id"],
            comment_text=case["text"],
            submitted_at=datetime(2026, 2, 26, 9, idx, 0),
        )
        expanded = pipeline.open_card(case["proposal_id"])
        result = next(r for r in expanded.stage1_results if r.comment_id == event.comment_id)

        expect = case["expect"]
        if "policy_block" in expect:
            assert result.abstain_flags.get("policy_block") is expect["policy_block"]
        if expect.get("has_review_reason"):
            assert result.review_reason_codes
        if "quality_min" in expect:
            assert result.argument_quality_score >= float(expect["quality_min"])
        if "relevance_label" in expect:
            assert result.agent_labels.get("relevance") == expect["relevance_label"]
