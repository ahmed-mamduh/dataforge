import { useState, useCallback } from "react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { Database, RotateCcw } from "lucide-react"
import { uploadFiles, type JobStatusResponse, ApiError } from "@/api/client"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { DropZone } from "@/components/DropZone"
import { MappingConfig } from "@/components/MappingConfig"
import { JobProgress } from "@/components/JobProgress"
import { ResultsSummary } from "@/components/ResultsSummary"

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false, refetchOnWindowFocus: false },
  },
})

type AppState =
  | { step: "upload" }
  | { step: "processing"; jobId: string }
  | { step: "results"; jobData: JobStatusResponse }

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

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-card/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 h-14 flex items-center gap-3">
          <Database className="h-5 w-5 text-primary" />
          <h1 className="text-base font-semibold tracking-tight">DataForge</h1>
          <span className="text-xs text-muted-foreground hidden sm:inline">
            CSV & Excel Cleaning Studio
          </span>
          {state.step !== "upload" && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleReset}
              className="ml-auto gap-1.5"
            >
              <RotateCcw className="h-3.5 w-3.5" />
              New Job
            </Button>
          )}
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-8">
        {state.step === "upload" && (
          <div className="max-w-2xl mx-auto space-y-6">
            <div className="text-center space-y-2">
              <h2 className="text-2xl font-bold tracking-tight sm:text-3xl">
                Clean your data
              </h2>
              <p className="text-muted-foreground text-sm sm:text-base">
                Upload CSV or Excel files. DataForge normalizes, validates,
                deduplicates, and exports clean data with a full audit trail.
              </p>
            </div>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Upload Files</CardTitle>
                <CardDescription>
                  Select up to 3 files with different column schemas — mappings are auto-detected.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <DropZone
                  files={files}
                  onFilesChange={setFiles}
                  disabled={uploading}
                />
                <MappingConfig
                  value={mappingConfig}
                  onChange={setMappingConfig}
                  disabled={uploading}
                />

                {error && (
                  <p className="text-sm text-destructive bg-destructive/10 rounded-md p-3">
                    {error}
                  </p>
                )}

                <Button
                  onClick={handleSubmit}
                  disabled={files.length === 0 || uploading}
                  className="w-full"
                  size="lg"
                >
                  {uploading ? "Uploading..." : "Start Cleaning"}
                </Button>
              </CardContent>
            </Card>

            <div className="grid grid-cols-3 gap-4 text-center">
              <FeatureCard title="Multi-Schema" desc="Auto-detects column mappings" />
              <FeatureCard title="Validated" desc="Price, currency, quantity checks" />
              <FeatureCard title="Deduplicated" desc="Composite key matching" />
            </div>
          </div>
        )}

        {state.step === "processing" && (
          <div className="max-w-2xl mx-auto">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Processing</CardTitle>
              </CardHeader>
              <CardContent>
                <JobProgress jobId={state.jobId} onComplete={handleComplete} />
              </CardContent>
            </Card>
          </div>
        )}

        {state.step === "results" && (
          <ResultsSummary jobData={state.jobData} />
        )}
      </main>

      <footer className="border-t mt-auto">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-4 text-center text-xs text-muted-foreground">
          DataForge — Portfolio demonstration. All data is synthetic.
        </div>
      </footer>
    </div>
  )
}

function FeatureCard({ title, desc }: { title: string; desc: string }) {
  return (
    <div className="rounded-lg border p-4">
      <p className="text-sm font-medium">{title}</p>
      <p className="text-xs text-muted-foreground mt-1">{desc}</p>
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
