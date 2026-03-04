from __future__ import annotations

from alpha_app.core.pipeline import AlphaPipeline
from alpha_app.core.proposals import PROPOSALS


def test_artifact_contract_files_exist_for_proposal(tmp_path) -> None:
    pipeline = AlphaPipeline(
        proposals=PROPOSALS,
        emit_artifacts=True,
        artifact_root=tmp_path,
        run_id="run_contract",
    )

    pipeline.open_card("deth_park")
    missing = pipeline.validate_artifact_contract("deth_park")

    assert pipeline.artifact_run_id == "run_contract"
    assert not missing


def test_initial_and_final_stage_payloads_are_available(tmp_path) -> None:
    pipeline = AlphaPipeline(
        proposals=PROPOSALS,
        emit_artifacts=True,
        artifact_root=tmp_path,
        run_id="run_stage_payloads",
    )

    pipeline.open_card("metro_west")
    initial = pipeline.read_analysis_initial_from_artifacts("metro_west")
    final = pipeline.read_analysis_final_from_artifacts("metro_west")
    corrections = pipeline.read_corrections_from_artifacts("metro_west")
    metrics = pipeline.read_review_metrics_from_artifacts("metro_west")

    assert initial
    assert final
    required_stage1_contract_keys = {
        "emotion_scores",
        "emotion_intensity",
        "agent_scores",
        "agent_labels",
        "calibrated_scores",
        "abstain_flags",
        "conflict_flags",
        "review_reason_codes",
        "offense_target",
    }
    assert required_stage1_contract_keys.issubset(set(initial[0].keys()))
    assert all("review_status" in row for row in final)
    assert isinstance(corrections, list)
    assert "correction_rate" in metrics


def test_dashboard_build_writes_visual_payload_artifact(tmp_path) -> None:
    pipeline = AlphaPipeline(
        proposals=PROPOSALS,
        emit_artifacts=True,
        artifact_root=tmp_path,
        run_id="run_visual_payload",
    )

    pipeline.build_dashboard_data(mode="advanced", proposal_id="nikis_pedestrian")
    payload = pipeline.read_visual_payload_from_artifacts("nikis_pedestrian", mode="advanced")

    assert payload["mode"] == "advanced"
    assert payload["overview"]["proposal_comparison"]
    assert payload["proposal"]["proposal_id"] == "nikis_pedestrian"
    assert "quality_telemetry" in payload["overview"]
    assert "correction_by_indicator" in payload["proposal"]
