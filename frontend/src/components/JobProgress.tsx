import { useEffect } from "react"
import { useQuery } from "@tanstack/react-query"
import { Loader2, CheckCircle2, XCircle, Clock } from "lucide-react"
import { getJobStatus, type JobStatusResponse } from "@/api/client"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"

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
  },
  running: {
    icon: Loader2,
    label: "Processing",
    variant: "default" as const,
    description: "Cleaning and validating your data...",
  },
  completed: {
    icon: CheckCircle2,
    label: "Completed",
    variant: "success" as const,
    description: "Your data is ready!",
  },
  failed: {
    icon: XCircle,
    label: "Failed",
    variant: "destructive" as const,
    description: "Something went wrong.",
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

  const progressValue =
    status === "queued" ? 15 : status === "running" ? 60 : status === "completed" ? 100 : 0

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <Icon
          className={`h-5 w-5 ${
            status === "running" ? "animate-spin text-primary" :
            status === "completed" ? "text-success" :
            status === "failed" ? "text-destructive" :
            "text-muted-foreground"
          }`}
        />
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium">{config.description}</span>
            <Badge variant={config.variant}>{config.label}</Badge>
          </div>
          <p className="text-xs text-muted-foreground mt-0.5">Job ID: {jobId}</p>
        </div>
      </div>
      <Progress value={progressValue} />

      {data?.error && (
        <p className="text-sm text-destructive bg-destructive/10 rounded-md p-3">
          {data.error}
        </p>
      )}
    </div>
  )
}
