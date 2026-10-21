import { type HTMLAttributes, forwardRef } from "react"
import { cn } from "@/lib/utils"

interface ProgressProps extends HTMLAttributes<HTMLDivElement> {
  value?: number
  max?: number
  indeterminate?: boolean
  variant?: "default" | "success" | "destructive"
}

const Progress = forwardRef<HTMLDivElement, ProgressProps>(
  ({ className, value = 0, max = 100, indeterminate = false, variant = "default", ...props }, ref) => {
    const fillClass =
      variant === "success"
        ? "bg-success"
        : variant === "destructive"
          ? "bg-destructive"
          : "bg-primary"

    if (indeterminate) {
      return (
        <div
          ref={ref}
          role="progressbar"
          aria-busy="true"
          className={cn("relative h-2 w-full overflow-hidden rounded-full bg-secondary", className)}
          {...props}
        >
          <div
            className={cn(
              "absolute inset-y-0 w-1/3 rounded-full motion-safe:animate-progress-indeterminate",
              fillClass,
            )}
          />
        </div>
      )
    }

    const pct = Math.min(100, Math.max(0, (value / max) * 100))
    return (
      <div
        ref={ref}
        role="progressbar"
        aria-valuenow={value}
        aria-valuemin={0}
        aria-valuemax={max}
        className={cn("relative h-2 w-full overflow-hidden rounded-full bg-secondary", className)}
        {...props}
      >
        <div
          className={cn("h-full transition-all duration-300", fillClass)}
          style={{ width: `${pct}%` }}
        />
      </div>
    )
  },
)
Progress.displayName = "Progress"

export { Progress }
