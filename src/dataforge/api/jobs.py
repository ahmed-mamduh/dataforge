"""In-memory job store with background worker pool.

NOTE: This is suitable only for a single-process local MVP. Job state is lost
on restart. For production, use a persistent store (database) and a task queue.
"""

from __future__ import annotations

import logging
import shutil
import tempfile
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

from dataforge.api.schemas import JobStatus

logger = logging.getLogger(__name__)

MAX_WORKERS = 2
MAX_ACTIVE_JOBS = 20
MAX_RETAINED_JOBS = 50
RETENTION_SECONDS = 3600  # 1 hour
DEFAULT_JOBS_DIR = Path(tempfile.gettempdir()) / "dataforge_jobs"


@dataclass
class Job:
    job_id: str
    status: JobStatus
    work_dir: Path
    created_at: float = field(default_factory=time.monotonic)
    completed_at: float | None = None
    input_files: list[str] = field(default_factory=list)
    stats: dict | None = None
    error: str | None = None
    mapping_config: dict | None = None


class JobStore:
    """Thread-safe in-memory job registry."""

    def __init__(
        self,
        jobs_dir: Path | None = None,
        max_active: int = MAX_ACTIVE_JOBS,
        max_retained: int = MAX_RETAINED_JOBS,
        retention_seconds: float = RETENTION_SECONDS,
    ) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()
        self._jobs_dir = jobs_dir or DEFAULT_JOBS_DIR
        self._jobs_dir.mkdir(parents=True, exist_ok=True)
        self._pool = ThreadPoolExecutor(max_workers=MAX_WORKERS)
        self.max_active = max_active
        self.max_retained = max_retained
        self.retention_seconds = retention_seconds

    def active_count(self) -> int:
        with self._lock:
            return sum(
                1 for j in self._jobs.values()
                if j.status in (JobStatus.QUEUED, JobStatus.RUNNING)
            )

    def create_job(self) -> Job | None:
        """Create a new job. Returns None if the queue is full."""
        self._cleanup_expired()

        with self._lock:
            active = sum(
                1 for j in self._jobs.values()
                if j.status in (JobStatus.QUEUED, JobStatus.RUNNING)
            )
            if active >= self.max_active:
                return None

            job_id = uuid.uuid4().hex[:12]
            work_dir = self._jobs_dir / job_id
            work_dir.mkdir(parents=True, exist_ok=True)
            (work_dir / "uploads").mkdir()
            (work_dir / "output").mkdir()

            job = Job(job_id=job_id, status=JobStatus.QUEUED, work_dir=work_dir)
            self._jobs[job_id] = job
            return job

    def get_job(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def update_status(self, job_id: str, status: JobStatus) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.status = status

    def set_result(self, job_id: str, stats: dict) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.stats = stats
                job.status = JobStatus.COMPLETED
                job.completed_at = time.monotonic()

    def set_error(self, job_id: str, error: str) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.error = error
                job.status = JobStatus.FAILED
                job.completed_at = time.monotonic()

    def submit(self, job_id: str, fn: object, *args: object) -> None:
        self._pool.submit(fn, job_id, *args)  # type: ignore[arg-type]

    def cleanup_job(self, job_id: str) -> None:
        with self._lock:
            job = self._jobs.pop(job_id, None)
        if job and job.work_dir.exists():
            shutil.rmtree(job.work_dir, ignore_errors=True)

    def _cleanup_expired(self) -> None:
        """Remove completed/failed jobs older than retention_seconds."""
        now = time.monotonic()
        to_remove: list[str] = []
        with self._lock:
            terminal = [
                j for j in self._jobs.values()
                if j.status in (JobStatus.COMPLETED, JobStatus.FAILED)
                and j.completed_at is not None
            ]
            terminal.sort(key=lambda j: j.completed_at or 0)

            for job in terminal:
                age = now - (job.completed_at or now)
                if age > self.retention_seconds:
                    to_remove.append(job.job_id)

            if len(self._jobs) > self.max_retained:
                excess = len(self._jobs) - self.max_retained
                for job in terminal[:excess]:
                    if job.job_id not in to_remove:
                        to_remove.append(job.job_id)

        for jid in to_remove:
            self.cleanup_job(jid)

    def shutdown(self) -> None:
        self._pool.shutdown(wait=False)


_store: JobStore | None = None


def get_store() -> JobStore:
    global _store
    if _store is None:
        _store = JobStore()
    return _store


def reset_store(jobs_dir: Path | None = None, **kwargs: object) -> JobStore:
    """Create a fresh store — used by tests."""
    global _store
    if _store is not None:
        _store.shutdown()
    _store = JobStore(jobs_dir=jobs_dir, **kwargs)  # type: ignore[arg-type]
    return _store
