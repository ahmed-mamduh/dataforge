import { useState, useCallback } from "react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { Check, RotateCcw, Upload, ShieldCheck, FileSpreadsheet } from "lucide-react"
import { uploadFiles, type JobStatusResponse, ApiError } from "@/api/client"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { DropZone } from "@/components/DropZone"
import { MappingConfig } from "@/components/MappingConfig"
import { JobProgress } from "@/components/JobProgress"
import { ResultsSummary } from "@/components/ResultsSummary"
import { BrandLogo } from "@/components/BrandLogo"
import { cn } from "@/lib/utils"

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false, refetchOnWindowFocus: false },
  },
})

type AppState =
  | { step: "upload" }
  | { step: "processing"; jobId: string }
  | { step: "results"; jobData: JobStatusResponse }

const STEPS = [
  {
    id: "upload",
    label: "Upload",
    title: "Upload files",
    detail: "Add Excel (.xlsx) or CSV files. Up to 3 files, 10 MB each.",
    icon: Upload,
  },
  {
    id: "processing",
    label: "Process",
    title: "Clean and validate",
    detail: "Normalize values, flag invalid rows, and detect duplicates.",
    icon: ShieldCheck,
  },
  {
    id: "results",
    label: "Review & Download",
    title: "Review and download",
    detail: "Inspect accepted and rejected rows, then download the ZIP.",
    icon: FileSpreadsheet,
  },
] as const

