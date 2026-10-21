"""Pipeline orchestrator — chains ingestion, mapping, normalization, validation, dedup."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from dataforge.config import PipelineConfig
from dataforge.deduplication import deduplicate
from dataforge.ingestion import read_file
from dataforge.mapping import apply_mapping, select_mapping
from dataforge.normalization import normalize_dataframe
from dataforge.reporting import write_outputs
from dataforge.validation import validate_dataframe


@dataclass
class PipelineResult:
    valid_df: pd.DataFrame
    rejected_df: pd.DataFrame
    stats: dict
    output_paths: dict[str, Path] = field(default_factory=dict)


def run_pipeline(config: PipelineConfig) -> PipelineResult:
    """Execute the full cleaning pipeline.

    Order: per-file (ingest → map → normalize) → concat → validate → dedup → output.
    """
    normalized_frames: list[pd.DataFrame] = []
    per_file_counts: dict[str, int] = {}

    for input_path in config.input_files:
        path = Path(input_path)
        df = read_file(path)
        per_file_counts[path.name] = len(df)

        mapping = select_mapping(list(df.columns), config.column_mappings)
        df = apply_mapping(df, mapping)
        df = normalize_dataframe(df)
        normalized_frames.append(df)

    if not normalized_frames:
        empty = pd.DataFrame()
        return PipelineResult(
            valid_df=empty,
            rejected_df=empty,
            stats={"input_rows": 0, "accepted": 0, "rejected": 0, "duplicates": 0},
        )

    combined = pd.concat(normalized_frames, ignore_index=True)
    total_input = len(combined)

    valid, rejected_validation = validate_dataframe(combined, config.validation)

    unique, rejected_dedup = deduplicate(valid, config.deduplication)

    all_rejected = pd.concat([rejected_validation, rejected_dedup], ignore_index=True)

    stats = _build_stats(
        total_input=total_input,
        accepted=len(unique),
        rejected_validation=len(rejected_validation),
        rejected_dedup=len(rejected_dedup),
        all_rejected=all_rejected,
        per_file_counts=per_file_counts,
    )

    assert total_input == len(unique) + len(all_rejected), (
        f"Row count mismatch: {total_input} != {len(unique)} + {len(all_rejected)}"
    )

    output_paths = write_outputs(unique, all_rejected, stats, config.output_dir)

    return PipelineResult(
        valid_df=unique,
        rejected_df=all_rejected,
        stats=stats,
        output_paths=output_paths,
    )


def _build_stats(
    total_input: int,
    accepted: int,
    rejected_validation: int,
    rejected_dedup: int,
    all_rejected: pd.DataFrame,
    per_file_counts: dict[str, int],
) -> dict:
    reason_counts: dict[str, int] = {}
    if "_rejection_reasons" in all_rejected.columns:
        for reasons_str in all_rejected["_rejection_reasons"]:
            for reason in str(reasons_str).split("; "):
                tag = reason.split(":")[0]
                reason_counts[tag] = reason_counts.get(tag, 0) + 1

    per_file_rejected: dict[str, int] = {}
    if "_source_file" in all_rejected.columns:
        for fname, group in all_rejected.groupby("_source_file"):
            per_file_rejected[str(fname)] = len(group)

    return {
        "input_rows": total_input,
        "accepted": accepted,
        "rejected": rejected_validation + rejected_dedup,
        "rejected_validation": rejected_validation,
        "duplicates": rejected_dedup,
        "reason_counts": reason_counts,
        "per_file": {
            fname: {
                "input_rows": count,
                "rejected": per_file_rejected.get(fname, 0),
            }
            for fname, count in per_file_counts.items()
        },
    }
