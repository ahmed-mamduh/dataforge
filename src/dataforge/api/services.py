"""Job processing service — bridges uploads to the existing engine."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from dataforge.api.jobs import JobStore
from dataforge.api.schemas import JobStatus
from dataforge.api.security import sanitize_csv_file
from dataforge.config import ColumnMapping, PipelineConfig
from dataforge.engine import run_pipeline

logger = logging.getLogger(__name__)


def process_job(
    job_id: str,
    store: JobStore,
    input_files: list[Path],
    column_mappings: list[ColumnMapping] | None,
) -> None:
    """Run the cleaning pipeline for a job. Called in a worker thread."""
    job = store.get_job(job_id)
    if not job:
        return

    store.update_status(job_id, JobStatus.RUNNING)

    try:
        output_dir = job.work_dir / "output"
        kwargs: dict = {
            "input_files": input_files,
            "output_dir": output_dir,
        }
        if column_mappings:
            kwargs["column_mappings"] = column_mappings

        config = PipelineConfig(**kwargs)
        result = run_pipeline(config)

        cleaned_csv = output_dir / "cleaned.csv"
        if cleaned_csv.exists():
            sanitized = output_dir / "cleaned_safe.csv"
            sanitize_csv_file(cleaned_csv, sanitized)
            sanitized.replace(cleaned_csv)

        rejected_csv = output_dir / "rejected.csv"
        if rejected_csv.exists():
            sanitized = output_dir / "rejected_safe.csv"
            sanitize_csv_file(rejected_csv, sanitized)
            sanitized.replace(rejected_csv)

        store.set_result(job_id, result.stats)

    except Exception as e:
        logger.exception("Job %s failed", job_id)
        store.set_error(job_id, str(e))
