import { useCallback, useState, type DragEvent } from "react"
import { Upload, X, FileSpreadsheet } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"

const ALLOWED_EXTENSIONS = [".csv", ".xlsx"]
const MAX_FILE_SIZE = 10 * 1024 * 1024
const MAX_FILES = 3

interface DropZoneProps {
  files: File[]
  onFilesChange: (files: File[]) => void
  disabled?: boolean
}

export function DropZone({ files, onFilesChange, disabled }: DropZoneProps) {
  const [dragOver, setDragOver] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const validateFiles = useCallback((incoming: File[]): File[] | null => {
    const total = files.length + incoming.length
    if (total > MAX_FILES) {
      setError(`Maximum ${MAX_FILES} files allowed`)
      return null
    }
    for (const f of incoming) {
      const ext = f.name.slice(f.name.lastIndexOf(".")).toLowerCase()
      if (!ALLOWED_EXTENSIONS.includes(ext)) {
        setError(`Unsupported file type: ${ext}. Use .csv or .xlsx`)
        return null
      }
      if (f.size > MAX_FILE_SIZE) {
        setError(`${f.name} exceeds 10 MB limit`)
        return null
      }
      if (f.size === 0) {
        setError(`${f.name} is empty`)
        return null
      }
    }
    setError(null)
    return incoming
  }, [files.length])

  const handleDrop = useCallback(
    (e: DragEvent) => {
      e.preventDefault()
      setDragOver(false)
      if (disabled) return
      const dropped = Array.from(e.dataTransfer.files)
      const valid = validateFiles(dropped)
      if (valid) onFilesChange([...files, ...valid])
    },
    [files, onFilesChange, disabled, validateFiles],
  )

  const handleBrowse = useCallback(() => {
    const input = document.createElement("input")
    input.type = "file"
    input.multiple = true
    input.accept = ALLOWED_EXTENSIONS.join(",")
    input.onchange = () => {
      const selected = Array.from(input.files || [])
      const valid = validateFiles(selected)
      if (valid) onFilesChange([...files, ...valid])
    }
    input.click()
  }, [files, onFilesChange, validateFiles])

  const removeFile = useCallback(
    (index: number) => {
      onFilesChange(files.filter((_, i) => i !== index))
      setError(null)
    },
    [files, onFilesChange],
  )

  return (
    <div className="space-y-3">
      <div
        onDragOver={(e) => {
          e.preventDefault()
          if (!disabled) setDragOver(true)
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        className={cn(
          "flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 transition-colors",
          dragOver && !disabled
            ? "border-primary bg-primary/5"
            : "border-border hover:border-primary/50",
          disabled && "opacity-50 cursor-not-allowed",
        )}
      >
        <Upload className="h-10 w-10 text-muted-foreground mb-3" />
        <p className="text-sm font-medium text-foreground mb-1">
          Drag & drop your files here
        </p>
        <p className="text-xs text-muted-foreground mb-4">
          CSV or XLSX — up to 3 files, 10 MB each
        </p>
        <Button
          variant="outline"
          size="sm"
          onClick={handleBrowse}
          disabled={disabled}
          type="button"
        >
          Browse files
        </Button>
      </div>

      {error && (
        <p className="text-sm text-destructive font-medium">{error}</p>
      )}

      {files.length > 0 && (
        <div className="space-y-2">
          {files.map((file, i) => (
            <div
              key={`${file.name}-${i}`}
              className="flex items-center gap-3 rounded-lg border bg-card p-3"
            >
              <FileSpreadsheet className="h-5 w-5 text-primary shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{file.name}</p>
                <p className="text-xs text-muted-foreground">
                  {(file.size / 1024).toFixed(1)} KB
                </p>
              </div>
              <button
                onClick={() => removeFile(i)}
                disabled={disabled}
                className="text-muted-foreground hover:text-destructive transition-colors"
                type="button"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
