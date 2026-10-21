import { useId } from "react"
import { cn } from "@/lib/utils"

interface BrandMarkProps {
  className?: string
}

export function BrandMark({ className }: BrandMarkProps) {
  const id = useId().replace(/:/g, "")
  return (
    <svg
      viewBox="0 0 32 32"
      className={cn("shrink-0", className)}
      aria-hidden="true"
      focusable="false"
    >
      <defs>
        <linearGradient id={id} x1="0" y1="32" x2="0" y2="0" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#008F6B" />
          <stop offset="100%" stopColor="#00C896" />
        </linearGradient>
      </defs>
      <rect x="1.5" y="18" width="8" height="12.5" rx="4" fill={`url(#${id})`} />
      <rect x="12" y="10.5" width="8" height="20" rx="4" fill={`url(#${id})`} />
      <rect x="22.5" y="3" width="8" height="27.5" rx="4" fill={`url(#${id})`} />
    </svg>
  )
}

interface BrandLogoProps {
  className?: string
  markClassName?: string
}

export function BrandLogo({ className, markClassName }: BrandLogoProps) {
  return (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      <BrandMark className={cn("h-8 w-8", markClassName)} />
      <span className="text-[1.15rem] font-extrabold leading-none tracking-tight">
        <span className="text-navy">Data</span>
        <span className="text-emerald">Forge</span>
      </span>
    </span>
  )
}
