import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"
import { uploadFiles, getJobStatus, getJobPreview, getDownloadUrl, ApiError } from "./client"

const mockFetch = vi.fn()

beforeEach(() => {
  vi.stubGlobal("fetch", mockFetch)
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe("uploadFiles", () => {
  it("sends files as FormData and returns job response", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ job_id: "abc123", status: "queued", files_received: 1 }),
    })

    const file = new File(["data"], "test.csv", { type: "text/csv" })
    const result = await uploadFiles([file])

    expect(result.job_id).toBe("abc123")
    expect(result.files_received).toBe(1)
    expect(mockFetch).toHaveBeenCalledWith("/api/v1/jobs", expect.objectContaining({ method: "POST" }))
  })

  it("includes mapping_config when provided", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ job_id: "x", status: "queued", files_received: 1 }),
    })

    const file = new File(["data"], "test.csv", { type: "text/csv" })
    await uploadFiles([file], '{"mappings":[]}')

    const formData = mockFetch.mock.calls[0][1].body as FormData
    expect(formData.get("mapping_config")).toBe('{"mappings":[]}')
  })

  it("throws ApiError on failure", async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 400,
      statusText: "Bad Request",
      json: () => Promise.resolve({ detail: "File too large" }),
    })

    const file = new File(["data"], "test.csv")
    try {
      await uploadFiles([file])
      expect.fail("Should have thrown")
    } catch (e) {
      expect(e).toBeInstanceOf(ApiError)
      expect((e as ApiError).status).toBe(400)
      expect((e as ApiError).detail).toBe("File too large")
    }
  })
})

describe("getJobStatus", () => {
  it("returns job status", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({
          job_id: "abc",
          status: "completed",
          files: ["a.csv"],
          stats: { input_rows: 10, accepted: 8, rejected: 2, duplicates: 0, reason_counts: {}, per_file: {} },
          error: null,
        }),
    })

    const result = await getJobStatus("abc")
    expect(result.status).toBe("completed")
    expect(result.stats?.accepted).toBe(8)
  })
})

describe("getJobPreview", () => {
  it("fetches preview with limit", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({
          job_id: "abc",
          cleaned: [{ sku: "SKU1" }],
          rejected: [],
          cleaned_total: 1,
          rejected_total: 0,
        }),
    })

    const result = await getJobPreview("abc", 50)
    expect(result.cleaned).toHaveLength(1)
    expect(mockFetch).toHaveBeenCalledWith("/api/v1/jobs/abc/preview?limit=50")
  })
})

describe("getDownloadUrl", () => {
  it("returns correct URL", () => {
    expect(getDownloadUrl("xyz")).toBe("/api/v1/jobs/xyz/download")
  })
})

describe("ApiError", () => {
  it("captures status and detail", () => {
    const err = new ApiError(429, "Too many requests")
    expect(err.status).toBe(429)
    expect(err.detail).toBe("Too many requests")
    expect(err.message).toBe("Too many requests")
    expect(err.name).toBe("ApiError")
  })
})
