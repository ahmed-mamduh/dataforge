import { useEffect } from "react"
import { useQuery } from "@tanstack/react-query"
import { Loader2, CheckCircle2, XCircle, Clock } from "lucide-react"
import { getJobStatus, type JobStatusResponse } from "@/api/client"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { cn } from "@/lib/utils"

interface JobProgressProps {
  jobId: string
  onComplete: (data: JobStatusResponse) => void
}

const STATUS_CONFIG = {
  queued: {
    icon: Clock,
    label: "Queued",
    variant: "secondary" as const,
    description: "Waiting for a worker...",
    detail: "Your files are in the queue. Processing starts as soon as a worker is free.",
  },
  running: {
    icon: Loader2,
    label: "Processing",
    variant: "default" as const,
    description: "Cleaning and validating your data...",
    detail: "Rows are being normalized, validated, and checked for duplicates.",
  },
  completed: {
    icon: CheckCircle2,
    label: "Completed",
    variant: "success" as const,
    description: "Your data is ready!",
    detail: "Processing finished. Results are ready to review.",
  },
  failed: {
    icon: XCircle,
    label: "Failed",
    variant: "destructive" as const,
    description: "Something went wrong.",
    detail: "This job did not finish. Use New Job to upload the files again.",
  },
}

export function JobProgress({ jobId, onComplete }: JobProgressProps) {
  const { data } = useQuery({
    queryKey: ["job", jobId],
    queryFn: () => getJobStatus(jobId),
    refetchInterval: (query) => {
      const status = query.state.data?.status
      if (status === "completed" || status === "failed") return false
      return 1000
    },
  })

  useEffect(() => {
    if (data && (data.status === "completed" || data.status === "failed")) {
      onComplete(data)
    }
  }, [data, onComplete])

  const status = data?.status || "queued"
  const config = STATUS_CONFIG[status]
  const Icon = config.icon

  return (
    <div className="space-y-5">
      <div className="flex items-start gap-4">
        <span
          className={cn(
            "flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl",
            status === "failed" && "bg-destructive/10 text-destructive",
            status === "completed" && "bg-pale text-success",
            (status === "queued" || status === "running") && "bg-pale text-emerald",
          )}
        >
          <Icon
            className={cn("h-5 w-5", status === "running" && "motion-safe:animate-spin")}
            aria-hidden
          />
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-base font-semibold text-navy">{config.description}</span>
            <Badge variant={config.variant}>{config.label}</Badge>
          </div>
          <p className="mt-1 text-sm text-slate">{config.detail}</p>
          <p className="mt-2 text-xs text-slate">Job ID: {jobId}</p>
        </div>
      </div>

      {status === "queued" || status === "running" ? (
        <Progress indeterminate aria-label="Job in progress" />
      ) : status === "completed" ? (
        <Progress value={100} max={100} variant="success" />
      ) : (
        <Progress value={100} max={100} variant="destructive" aria-label="Job failed" />
      )}

      {data?.error && (
        <p role="alert" className="rounded-xl bg-destructive/10 p-3 text-sm text-destructive">
          {data.error}
        </p>
      )}
    </div>
  )
}
