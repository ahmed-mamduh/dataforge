const BASE = "/api/v1"

export interface JobCreatedResponse {
  job_id: string
  status: string
  files_received: number
}

export interface JobStatusResponse {
  job_id: string
  status: "queued" | "running" | "completed" | "failed"
  files: string[]
  stats: JobStats | null
  error: string | null
}

export interface JobStats {
  input_rows: number
  accepted: number
  rejected: number
  duplicates: number
  reason_counts: Record<string, number>
  per_file: Record<string, { input_rows: number; mapped_columns: string[] }>
}

export interface PreviewResponse {
  job_id: string
  cleaned: Record<string, string>[]
  rejected: Record<string, string>[]
  cleaned_total: number
  rejected_total: number
}

export interface QualityReport {
  input_rows: number
  accepted: number
  rejected: number
  duplicates: number
  reason_counts: Record<string, number>
  per_file: Record<string, { input_rows: number; mapped_columns: string[] }>
}

class ApiError extends Error {
  status: number
  detail: string

  constructor(status: number, detail: string) {
    super(detail)
    this.name = "ApiError"
    this.status = status
    this.detail = detail
  }
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }))
    throw new ApiError(res.status, body.detail || res.statusText)
  }
  return res.json()
}

export async function uploadFiles(
  files: File[],
  mappingConfig?: string,
): Promise<JobCreatedResponse> {
  const form = new FormData()
  for (const file of files) {
    form.append("files", file)
  }
  if (mappingConfig) {
    form.append("mapping_config", mappingConfig)
  }
  const res = await fetch(`${BASE}/jobs`, { method: "POST", body: form })
  return handleResponse<JobCreatedResponse>(res)
}

export async function getJobStatus(jobId: string): Promise<JobStatusResponse> {
  const res = await fetch(`${BASE}/jobs/${jobId}`)
  return handleResponse<JobStatusResponse>(res)
}

export async function getJobReport(jobId: string): Promise<QualityReport> {
  const res = await fetch(`${BASE}/jobs/${jobId}/report`)
  return handleResponse<QualityReport>(res)
}

export async function getJobPreview(
  jobId: string,
  limit = 100,
): Promise<PreviewResponse> {
  const res = await fetch(`${BASE}/jobs/${jobId}/preview?limit=${limit}`)
  return handleResponse<PreviewResponse>(res)
}

export function getDownloadUrl(jobId: string): string {
  return `${BASE}/jobs/${jobId}/download`
}

export { ApiError }
