import { useQuery } from "@tanstack/react-query"
import {
  CheckCircle2,
  XCircle,
  Copy,
  FileDown,
  BarChart3,
  AlertTriangle,
} from "lucide-react"
import { getJobReport, getDownloadUrl, type JobStatusResponse } from "@/api/client"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { DataPreview } from "./DataPreview"

interface ResultsSummaryProps {
  jobData: JobStatusResponse
}

export function ResultsSummary({ jobData }: ResultsSummaryProps) {
  const { data: report } = useQuery({
    queryKey: ["report", jobData.job_id],
    queryFn: () => getJobReport(jobData.job_id),
    enabled: jobData.status === "completed",
  })

  if (jobData.status === "failed") {
    return (
      <Card className="border-destructive/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-destructive text-lg">
            <XCircle className="h-5 w-5" />
            Processing Failed
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">{jobData.error}</p>
        </CardContent>
      </Card>
    )
  }

  const stats = report || jobData.stats
  if (!stats) return null

  const acceptRate = stats.input_rows > 0
    ? ((stats.accepted / stats.input_rows) * 100).toFixed(1)
    : "0"

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard
          icon={<BarChart3 className="h-4 w-4" />}
          label="Input Rows"
          value={stats.input_rows}
        />
        <StatCard
          icon={<CheckCircle2 className="h-4 w-4 text-success" />}
          label="Accepted"
          value={stats.accepted}
          accent="success"
        />
        <StatCard
          icon={<XCircle className="h-4 w-4 text-destructive" />}
          label="Rejected"
          value={stats.rejected}
          accent="destructive"
        />
        <StatCard
          icon={<Copy className="h-4 w-4 text-warning" />}
          label="Duplicates"
          value={stats.duplicates}
          accent="warning"
        />
      </div>

      <div className="flex items-center gap-3 flex-wrap">
        <Badge variant="success" className="text-sm px-3 py-1">
          {acceptRate}% acceptance rate
        </Badge>
        <a href={getDownloadUrl(jobData.job_id)} download>
          <Button size="sm" className="gap-2">
            <FileDown className="h-4 w-4" />
            Download ZIP
          </Button>
        </a>
      </div>

      {report?.reason_counts && Object.keys(report.reason_counts).length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-warning" />
              Rejection Reasons
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {Object.entries(report.reason_counts)
                .sort(([, a], [, b]) => b - a)
                .map(([reason, count]) => (
                  <div key={reason} className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">{reason}</span>
                    <Badge variant="outline">{count}</Badge>
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>
      )}

      {report?.per_file && Object.keys(report.per_file).length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Per-File Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {Object.entries(report.per_file).map(([file, info]) => (
                <div key={file} className="flex items-center justify-between text-sm">
                  <span className="font-mono text-xs truncate max-w-[200px]">{file}</span>
                  <span className="text-muted-foreground">{info.input_rows} rows</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <DataPreview jobId={jobData.job_id} />
    </div>
  )
}

function StatCard({
  icon,
  label,
  value,
  accent,
}: {
  icon: React.ReactNode
  label: string
  value: number
  accent?: string
}) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center gap-2 mb-1">
          {icon}
          <span className="text-xs text-muted-foreground">{label}</span>
        </div>
        <p
          className={`text-2xl font-bold ${
            accent === "success"
              ? "text-success"
              : accent === "destructive"
                ? "text-destructive"
                : accent === "warning"
                  ? "text-warning"
                  : ""
          }`}
        >
          {value.toLocaleString()}
        </p>
      </CardContent>
    </Card>
  )
}
