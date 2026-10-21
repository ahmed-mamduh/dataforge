import { useQuery } from "@tanstack/react-query"
import {
  CheckCircle2,
  XCircle,
  Copy,
  FileDown,
  Rows3,
  AlertTriangle,
} from "lucide-react"
import { getJobReport, getDownloadUrl, type JobStatusResponse } from "@/api/client"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { DataPreview } from "./DataPreview"
import { cn } from "@/lib/utils"

interface ResultsSummaryProps {
  jobData: JobStatusResponse
  onNewJob?: () => void
}

export function ResultsSummary({ jobData, onNewJob }: ResultsSummaryProps) {
  const { data: report } = useQuery({
    queryKey: ["report", jobData.job_id],
    queryFn: () => getJobReport(jobData.job_id),
    enabled: jobData.status === "completed",
  })

  if (jobData.status === "failed") {
    return (
      <Card className="mx-auto max-w-2xl border-destructive/40">
        <CardContent className="space-y-4 p-6 sm:p-8">
          <h1 className="flex items-center gap-2 text-2xl font-extrabold text-destructive">
            <XCircle className="h-6 w-6" aria-hidden />
            Processing Failed
          </h1>
          <p className="text-sm text-slate">{jobData.error}</p>
          {onNewJob && (
            <Button variant="outline" onClick={onNewJob}>
              Start New Job
            </Button>
          )}
        </CardContent>
      </Card>
    )
  }

  const stats = report || jobData.stats
  if (!stats) return null

  const acceptRate = stats.input_rows > 0
    ? ((stats.accepted / stats.input_rows) * 100).toFixed(1)
    : "0"
  const acceptedShare = stats.input_rows > 0 ? (stats.accepted / stats.input_rows) * 100 : 0
  const rejectedShare = stats.input_rows > 0 ? (stats.rejected / stats.input_rows) * 100 : 0

  const fileCount = jobData.files.length

  return (
    <div className="space-y-6">
      <div className="rounded-[24px] border border-white bg-white/95 p-5 shadow-[var(--shadow-card)] sm:p-8">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
          <div className="space-y-2">
            <h1 className="text-3xl font-extrabold tracking-tight text-navy sm:text-4xl">
              Data Cleaning Complete
            </h1>
            <p className="text-sm text-slate">
              {fileCount} file{fileCount === 1 ? "" : "s"} processed. Your processed files are ready to review and download.
            </p>
          </div>
          <span className="inline-flex h-fit items-center gap-1.5 self-start rounded-full bg-pale px-3 py-1.5 text-sm font-semibold text-emerald">
            <CheckCircle2 className="h-4 w-4" aria-hidden />
            Ready to Download
          </span>
        </div>

        <div className="mt-6 grid grid-cols-2 gap-3 lg:grid-cols-4">
          <StatCard icon={<Rows3 className="h-4 w-4" />} label="Input Rows" value={stats.input_rows} tone="navy" />
          <StatCard icon={<CheckCircle2 className="h-4 w-4" />} label="Accepted" value={stats.accepted} tone="emerald" />
          <StatCard icon={<XCircle className="h-4 w-4" />} label="Rejected" value={stats.rejected} tone="red" />
          <StatCard icon={<Copy className="h-4 w-4" />} label="Duplicates" value={stats.duplicates} tone="amber" />
        </div>

        <div className="mt-6 flex flex-col gap-3 border-t border-border pt-5 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-xs leading-relaxed text-slate">
            The ZIP contains cleaned.csv, rejected.csv, and quality-report.json.
          </p>
          <div className="flex flex-col gap-2 sm:flex-row">
            <a href={getDownloadUrl(jobData.job_id)} download>
              <Button size="lg" className="h-11 w-full gap-2 px-5 sm:w-auto">
                <FileDown className="h-4 w-4" aria-hidden />
                Download Cleaned Data
              </Button>
            </a>
            {onNewJob && (
              <Button variant="outline" size="lg" className="h-11" onClick={onNewJob}>
                Start New Job
              </Button>
            )}
          </div>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-1">
          <CardContent className="space-y-4 p-5">
            <h2 className="text-sm font-bold text-navy">Quality Summary</h2>
            <p className="text-3xl font-extrabold tracking-tight text-emerald">{acceptRate}%</p>
            <p className="text-sm text-slate">{acceptRate}% acceptance rate</p>
            <ul className="space-y-2 text-sm text-navy">
              <li className="flex items-start gap-2">
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald" aria-hidden />
                {stats.accepted} rows accepted
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald" aria-hidden />
                {stats.duplicates} duplicate rows flagged
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald" aria-hidden />
                {stats.rejected} rows kept in the rejection report
              </li>
            </ul>
            <div
              className="flex h-3 overflow-hidden rounded-full bg-muted"
              role="img"
              aria-label={`${acceptRate} percent of input rows were accepted. ${stats.rejected} rows were rejected.`}
            >
              <span className="bg-emerald" style={{ width: `${acceptedShare}%` }} />
              <span className="bg-destructive/80" style={{ width: `${rejectedShare}%` }} />
            </div>
            <div className="flex justify-between text-xs text-slate">
              <span>Accepted {stats.accepted}</span>
              <span>Rejected {stats.rejected}</span>
            </div>
            <p className="text-xs leading-relaxed text-slate">
              Acceptance rate is accepted rows divided by input rows. Rejected rows were not accepted.
            </p>
          </CardContent>
        </Card>

        {report?.reason_counts && Object.keys(report.reason_counts).length > 0 && (
          <Card>
            <CardContent className="space-y-3 p-5">
              <h2 className="flex items-center gap-2 text-sm font-bold text-navy">
                <AlertTriangle className="h-4 w-4 text-warning" aria-hidden />
                Rejection Reasons
              </h2>
              {Object.entries(report.reason_counts)
                .sort(([, a], [, b]) => b - a)
                .map(([reason, count]) => (
                  <div key={reason} className="flex items-center justify-between gap-3 text-sm">
                    <span className="truncate text-slate">{reason}</span>
                    <span className="rounded-full border border-border px-2 py-0.5 text-xs font-semibold text-navy">
                      {count}
                    </span>
                  </div>
                ))}
            </CardContent>
          </Card>
        )}

        {report?.per_file && Object.keys(report.per_file).length > 0 && (
          <Card>
            <CardContent className="space-y-3 p-5">
              <h2 className="text-sm font-bold text-navy">Per-file breakdown</h2>
              {Object.entries(report.per_file).map(([file, info]) => (
                <div key={file} className="flex items-center justify-between gap-3 text-sm">
                  <span className="truncate font-medium text-navy">{file}</span>
                  <span className="shrink-0 text-slate">{info.input_rows} rows</span>
                </div>
              ))}
            </CardContent>
          </Card>
        )}
      </div>

      <DataPreview jobId={jobData.job_id} />
    </div>
  )
}

function StatCard({
  icon,
  label,
  value,
  tone,
}: {
  icon: React.ReactNode
  label: string
  value: number
  tone: "navy" | "emerald" | "red" | "amber"
}) {
  return (
    <Card className="h-full border-border/80 bg-canvas/60 shadow-none">
      <CardContent className="flex h-full flex-col justify-between gap-3 p-4">
        <div className="flex items-center gap-2">
          <span
            className={cn(
              "flex h-8 w-8 items-center justify-center rounded-xl",
              tone === "navy" && "bg-navy/5 text-navy",
              tone === "emerald" && "bg-pale text-emerald",
              tone === "red" && "bg-destructive/10 text-destructive",
              tone === "amber" && "bg-warning/10 text-warning",
            )}
          >
            {icon}
          </span>
          <span className="text-xs font-semibold uppercase tracking-wide text-slate">{label}</span>
        </div>
        <p
          className={cn(
            "text-3xl font-extrabold tracking-tight",
            tone === "navy" && "text-navy",
            tone === "emerald" && "text-emerald",
            tone === "red" && "text-destructive",
            tone === "amber" && "text-warning",
          )}
        >
          {value.toLocaleString()}
        </p>
      </CardContent>
    </Card>
  )
}
