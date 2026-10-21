"""API route handlers."""

from __future__ import annotations

import csv
import io
import json
import zipfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse

from dataforge import __version__
from dataforge.api.jobs import get_store
from dataforge.api.schemas import (
    ErrorResponse,
    HealthResponse,
    JobCreatedResponse,
    JobStatus,
    JobStatusResponse,
    PreviewResponse,
)
from dataforge.api.security import (
    MAX_FILE_SIZE,
    MAX_FILES_PER_REQUEST,
    safe_filename,
    validate_extension,
)
from dataforge.config import (
    CANONICAL_FIELDS,
    ColumnMapping,
    MappingConfigError,
)

router = APIRouter()

UPLOAD_CHUNK_SIZE = 64 * 1024  # 64 KB
PREVIEW_MAX_ROWS = 100


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(version=__version__)


@router.post(
    "/api/v1/jobs",
    response_model=JobCreatedResponse,
    status_code=201,
    responses={
        400: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
    },
)
async def create_job(
    files: list[UploadFile] = File(...),
    mapping_config: str | None = Form(default=None),
) -> JobCreatedResponse:
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    if len(files) > MAX_FILES_PER_REQUEST:
        raise HTTPException(
            status_code=400,
            detail=f"Too many files ({len(files)}). Maximum is {MAX_FILES_PER_REQUEST}",
        )

    column_mappings: list[ColumnMapping] | None = None
    if mapping_config:
        column_mappings = _parse_mapping_config(mapping_config)

    store = get_store()
    job = store.create_job()
    if job is None:
        raise HTTPException(
            status_code=429,
            detail="Too many active jobs. Please try again later.",
        )

    saved_files: list[Path] = []
    used_names: set[str] = set()

    try:
        for upload in files:
            filename = upload.filename or "upload.csv"
            ext_error = validate_extension(filename)
            if ext_error:
                raise HTTPException(status_code=400, detail=ext_error)

            sname = safe_filename(filename)
            if sname in used_names:
                stem = Path(sname).stem
                suffix = Path(sname).suffix
                counter = 2
                while sname in used_names:
                    sname = f"{stem}_{counter}{suffix}"
                    counter += 1
            used_names.add(sname)

            dest = job.work_dir / "uploads" / sname
            size = await _stream_upload(upload, dest)

            if size > MAX_FILE_SIZE:
                dest.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=400,
                    detail=f"File '{filename}' exceeds 10 MB limit",
                )
            if size == 0:
                dest.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=400,
                    detail=f"File '{filename}' is empty",
                )

            saved_files.append(dest)

        job.input_files = [f.name for f in saved_files]
    except HTTPException:
        store.cleanup_job(job.job_id)
        raise

    from dataforge.api.services import process_job

    store.submit(job.job_id, process_job, store, saved_files, column_mappings)

    return JobCreatedResponse(
        job_id=job.job_id,
        status=JobStatus.QUEUED,
        files_received=len(saved_files),
    )


async def _stream_upload(upload: UploadFile, dest: Path) -> int:
    """Stream an upload to disk in chunks, returning total bytes written."""
    total = 0
    with open(dest, "wb") as f:
        while True:
            chunk = await upload.read(UPLOAD_CHUNK_SIZE)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_FILE_SIZE:
                f.close()
                return total
            f.write(chunk)
    return total


@router.get(
    "/api/v1/jobs/{job_id}",
    response_model=JobStatusResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_job_status(job_id: str) -> JobStatusResponse:
    job = get_store().get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        files=job.input_files,
        stats=job.stats,
        error=job.error,
    )


@router.get(
    "/api/v1/jobs/{job_id}/report",
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
async def get_job_report(job_id: str) -> dict:
    job = get_store().get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status == JobStatus.FAILED:
        raise HTTPException(status_code=409, detail=f"Job failed: {job.error}")
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=409,
            detail=f"Job is not complete (status: {job.status.value})",
        )

    report_path = job.work_dir / "output" / "quality-report.json"
    if not report_path.exists():
        raise HTTPException(status_code=500, detail="Report file missing")

    with open(report_path, encoding="utf-8") as f:
        return json.load(f)


@router.get(
    "/api/v1/jobs/{job_id}/download",
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
async def download_job(job_id: str) -> StreamingResponse:
    job = get_store().get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status == JobStatus.FAILED:
        raise HTTPException(status_code=409, detail=f"Job failed: {job.error}")
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=409,
            detail=f"Job is not complete (status: {job.status.value})",
        )

    output_dir = job.work_dir / "output"
    expected_files = ["cleaned.csv", "rejected.csv", "quality-report.json"]
    for fname in expected_files:
        if not (output_dir / fname).exists():
            raise HTTPException(status_code=500, detail=f"Output file '{fname}' missing")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname in expected_files:
            zf.write(output_dir / fname, fname)
    buf.seek(0)

    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=dataforge_{job_id}.zip"},
    )


@router.get(
    "/api/v1/jobs/{job_id}/preview",
    response_model=PreviewResponse,
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
async def preview_job(job_id: str, limit: int = PREVIEW_MAX_ROWS) -> PreviewResponse:
    """Return a bounded preview of cleaned and rejected records."""
    job = get_store().get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status == JobStatus.FAILED:
        raise HTTPException(status_code=409, detail=f"Job failed: {job.error}")
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=409,
            detail=f"Job is not complete (status: {job.status.value})",
        )

    limit = max(1, min(limit, PREVIEW_MAX_ROWS))
    output_dir = job.work_dir / "output"

    cleaned_rows, cleaned_total = _read_csv_preview(output_dir / "cleaned.csv", limit)
    rejected_rows, rejected_total = _read_csv_preview(output_dir / "rejected.csv", limit)

    return PreviewResponse(
        job_id=job_id,
        cleaned=cleaned_rows,
        rejected=rejected_rows,
        cleaned_total=cleaned_total,
        rejected_total=rejected_total,
    )


def _read_csv_preview(path: Path, limit: int) -> tuple[list[dict], int]:
    """Read up to `limit` rows from a CSV, returning (rows, total_count)."""
    if not path.exists():
        return [], 0

    rows: list[dict] = []
    total = 0
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total += 1
            if len(rows) < limit:
                rows.append(dict(row))
    return rows, total


def _parse_mapping_config(raw: str) -> list[ColumnMapping]:
    """Parse and validate the mapping_config form field."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid mapping_config JSON: {e}")

    if not isinstance(data, dict) or "mappings" not in data:
        raise HTTPException(
            status_code=400,
            detail="mapping_config must have a 'mappings' key",
        )

    mappings_raw = data["mappings"]
    if not isinstance(mappings_raw, list) or len(mappings_raw) == 0:
        raise HTTPException(status_code=400, detail="'mappings' must be a non-empty list")

    result: list[ColumnMapping] = []
    for i, entry in enumerate(mappings_raw):
        if not isinstance(entry, dict) or "mapping" not in entry:
            raise HTTPException(
                status_code=400,
                detail=f"mappings[{i}] must have a 'mapping' key",
            )
        raw_map = entry["mapping"]
        if not isinstance(raw_map, dict) or len(raw_map) == 0:
            raise HTTPException(
                status_code=400,
                detail=f"mappings[{i}].mapping must be a non-empty object",
            )
        targets = list(raw_map.values())
        for t in targets:
            if t not in CANONICAL_FIELDS:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unknown canonical field '{t}' in mappings[{i}]",
                )
        if len(set(targets)) != len(targets):
            raise HTTPException(
                status_code=400,
                detail=f"Duplicate target fields in mappings[{i}]",
            )
        result.append(ColumnMapping(mapping=raw_map))

    return result
