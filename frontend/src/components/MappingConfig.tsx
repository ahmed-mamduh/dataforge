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
        setError("The configuration needs a mappings list. Leave this blank to use automatic matching.")
      } else {
        setError(null)
      }
    } catch {
      setError("This is not valid JSON. Check commas and quotes, or clear the field to use automatic matching.")
    }
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-border bg-white">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        className="flex w-full items-center gap-3 px-4 py-4 text-left transition-colors hover:bg-pale/60"
      >
        <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-pale text-emerald">
          <Settings2 className="h-4 w-4" aria-hidden />
        </span>
        <span className="min-w-0 flex-1">
          <span className="block text-sm font-semibold text-navy">Advanced Column Mapping</span>
          <span className="block text-xs text-slate">Optional. Automatic matching is used when this is empty.</span>
        </span>
        {open ? (
          <ChevronUp className="h-4 w-4 text-slate" aria-hidden />
        ) : (
          <ChevronDown className="h-4 w-4 text-slate" aria-hidden />
        )}
      </button>
      {open && (
        <div className="space-y-3 border-t border-border px-4 py-4">
          <p className="text-xs leading-relaxed text-slate">
            Paste a JSON mapping only when your column names do not match the built-in synonyms.
            Each entry maps a source header to a canonical field such as sku, price, or quantity.
          </p>
          <textarea
            value={value}
            onChange={(e) => handleChange(e.target.value)}
            disabled={disabled}
            placeholder={EXAMPLE_CONFIG}
            rows={8}
            aria-label="Column mapping JSON"
            className="w-full resize-y rounded-xl border border-border bg-canvas px-3 py-2 font-mono text-xs text-navy focus:outline-none focus:ring-2 focus:ring-emerald disabled:opacity-50"
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
