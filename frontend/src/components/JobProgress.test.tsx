import { render, screen, cleanup } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { describe, it, expect, vi, afterEach } from "vitest"
import type { JobStatusResponse } from "@/api/client"

vi.mock("@/api/client", async () => {
  const actual = await vi.importActual<typeof import("@/api/client")>("@/api/client")
  return {
    ...actual,
    getJobStatus: vi.fn(),
  }
})

import { getJobStatus } from "@/api/client"
import { JobProgress } from "./JobProgress"

const onComplete = vi.fn()

function renderProgress(status: JobStatusResponse["status"], error: string | null = null) {
  vi.mocked(getJobStatus).mockResolvedValue({
    job_id: "job-1",
    status,
    files: ["a.csv"],
    stats: null,
    error,
  })

  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <JobProgress jobId="job-1" onComplete={onComplete} />
    </QueryClientProvider>,
  )
}

describe("JobProgress", () => {
  afterEach(() => {
    cleanup()
    vi.clearAllMocks()
  })

  it("shows an indeterminate progress bar while running", async () => {
    renderProgress("running")
    const bar = await screen.findByRole("progressbar")
    expect(bar).toHaveAttribute("aria-busy", "true")
    expect(bar).not.toHaveAttribute("aria-valuenow")
  })

  it("shows a completed progress bar at 100%", async () => {
    renderProgress("completed")
    await screen.findByText("Completed")
    const bar = screen.getByRole("progressbar")
    expect(bar).toHaveAttribute("aria-valuenow", "100")
    expect(bar).not.toHaveAttribute("aria-busy")
  })

  it("shows a failed state and error message", async () => {
    renderProgress("failed", "Worker crashed")
    expect(await screen.findByText("Failed")).toBeInTheDocument()
    expect(await screen.findByText("Worker crashed")).toBeInTheDocument()
    const bar = screen.getByRole("progressbar")
    expect(bar).toHaveAttribute("aria-label", "Job failed")
  })
})
