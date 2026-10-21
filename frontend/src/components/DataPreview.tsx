import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { ChevronLeft, ChevronRight } from "lucide-react"
import { getJobPreview } from "@/api/client"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface DataPreviewProps {
  jobId: string
}

const PAGE_SIZE = 20

export function DataPreview({ jobId }: DataPreviewProps) {
  const { data, isLoading } = useQuery({
    queryKey: ["preview", jobId],
    queryFn: () => getJobPreview(jobId, 100),
  })

  if (isLoading || !data) {
    return (
      <div className="rounded-[18px] border border-border bg-white py-10 text-center text-sm text-slate">
        Loading preview...
      </div>
    )
  }

  return (
    <section className="space-y-4">
      <div>
        <h2 className="text-3xl font-extrabold leading-tight tracking-tight sm:text-4xl">
          <span className="text-navy">From flagged rows to </span>
          <span className="text-emerald">clean, reliable results</span>
        </h2>
        <p className="mt-2 max-w-3xl text-sm leading-relaxed text-slate sm:text-base">
          Rejected rows are the records the engine flagged. Cleaned rows are the records that passed validation.
          Both come from the job preview — the left table is not a reconstruction of the original file.
        </p>
      </div>
      <div className="grid gap-4 xl:grid-cols-2">
        <RecordTable
          title="Rejected · flagged rows"
          tone="danger"
          rows={data.rejected}
          total={data.rejected_total}
        />
        <RecordTable
          title="Cleaned · validated rows"
          tone="success"
          rows={data.cleaned}
          total={data.cleaned_total}
        />
      </div>
    </section>
  )
}

function RecordTable({
  title,
  tone,
  rows,
  total,
}: {
  title: string
  tone: "success" | "danger"
  rows: Record<string, string>[]
  total: number
}) {
  const [page, setPage] = useState(0)
  const columns = rows.length > 0 ? Object.keys(rows[0]) : []
  const pageStart = page * PAGE_SIZE
  const pageRows = rows.slice(pageStart, pageStart + PAGE_SIZE)
  const totalPages = Math.max(1, Math.ceil(rows.length / PAGE_SIZE))

  return (
    <div
      className={cn(
        "overflow-hidden rounded-[18px] border bg-white shadow-[var(--shadow-card)]",
        tone === "success" ? "border-emerald/25" : "border-destructive/25",
      )}
    >
      <div className="flex items-center justify-between gap-3 px-4 pt-4">
        <h3
          className={cn(
            "rounded-full px-3 py-1 text-xs font-bold tracking-wide",
            tone === "success" ? "bg-pale text-emerald" : "bg-destructive/10 text-destructive",
          )}
        >
          {title}
        </h3>
        <span
          className={cn(
            "flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold",
            tone === "success" ? "bg-pale text-emerald" : "bg-destructive/10 text-destructive",
          )}
          aria-label={`${total} rows`}
        >
          {total > 99 ? "99+" : total}
        </span>
      </div>
      {rows.length === 0 ? (
        <p className="px-4 py-8 text-center text-sm text-slate">No records in this preview.</p>
      ) : (
        <>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[28rem] text-left text-xs">
              <thead className="bg-canvas">
                <tr className="border-b border-border">
                  {columns.map((col) => (
                    <th key={col} scope="col" className="whitespace-nowrap px-3 py-2.5 font-semibold text-slate">
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {pageRows.map((row, i) => (
                  <tr
                    key={pageStart + i}
                    className={cn(
                      "border-b border-border/70 last:border-0",
                      tone === "success" ? "hover:bg-pale/60" : "bg-destructive/[0.03] hover:bg-destructive/[0.07]",
                    )}
                  >
                    {columns.map((col) => {
                      const value = row[col] ?? ""
                      return (
                        <td key={col} className="max-w-[14rem] truncate px-3 py-2.5 text-navy" title={value}>
                          {value}
                        </td>
                      )
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="flex items-center justify-between border-t border-border px-3 py-2 text-xs text-slate">
            <span>
              {pageStart + 1}–{Math.min(pageStart + PAGE_SIZE, rows.length)} of {rows.length}
              {total > rows.length ? ` shown (${total} total)` : ""}
            </span>
            {totalPages > 1 && (
              <div className="flex gap-1">
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8"
                  onClick={() => setPage((current) => Math.max(0, current - 1))}
                  disabled={page === 0}
                  aria-label={`Previous ${title} page`}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8"
                  onClick={() => setPage((current) => Math.min(totalPages - 1, current + 1))}
                  disabled={page >= totalPages - 1}
                  aria-label={`Next ${title} page`}
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}
