from __future__ import annotations

import csv
import json
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from alpha_app.domain.models import CommentEvent, DashboardOverviewSeries, DashboardProposalSeries, Stage2Insight

STAGE_FILE_CONTRACT = (
    "raw/comments.json",
    "segments/comment_segments.json",
    "analysis/initial/stage1_results.json",
    "analysis/initial/stage1_results.csv",
    "analysis/final/stage1_results.json",
    "analysis/final/stage1_results.csv",
    "analysis/final/corrections.json",
    "analysis/final/review_metrics.json",
    "analysis/final/stage2_insight.json",
)


def default_artifact_root() -> Path:
    return Path.cwd() / "artifacts" / "pipeline_runs"


def build_run_id(now: datetime | None = None) -> str:
    timestamp = (now or datetime.utcnow()).strftime("%Y%m%dT%H%M%SZ")
    return f"run_{timestamp}"


def _jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, datetime):
        return value.isoformat(timespec="seconds")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    return value


def _comment_to_row(comment: CommentEvent) -> dict[str, Any]:
    return {
        "municipality_id": comment.municipality_id,
        "proposal_id": comment.proposal_id,
        "comment_id": comment.comment_id,
        "author_name": comment.author_name,
        "comment_text": comment.comment_text,
        "reactions": dict(comment.reactions),
        "submitted_at": comment.submitted_at.isoformat(timespec="seconds"),
    }


def _comment_segment_row(comment: CommentEvent) -> dict[str, Any]:
    return {
        "comment_id": comment.comment_id,
        "proposal_id": comment.proposal_id,
        "segment_id": f"{comment.comment_id}_seg_001",
        "segment_index": 1,
        "segment_text": comment.comment_text,
        "source": "comment",
    }


class PipelineArtifacts:
    def __init__(self, root: Path | str | None = None, run_id: str | None = None) -> None:
        self.root = Path(root) if root is not None else default_artifact_root()
        self.root.mkdir(parents=True, exist_ok=True)
        self.run_id = self._resolve_run_id(run_id or build_run_id())
        self.run_root = self.root / self.run_id
        self.run_root.mkdir(parents=True, exist_ok=True)

    def _resolve_run_id(self, base_run_id: str) -> str:
        if not (self.root / base_run_id).exists():
            return base_run_id
        suffix = 1
        while True:
            candidate = f"{base_run_id}_{suffix:02d}"
            if not (self.root / candidate).exists():
                return candidate
            suffix += 1

    def proposal_dir(self, proposal_id: str) -> Path:
        target = self.run_root / proposal_id
        target.mkdir(parents=True, exist_ok=True)
        return target

    def write_json(self, proposal_id: str, relative_path: str, payload: Any) -> Path:
        destination = self.proposal_dir(proposal_id) / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w", encoding="utf-8") as f:
            json.dump(_jsonable(payload), f, ensure_ascii=False, indent=2)
        return destination

    def write_csv(
        self,
        proposal_id: str,
        relative_path: str,
        rows: list[dict[str, Any]],
        *,
        fieldnames: list[str] | None = None,
    ) -> Path:
        destination = self.proposal_dir(proposal_id) / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        resolved_fieldnames = fieldnames or sorted({key for row in rows for key in row.keys()})
        with destination.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=resolved_fieldnames)
            if resolved_fieldnames:
                writer.writeheader()
                if rows:
                    writer.writerows(rows)
        return destination

    def read_json(self, proposal_id: str, relative_path: str) -> Any:
        source = self.proposal_dir(proposal_id) / relative_path
        with source.open("r", encoding="utf-8") as f:
            return json.load(f)

    def missing_contract_files(self, proposal_id: str) -> list[str]:
        target = self.proposal_dir(proposal_id)
        return [path for path in STAGE_FILE_CONTRACT if not (target / path).exists()]

    def write_ingestion_artifacts(self, proposal_id: str, comments: list[CommentEvent]) -> None:
        raw_rows = [_comment_to_row(comment) for comment in comments]
        segment_rows = [_comment_segment_row(comment) for comment in comments]
        self.write_json(proposal_id, "raw/comments.json", raw_rows)
        self.write_json(proposal_id, "segments/comment_segments.json", segment_rows)

    def write_analysis_artifacts(
        self,
        proposal_id: str,
        *,
        initial_rows: list[dict[str, Any]],
        final_rows: list[dict[str, Any]],
        corrections: list[dict[str, Any]],
        review_metrics: dict[str, Any],
        insight: Stage2Insight,
    ) -> None:
        self.write_json(proposal_id, "analysis/initial/stage1_results.json", initial_rows)
        self.write_csv(
            proposal_id,
            "analysis/initial/stage1_results.csv",
            initial_rows,
        )
        self.write_json(proposal_id, "analysis/final/stage1_results.json", final_rows)
        self.write_csv(
            proposal_id,
            "analysis/final/stage1_results.csv",
            final_rows,
        )
        self.write_json(proposal_id, "analysis/final/corrections.json", corrections)
        self.write_json(proposal_id, "analysis/final/review_metrics.json", review_metrics)
        self.write_json(proposal_id, "analysis/final/stage2_insight.json", insight)

    def write_visual_payload(
        self,
        proposal_id: str,
        *,
        mode: str,
        overview: DashboardOverviewSeries,
        proposal: DashboardProposalSeries,
    ) -> None:
        self.write_json(
            proposal_id,
            f"analysis/visuals/dashboard_{mode}.json",
            {
                "mode": mode,
                "overview": overview,
                "proposal": proposal,
            },
        )
