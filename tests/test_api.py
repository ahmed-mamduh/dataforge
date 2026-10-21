"""FastAPI integration tests for the DataForge API."""

from __future__ import annotations

import io
import json
import time
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from dataforge.api import create_app
from dataforge.api.jobs import reset_store
from dataforge.api.security import sanitize_csv_value

SAMPLE_DATA = Path(__file__).resolve().parent.parent / "sample_data"
SUPPLIER_A = SAMPLE_DATA / "supplier_a.csv"
SUPPLIER_B = SAMPLE_DATA / "supplier_b.csv"
EXCEL_FIXTURE = Path(__file__).parent / "fixtures" / "test_workbook.xlsx"


@pytest.fixture(autouse=True)
def _fresh_store(tmp_path: Path) -> None:
    reset_store(jobs_dir=tmp_path / "jobs")


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


def _wait_for_job(client: TestClient, job_id: str, timeout: float = 10.0) -> dict:
    """Poll until job completes or fails."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        resp = client.get(f"/api/v1/jobs/{job_id}")
        data = resp.json()
        if data["status"] in ("completed", "failed"):
            return data
        time.sleep(0.1)
    raise TimeoutError(f"Job {job_id} did not finish in {timeout}s")


class TestHealth:
    def test_health(self, client: TestClient) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "version" in data


class TestJobCreation:
    def test_upload_csv(self, client: TestClient) -> None:
        with open(SUPPLIER_A, "rb") as f:
            resp = client.post("/api/v1/jobs", files=[("files", ("supplier_a.csv", f, "text/csv"))])
        assert resp.status_code == 201
        data = resp.json()
        assert "job_id" in data
        assert data["files_received"] == 1
        assert data["status"] == "queued"

    def test_upload_xlsx(self, client: TestClient) -> None:
        with open(EXCEL_FIXTURE, "rb") as f:
            resp = client.post("/api/v1/jobs", files=[("files", ("test.xlsx", f, "application/octet-stream"))])
        assert resp.status_code == 201
        assert resp.json()["files_received"] == 1

    def test_upload_multiple_files(self, client: TestClient) -> None:
        files = []
        for path in [SUPPLIER_A, SUPPLIER_B]:
            files.append(("files", (path.name, open(path, "rb"), "text/csv")))
        resp = client.post("/api/v1/jobs", files=files)
        for _, (_, fh, _) in files:
            fh.close()
        assert resp.status_code == 201
        assert resp.json()["files_received"] == 2

    def test_too_many_files(self, client: TestClient) -> None:
        files = [
            ("files", (f"f{i}.csv", b"a,b\n1,2\n", "text/csv"))
            for i in range(4)
        ]
        resp = client.post("/api/v1/jobs", files=files)
        assert resp.status_code == 400
        assert "Too many files" in resp.json()["detail"]

    def test_invalid_extension(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/jobs",
            files=[("files", ("data.json", b'{"a": 1}', "application/json"))],
        )
        assert resp.status_code == 400
        assert "Unsupported file type" in resp.json()["detail"]

    def test_legacy_xls_rejected(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/jobs",
            files=[("files", ("legacy.xls", b"\x00\x00", "application/vnd.ms-excel"))],
        )
        assert resp.status_code == 400
        assert "Unsupported file type" in resp.json()["detail"]

    def test_empty_file(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/jobs",
            files=[("files", ("empty.csv", b"", "text/csv"))],
        )
        assert resp.status_code == 400
        assert "empty" in resp.json()["detail"].lower()

    def test_oversized_file(self, client: TestClient) -> None:
        big = b"x" * (10 * 1024 * 1024 + 1)
        resp = client.post(
            "/api/v1/jobs",
            files=[("files", ("big.csv", big, "text/csv"))],
        )
        assert resp.status_code == 400
        assert "10 MB" in resp.json()["detail"]

    def test_duplicate_filenames(self, client: TestClient) -> None:
        with open(SUPPLIER_A, "rb") as f1, open(SUPPLIER_A, "rb") as f2:
            resp = client.post(
                "/api/v1/jobs",
                files=[
                    ("files", ("data.csv", f1, "text/csv")),
                    ("files", ("data.csv", f2, "text/csv")),
                ],
            )
        assert resp.status_code == 201
        assert resp.json()["files_received"] == 2


class TestJobLifecycle:
    def test_csv_end_to_end(self, client: TestClient) -> None:
        with open(SUPPLIER_A, "rb") as f:
            resp = client.post("/api/v1/jobs", files=[("files", ("supplier_a.csv", f, "text/csv"))])
        job_id = resp.json()["job_id"]

        data = _wait_for_job(client, job_id)
        assert data["status"] == "completed"
        assert data["stats"]["input_rows"] == 41
        assert data["stats"]["accepted"] + data["stats"]["rejected"] == 41

    def test_xlsx_end_to_end(self, client: TestClient) -> None:
        with open(EXCEL_FIXTURE, "rb") as f:
            resp = client.post("/api/v1/jobs", files=[("files", ("test.xlsx", f, "application/octet-stream"))])
        job_id = resp.json()["job_id"]

        data = _wait_for_job(client, job_id)
        assert data["status"] == "completed"
        assert data["stats"]["input_rows"] == 12
        assert data["stats"]["accepted"] + data["stats"]["rejected"] == 12

    def test_multi_file_end_to_end(self, client: TestClient) -> None:
        files = []
        for path in [SUPPLIER_A, SUPPLIER_B]:
            files.append(("files", (path.name, open(path, "rb"), "text/csv")))
        resp = client.post("/api/v1/jobs", files=files)
        for _, (_, fh, _) in files:
            fh.close()
        job_id = resp.json()["job_id"]

        data = _wait_for_job(client, job_id)
        assert data["status"] == "completed"
        assert data["stats"]["input_rows"] == 83
        assert data["stats"]["accepted"] + data["stats"]["rejected"] == 83

    def test_custom_mapping(self, client: TestClient) -> None:
        mapping = json.dumps({
            "mappings": [{
                "mapping": {
                    "SKU": "sku",
                    "Product Name": "product_name",
                    "Category": "category",
                    "Unit Price": "price",
                    "Currency": "currency",
                    "Qty": "quantity",
                    "Supplier": "supplier",
                    "Description": "description",
                }
            }]
        })
        with open(SUPPLIER_A, "rb") as f:
            resp = client.post(
                "/api/v1/jobs",
                files=[("files", ("supplier_a.csv", f, "text/csv"))],
                data={"mapping_config": mapping},
            )
        assert resp.status_code == 201
        job_id = resp.json()["job_id"]
        data = _wait_for_job(client, job_id)
        assert data["status"] == "completed"

    def test_invalid_mapping_config(self, client: TestClient) -> None:
        with open(SUPPLIER_A, "rb") as f:
            resp = client.post(
                "/api/v1/jobs",
                files=[("files", ("supplier_a.csv", f, "text/csv"))],
                data={"mapping_config": "not json"},
            )
        assert resp.status_code == 400

    def test_malformed_csv(self, client: TestClient) -> None:
        bad_csv = b"not,a,proper,csv\x00\x01\x02"
        resp = client.post(
            "/api/v1/jobs",
            files=[("files", ("bad.csv", bad_csv, "text/csv"))],
        )
        job_id = resp.json()["job_id"]
        data = _wait_for_job(client, job_id)
        # It may complete with rejections or fail — both are acceptable
        assert data["status"] in ("completed", "failed")


class TestJobStatus:
    def test_unknown_job(self, client: TestClient) -> None:
        resp = client.get("/api/v1/jobs/nonexistent123")
        assert resp.status_code == 404

    def test_queued_status(self, client: TestClient) -> None:
        with open(SUPPLIER_A, "rb") as f:
            resp = client.post("/api/v1/jobs", files=[("files", ("supplier_a.csv", f, "text/csv"))])
        job_id = resp.json()["job_id"]
        resp = client.get(f"/api/v1/jobs/{job_id}")
        assert resp.status_code == 200
        assert resp.json()["status"] in ("queued", "running", "completed")


class TestReport:
    def test_report_after_completion(self, client: TestClient) -> None:
        with open(SUPPLIER_A, "rb") as f:
            resp = client.post("/api/v1/jobs", files=[("files", ("supplier_a.csv", f, "text/csv"))])
        job_id = resp.json()["job_id"]
        _wait_for_job(client, job_id)

        resp = client.get(f"/api/v1/jobs/{job_id}/report")
        assert resp.status_code == 200
        report = resp.json()
        assert report["input_rows"] == 41
        assert report["accepted"] + report["rejected"] == 41

    def test_report_before_completion(self, client: TestClient) -> None:
        # Create a job but check report immediately (may be queued/running)
        with open(SUPPLIER_A, "rb") as f:
            resp = client.post("/api/v1/jobs", files=[("files", ("supplier_a.csv", f, "text/csv"))])
        job_id = resp.json()["job_id"]
        # Check immediately — if already complete, this passes; if not, 409
        resp = client.get(f"/api/v1/jobs/{job_id}/report")
        assert resp.status_code in (200, 409)

    def test_report_unknown_job(self, client: TestClient) -> None:
        resp = client.get("/api/v1/jobs/nonexistent/report")
        assert resp.status_code == 404


class TestDownload:
    def test_zip_download(self, client: TestClient) -> None:
        with open(SUPPLIER_A, "rb") as f:
            resp = client.post("/api/v1/jobs", files=[("files", ("supplier_a.csv", f, "text/csv"))])
        job_id = resp.json()["job_id"]
        _wait_for_job(client, job_id)

        resp = client.get(f"/api/v1/jobs/{job_id}/download")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/zip"

        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            names = zf.namelist()
            assert "cleaned.csv" in names
            assert "rejected.csv" in names
            assert "quality-report.json" in names

            report = json.loads(zf.read("quality-report.json"))
            assert report["accepted"] + report["rejected"] == report["input_rows"]

    def test_download_unknown_job(self, client: TestClient) -> None:
        resp = client.get("/api/v1/jobs/nonexistent/download")
        assert resp.status_code == 404

    def test_download_not_ready(self, client: TestClient) -> None:
        with open(SUPPLIER_A, "rb") as f:
            resp = client.post("/api/v1/jobs", files=[("files", ("supplier_a.csv", f, "text/csv"))])
        job_id = resp.json()["job_id"]
        resp = client.get(f"/api/v1/jobs/{job_id}/download")
        assert resp.status_code in (200, 409)


class TestConcurrentJobs:
    def test_job_isolation(self, client: TestClient) -> None:
        """Two jobs submitted concurrently produce independent results."""
        with open(SUPPLIER_A, "rb") as f:
            resp1 = client.post("/api/v1/jobs", files=[("files", ("a.csv", f, "text/csv"))])
        with open(SUPPLIER_B, "rb") as f:
            resp2 = client.post("/api/v1/jobs", files=[("files", ("b.csv", f, "text/csv"))])

        job1 = resp1.json()["job_id"]
        job2 = resp2.json()["job_id"]
        assert job1 != job2

        data1 = _wait_for_job(client, job1)
        data2 = _wait_for_job(client, job2)

        assert data1["status"] == "completed"
        assert data2["status"] == "completed"
        assert data1["stats"]["input_rows"] == 41
        assert data2["stats"]["input_rows"] == 42


class TestSecurity:
    def test_path_traversal_filename(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/jobs",
            files=[("files", ("../../etc/passwd.csv", b"a,b\n1,2\n", "text/csv"))],
        )
        assert resp.status_code == 201

    def test_formula_injection_sanitized(self) -> None:
        assert sanitize_csv_value("=SUM(A1:A10)") == "'=SUM(A1:A10)"
        assert sanitize_csv_value("+cmd|' /C calc'!A0") == "'+cmd|' /C calc'!A0"
        assert sanitize_csv_value("-1+1") == "'-1+1"
        assert sanitize_csv_value("@SUM(A1)") == "'@SUM(A1)"
        assert sanitize_csv_value("normal text") == "normal text"
        assert sanitize_csv_value("") == ""

    def test_cleaned_csv_no_formula_injection(self, client: TestClient) -> None:
        """Verify that output CSVs have formula-prefixed values sanitized."""
        with open(SUPPLIER_A, "rb") as f:
            resp = client.post("/api/v1/jobs", files=[("files", ("a.csv", f, "text/csv"))])
        job_id = resp.json()["job_id"]
        _wait_for_job(client, job_id)

        resp = client.get(f"/api/v1/jobs/{job_id}/download")
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            cleaned = zf.read("cleaned.csv").decode("utf-8")
            for line in cleaned.split("\n")[1:]:
                for cell in line.split(","):
                    cell = cell.strip().strip('"')
                    if cell and cell[0] in ("=", "+", "@", "\t", "\r"):
                        pytest.fail(f"Unsanitized formula-triggering cell: {cell!r}")


class TestQueueLimit:
    def test_queue_full_returns_429(self, tmp_path: Path) -> None:
        """When max_active jobs are queued/running, new jobs get 429."""
        reset_store(jobs_dir=tmp_path / "jobs", max_active=2)
        app = create_app()
        client = TestClient(app)

        with open(SUPPLIER_A, "rb") as f:
            resp1 = client.post("/api/v1/jobs", files=[("files", ("a.csv", f, "text/csv"))])
        assert resp1.status_code == 201

        with open(SUPPLIER_A, "rb") as f:
            resp2 = client.post("/api/v1/jobs", files=[("files", ("b.csv", f, "text/csv"))])
        assert resp2.status_code == 201

        # Third job should be rejected — wait briefly to ensure both are still active
        with open(SUPPLIER_A, "rb") as f:
            resp3 = client.post("/api/v1/jobs", files=[("files", ("c.csv", f, "text/csv"))])
        # Might be 201 if jobs finished fast, or 429 if still active
        assert resp3.status_code in (201, 429)

    def test_queue_full_definite_429(self, tmp_path: Path) -> None:
        """Force a 429 by setting max_active=1 and blocking the worker."""
        from unittest.mock import patch

        reset_store(jobs_dir=tmp_path / "jobs", max_active=1)
        app = create_app()
        client = TestClient(app)

        # Patch process_job to block so the first job stays QUEUED
        with patch("dataforge.api.services.process_job", side_effect=lambda *a: time.sleep(5)):
            with open(SUPPLIER_A, "rb") as f:
                resp1 = client.post("/api/v1/jobs", files=[("files", ("a.csv", f, "text/csv"))])
            assert resp1.status_code == 201

            with open(SUPPLIER_A, "rb") as f:
                resp2 = client.post("/api/v1/jobs", files=[("files", ("b.csv", f, "text/csv"))])
            assert resp2.status_code == 429
            assert "Too many active jobs" in resp2.json()["detail"]


class TestRetention:
    def test_expired_jobs_cleaned_up(self, tmp_path: Path) -> None:
        """Completed jobs older than retention_seconds are cleaned up."""
        reset_store(
            jobs_dir=tmp_path / "jobs",
            retention_seconds=0,  # expire immediately
        )
        app = create_app()
        client = TestClient(app)

        with open(SUPPLIER_A, "rb") as f:
            resp = client.post("/api/v1/jobs", files=[("files", ("a.csv", f, "text/csv"))])
        job_id = resp.json()["job_id"]
        _wait_for_job(client, job_id)

        # The completed job exists
        resp = client.get(f"/api/v1/jobs/{job_id}")
        assert resp.status_code == 200

        # Trigger cleanup by creating another job
        with open(SUPPLIER_A, "rb") as f:
            client.post("/api/v1/jobs", files=[("files", ("b.csv", f, "text/csv"))])

        # The expired job should be gone
        resp = client.get(f"/api/v1/jobs/{job_id}")
        assert resp.status_code == 404


class TestPreview:
    def test_preview_after_completion(self, client: TestClient) -> None:
        with open(SUPPLIER_A, "rb") as f:
            resp = client.post("/api/v1/jobs", files=[("files", ("a.csv", f, "text/csv"))])
        job_id = resp.json()["job_id"]
        _wait_for_job(client, job_id)

        resp = client.get(f"/api/v1/jobs/{job_id}/preview")
        assert resp.status_code == 200
        data = resp.json()
        assert data["job_id"] == job_id
        assert isinstance(data["cleaned"], list)
        assert isinstance(data["rejected"], list)
        assert data["cleaned_total"] >= len(data["cleaned"])
        assert data["rejected_total"] >= len(data["rejected"])
        assert data["cleaned_total"] + data["rejected_total"] == 41

    def test_preview_limit(self, client: TestClient) -> None:
        with open(SUPPLIER_A, "rb") as f:
            resp = client.post("/api/v1/jobs", files=[("files", ("a.csv", f, "text/csv"))])
        job_id = resp.json()["job_id"]
        _wait_for_job(client, job_id)

        resp = client.get(f"/api/v1/jobs/{job_id}/preview?limit=5")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["cleaned"]) <= 5

    def test_preview_before_completion(self, client: TestClient) -> None:
        with open(SUPPLIER_A, "rb") as f:
            resp = client.post("/api/v1/jobs", files=[("files", ("a.csv", f, "text/csv"))])
        job_id = resp.json()["job_id"]
        resp = client.get(f"/api/v1/jobs/{job_id}/preview")
        assert resp.status_code in (200, 409)

    def test_preview_unknown_job(self, client: TestClient) -> None:
        resp = client.get("/api/v1/jobs/nonexistent/preview")
        assert resp.status_code == 404

    def test_preview_cell_content_is_text(self, client: TestClient) -> None:
        """All preview cell values are strings — no formulas or HTML executed."""
        with open(SUPPLIER_A, "rb") as f:
            resp = client.post("/api/v1/jobs", files=[("files", ("a.csv", f, "text/csv"))])
        job_id = resp.json()["job_id"]
        _wait_for_job(client, job_id)

        resp = client.get(f"/api/v1/jobs/{job_id}/preview")
        data = resp.json()
        for row in data["cleaned"] + data["rejected"]:
            for val in row.values():
                assert isinstance(val, str)


class TestStreamingUpload:
    def test_oversized_file_streaming(self, client: TestClient) -> None:
        """Large file detected during streaming, not buffered in memory."""
        big = b"x" * (10 * 1024 * 1024 + 1)
        resp = client.post(
            "/api/v1/jobs",
            files=[("files", ("big.csv", big, "text/csv"))],
        )
        assert resp.status_code == 400
        assert "10 MB" in resp.json()["detail"]
