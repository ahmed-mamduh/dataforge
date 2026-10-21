import { useState } from "react"
import { Settings2, ChevronDown, ChevronUp } from "lucide-react"
import { Button } from "@/components/ui/button"

interface MappingConfigProps {
  value: string
  onChange: (v: string) => void
  disabled?: boolean
}

const EXAMPLE_CONFIG = JSON.stringify(
  {
    mappings: [
      {
        mapping: {
          "Your SKU Column": "sku",
          "Your Name Column": "product_name",
          "Your Category": "category",
          "Your Price": "price",
          "Your Currency": "currency",
          "Your Qty": "quantity",
          "Your Supplier": "supplier",
          "Your Description": "description",
        },
      },
    ],
  },
  null,
  2,
)

export function MappingConfig({ value, onChange, disabled }: MappingConfigProps) {
  const [open, setOpen] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleChange = (raw: string) => {
    onChange(raw)
    if (!raw.trim()) {
      setError(null)
      return
    }
    try {
      const parsed = JSON.parse(raw)
      if (!parsed.mappings || !Array.isArray(parsed.mappings)) {
        setError("JSON must have a 'mappings' array")
      } else {
        setError(null)
      }
    } catch {
      setError("Invalid JSON")
    }
  }

  return (
    <div className="rounded-lg border bg-card">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 w-full p-4 text-left hover:bg-accent/50 transition-colors rounded-lg"
      >
        <Settings2 className="h-4 w-4 text-muted-foreground" />
        <span className="text-sm font-medium flex-1">
          Custom column mapping
        </span>
        <span className="text-xs text-muted-foreground mr-2">Optional</span>
        {open ? (
          <ChevronUp className="h-4 w-4 text-muted-foreground" />
        ) : (
          <ChevronDown className="h-4 w-4 text-muted-foreground" />
        )}
      </button>
      {open && (
        <div className="px-4 pb-4 space-y-3">
          <p className="text-xs text-muted-foreground">
            Provide a JSON mapping if your columns don't match the defaults.
            Leave empty for auto-detection.
          </p>
          <textarea
            value={value}
            onChange={(e) => handleChange(e.target.value)}
            disabled={disabled}
            placeholder={EXAMPLE_CONFIG}
            rows={8}
            className="w-full rounded-md border bg-background px-3 py-2 text-xs font-mono resize-y focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
          />
          {error && <p className="text-xs text-destructive">{error}</p>}
          {!value.trim() && (
            <Button
              variant="ghost"
              size="sm"
              type="button"
              onClick={() => onChange(EXAMPLE_CONFIG)}
              disabled={disabled}
            >
              Load example
            </Button>
          )}
        </div>
      )}
    </div>
  )
}
