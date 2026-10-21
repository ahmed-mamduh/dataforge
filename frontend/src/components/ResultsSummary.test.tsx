import { render, screen, cleanup } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { describe, it, expect, vi, afterEach } from "vitest"
import { ResultsSummary } from "./ResultsSummary"
import type { JobStatusResponse } from "@/api/client"

vi.mock("@/api/client", async () => {
  const actual = await vi.importActual<typeof import("@/api/client")>("@/api/client")
  return {
    ...actual,
    getJobReport: vi.fn().mockResolvedValue({
      input_rows: 83,
      accepted: 73,
      rejected: 10,
      duplicates: 2,
      reason_counts: { invalid_price: 2, duplicate: 2, missing_required: 3 },
      per_file: {
        "supplier_a.csv": { input_rows: 41, mapped_columns: [] },
        "supplier_b.csv": { input_rows: 42, mapped_columns: [] },
      },
    }),
    getJobPreview: vi.fn().mockResolvedValue({
      job_id: "test123",
      cleaned: [{ sku: "SKU001", product_name: "Widget" }],
      rejected: [{ sku: "", product_name: "", _rejection_reasons: "missing_required" }],
      cleaned_total: 73,
      rejected_total: 10,
    }),
  }
})

function renderWithQuery(ui: React.ReactElement) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false, refetchOnWindowFocus: false } },
  })
  return render(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>)
}

const completedJob: JobStatusResponse = {
  job_id: "test123",
  status: "completed",
  files: ["supplier_a.csv", "supplier_b.csv"],
  stats: {
    input_rows: 83,
    accepted: 73,
    rejected: 10,
    duplicates: 2,
    reason_counts: {},
    per_file: {},
  },
  error: null,
}

const failedJob: JobStatusResponse = {
  job_id: "fail456",
  status: "failed",
  files: ["bad.csv"],
  stats: null,
  error: "Pipeline crashed",
}

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

describe("ResultsSummary", () => {
  it("shows stat cards for completed job", () => {
    renderWithQuery(<ResultsSummary jobData={completedJob} />)

    expect(screen.getByText("Input Rows")).toBeInTheDocument()
    expect(screen.getByText("83")).toBeInTheDocument()
    expect(screen.getByText("73")).toBeInTheDocument()
    expect(screen.getByText("10")).toBeInTheDocument()
    expect(screen.getByText("2")).toBeInTheDocument()
  })

  it("shows correct acceptance rate", () => {
    renderWithQuery(<ResultsSummary jobData={completedJob} />)
    expect(screen.getByText("88.0% acceptance rate")).toBeInTheDocument()
  })

  it("has download button with correct URL", () => {
    renderWithQuery(<ResultsSummary jobData={completedJob} />)
    const link = screen.getByRole("link")
    expect(link).toHaveAttribute("href", "/api/v1/jobs/test123/download")
  })

  it("shows failure message for failed job", () => {
    renderWithQuery(<ResultsSummary jobData={failedJob} />)
    expect(screen.getByText("Processing Failed")).toBeInTheDocument()
    expect(screen.getByText("Pipeline crashed")).toBeInTheDocument()
  })

  it("shows rejection reasons after report loads", async () => {
    renderWithQuery(<ResultsSummary jobData={completedJob} />)
    expect(await screen.findByText("Rejection Reasons")).toBeInTheDocument()
    expect(await screen.findByText("invalid_price")).toBeInTheDocument()
    expect(await screen.findByText("missing_required")).toBeInTheDocument()
  })

  it("shows per-file breakdown", async () => {
    renderWithQuery(<ResultsSummary jobData={completedJob} />)
    expect(await screen.findByText("supplier_a.csv")).toBeInTheDocument()
    expect(await screen.findByText("41 rows")).toBeInTheDocument()
    expect(await screen.findByText("supplier_b.csv")).toBeInTheDocument()
    expect(await screen.findByText("42 rows")).toBeInTheDocument()
  })
})
