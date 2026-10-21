import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { Table2, ChevronLeft, ChevronRight } from "lucide-react"
import { getJobPreview } from "@/api/client"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"

interface DataPreviewProps {
  jobId: string
}

const PAGE_SIZE = 20

function escapeText(val: string): string {
  return val
}

export function DataPreview({ jobId }: DataPreviewProps) {
  const [tab, setTab] = useState<"cleaned" | "rejected">("cleaned")
  const [page, setPage] = useState(0)

  const { data, isLoading } = useQuery({
    queryKey: ["preview", jobId],
    queryFn: () => getJobPreview(jobId, 100),
  })

  if (isLoading || !data) {
    return (
      <div className="flex items-center justify-center py-8 text-muted-foreground text-sm">
        Loading preview...
      </div>
    )
  }

  const rows = tab === "cleaned" ? data.cleaned : data.rejected
  const total = tab === "cleaned" ? data.cleaned_total : data.rejected_total
  const columns = rows.length > 0 ? Object.keys(rows[0]) : []
  const pageStart = page * PAGE_SIZE
  const pageRows = rows.slice(pageStart, pageStart + PAGE_SIZE)
  const totalPages = Math.ceil(rows.length / PAGE_SIZE)

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Table2 className="h-4 w-4 text-muted-foreground" />
        <span className="text-sm font-medium">Data Preview</span>
      </div>

      <div className="flex gap-2">
        <button
          onClick={() => { setTab("cleaned"); setPage(0) }}
          className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
            tab === "cleaned"
              ? "bg-primary text-primary-foreground"
              : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
          }`}
        >
          Cleaned
          <Badge variant="secondary" className="ml-2 text-xs">
            {data.cleaned_total}
          </Badge>
        </button>
        <button
          onClick={() => { setTab("rejected"); setPage(0) }}
          className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
            tab === "rejected"
              ? "bg-destructive text-destructive-foreground"
              : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
          }`}
        >
          Rejected
          <Badge variant="secondary" className="ml-2 text-xs">
            {data.rejected_total}
          </Badge>
        </button>
      </div>

      {rows.length === 0 ? (
        <p className="text-sm text-muted-foreground py-4 text-center">
          No {tab} records.
        </p>
      ) : (
        <>
          <div className="rounded-lg border overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="px-3 py-2 text-left font-medium text-muted-foreground w-10">
                    #
                  </th>
                  {columns.map((col) => (
                    <th
                      key={col}
                      className="px-3 py-2 text-left font-medium text-muted-foreground whitespace-nowrap"
                    >
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {pageRows.map((row, i) => (
                  <tr key={pageStart + i} className="border-b last:border-0 hover:bg-muted/30">
                    <td className="px-3 py-2 text-muted-foreground">
                      {pageStart + i + 1}
                    </td>
                    {columns.map((col) => (
                      <td
                        key={col}
                        className="px-3 py-2 max-w-[200px] truncate"
                        title={escapeText(row[col] || "")}
                      >
                        {escapeText(row[col] || "")}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>
              Showing {pageStart + 1}–{Math.min(pageStart + PAGE_SIZE, rows.length)} of{" "}
              {rows.length} rows
              {total > rows.length && ` (${total} total)`}
            </span>
            {totalPages > 1 && (
              <div className="flex gap-1">
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7"
                  onClick={() => setPage((p) => Math.max(0, p - 1))}
                  disabled={page === 0}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7"
                  onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                  disabled={page >= totalPages - 1}
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
