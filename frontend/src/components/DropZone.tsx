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
    <div className="space-y-4">
      <div
        onDragOver={(e) => {
          e.preventDefault()
          if (!disabled) setDragOver(true)
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        className={cn(
          "flex flex-col items-center justify-center rounded-[20px] border border-dashed px-6 py-12 text-center transition-colors",
          dragOver && !disabled
            ? "border-emerald bg-pale"
            : "border-emerald/40 bg-gradient-to-b from-pale/80 to-white",
          disabled && "cursor-not-allowed opacity-60",
        )}
      >
        <span className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-pale text-emerald">
          <Upload className="h-6 w-6" aria-hidden />
        </span>
        <p className="text-base font-semibold text-navy">Drag & drop your files here</p>
        <p className="mt-1 max-w-sm text-sm text-slate">
          CSV or XLSX. Up to 3 files, 10 MB each. Column names are matched automatically.
        </p>
        <Button
          size="sm"
          onClick={handleBrowse}
          disabled={disabled}
          type="button"
          className="mt-5"
        >
          Browse files
        </Button>
      </div>

      {error && (
        <p role="alert" className="rounded-xl bg-destructive/10 px-3 py-2 text-sm font-medium text-destructive">
          {error}
        </p>
      )}

      {files.length > 0 && (
        <ul className="space-y-2">
          {files.map((file, i) => (
            <li
              key={`${file.name}-${i}`}
              className="flex items-center gap-3 rounded-2xl border border-border bg-white px-4 py-3"
            >
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-pale text-emerald">
                <FileSpreadsheet className="h-5 w-5" aria-hidden />
              </span>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-semibold text-navy">{file.name}</p>
                <p className="text-xs text-slate">
                  {`${(file.size / 1024).toFixed(1)} KB · Ready`}
                </p>
              </div>
              <button
                onClick={() => removeFile(i)}
                disabled={disabled}
                className="rounded-lg p-2 text-slate transition-colors hover:bg-destructive/10 hover:text-destructive disabled:opacity-50"
                type="button"
                aria-label={`Remove ${file.name}`}
              >
                <X className="h-4 w-4" />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