function AppContent() {
  const [state, setState] = useState<AppState>({ step: "upload" })
  const [files, setFiles] = useState<File[]>([])
  const [mappingConfig, setMappingConfig] = useState("")
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = useCallback(async () => {
    if (files.length === 0) return
    setUploading(true)
    setError(null)
    try {
      const mapping = mappingConfig.trim() || undefined
      const result = await uploadFiles(files, mapping)
      setState({ step: "processing", jobId: result.job_id })
    } catch (e) {
      if (e instanceof ApiError) {
        setError(e.detail)
      } else {
        setError("Upload failed. Is the backend running?")
      }
    } finally {
      setUploading(false)
    }
  }, [files, mappingConfig])

  const handleComplete = useCallback((data: JobStatusResponse) => {
    setState({ step: "results", jobData: data })
  }, [])

  const handleReset = useCallback(() => {
    setState({ step: "upload" })
    setFiles([])
    setMappingConfig("")
    setError(null)
    queryClient.clear()
  }, [])

  const activeIndex = STEPS.findIndex((step) => step.id === state.step)

  return (
    <div className="flex min-h-screen flex-col overflow-x-hidden bg-canvas">
      <header className="sticky top-0 z-20 border-b border-white/70 bg-white/80 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-[1440px] items-center gap-4 px-4 sm:px-8">
          <BrandLogo />
          <span className="hidden border-l border-border pl-4 text-sm font-medium text-slate md:inline">
            Data Cleaning Studio
          </span>
          <nav aria-label="Workflow" className="ml-auto hidden items-center gap-1 lg:flex">
            {STEPS.map((step, index) => {
              const done = index < activeIndex
              const current = index === activeIndex
              return (
                <span
                  key={step.id}
                  className={cn(
                    "rounded-full px-3 py-1 text-xs font-semibold",
                    current && "bg-pale text-emerald",
                    done && "text-navy",
                    !current && !done && "text-slate",
                  )}
                  aria-current={current ? "step" : undefined}
                >
                  {index + 1}. {step.label}
                </span>
              )
            })}
          </nav>
          {state.step !== "upload" && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleReset}
              className="ml-auto gap-1.5 lg:ml-4"
            >
              <RotateCcw className="h-3.5 w-3.5" />
              New Job
            </Button>
          )}
        </div>
      </header>

      <main className="mx-auto w-full max-w-[1440px] flex-1 px-4 py-8 sm:px-8 sm:py-12">
        {state.step === "upload" && (
          <div className="mx-auto max-w-5xl space-y-8">
            <div className="space-y-4 text-center">
              <h1 className="text-4xl font-extrabold leading-[1.05] tracking-tight sm:text-6xl">
                <span className="block text-navy">Clean data.</span>
                <span className="block text-emerald">Confident decisions.</span>
              </h1>
              <p className="mx-auto max-w-2xl text-base leading-relaxed text-slate sm:text-lg">
                Upload Excel or CSV files, detect inconsistencies, remove duplicates,
                and download clean, validated results.
              </p>
            </div>

            <ol className="grid gap-3 md:grid-cols-3">
              {STEPS.map((step, index) => {
                const Icon = step.icon
                return (
                  <li
                    key={step.id}
                    className="flex gap-3 rounded-[20px] border border-white/80 bg-white/90 p-4 shadow-[var(--shadow-card)]"
                  >
                    <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-pale text-sm font-bold text-emerald">
                      {index + 1}
                    </span>
                    <span>
                      <span className="flex items-center gap-2 text-sm font-bold text-navy">
                        <Icon className="h-4 w-4 text-emerald" aria-hidden />
                        {step.title}
                      </span>
                      <span className="mt-1 block text-xs leading-relaxed text-slate">{step.detail}</span>
                    </span>
                  </li>
                )
              })}
            </ol>

            <Card>
              <CardContent className="space-y-5 p-5 sm:p-8">
                <div>
                  <h2 className="text-lg font-bold text-navy">Upload files</h2>
                  <p className="mt-1 text-sm text-slate">
                    Add up to three .csv or .xlsx files. Different column layouts are matched automatically.
                  </p>
                </div>
                <DropZone files={files} onFilesChange={setFiles} disabled={uploading} />
                <p className="text-xs leading-relaxed text-slate">
                  Supported formats are .csv and .xlsx, with a limit of 3 files and 10 MB each.
                  Rows that fail validation stay in the rejected report with a reason — they are not rewritten as accepted.
                </p>
                <MappingConfig
                  value={mappingConfig}
                  onChange={setMappingConfig}
                  disabled={uploading}
                />
                {error && (
                  <p role="alert" className="rounded-xl bg-destructive/10 p-3 text-sm text-destructive">
                    {error}
                  </p>
                )}
                <Button
                  onClick={handleSubmit}
                  disabled={files.length === 0 || uploading}
                  className="h-12 w-full text-base"
                  size="lg"
                >
                  {uploading ? "Uploading..." : "Start Cleaning"}
                </Button>
              </CardContent>
            </Card>

            <div className="grid gap-4 sm:grid-cols-3">
              <FeatureCard title="Multi-schema" desc="Matches common column names across supplier files." />
              <FeatureCard title="Validated" desc="Checks price, currency, quantity, and required fields." />
              <FeatureCard title="Traceable" desc="Every rejected row keeps its source file and reason." />
            </div>
          </div>
        )}

        {state.step === "processing" && (
          <div className="mx-auto max-w-2xl">
            <Card>
              <CardContent className="space-y-2 p-6 sm:p-8">
                <h1 className="text-2xl font-extrabold tracking-tight text-navy">Processing your files</h1>
                <p className="pb-4 text-sm text-slate">
                  DataForge is normalizing, validating, and checking for duplicates. This view updates from the job status.
                </p>
                <JobProgress jobId={state.jobId} onComplete={handleComplete} />
              </CardContent>
            </Card>
          </div>
        )}

        {state.step === "results" && (
          <ResultsSummary jobData={state.jobData} onNewJob={handleReset} />
        )}
      </main>

      <footer className="border-t border-border bg-white">
        <div className="mx-auto flex max-w-[1440px] flex-col gap-1 px-4 py-5 text-xs text-slate sm:flex-row sm:items-center sm:justify-between sm:px-8">
          <span className="inline-flex items-center gap-2 font-semibold text-navy">
            <Check className="h-3.5 w-3.5 text-emerald" aria-hidden />
            DataForge
          </span>
          <span>Portfolio demonstration. Sample data is synthetic.</span>
        </div>
      </footer>
    </div>
  )
}

function FeatureCard({ title, desc }: { title: string; desc: string }) {
  return (
    <div className="rounded-[18px] border border-border bg-white p-5 shadow-[var(--shadow-card)]">
      <p className="text-sm font-bold text-navy">{title}</p>
      <p className="mt-1 text-xs leading-relaxed text-slate">{desc}</p>
    </div>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  )
}
