import React from 'react'

const skeletonBase = 'rounded animate-pulse bg-slate-300 dark:bg-slate-700'

/** Einzeiliger Text-Skeleton */
export function SkeletonText({ className = 'h-4 w-full' }: { className?: string }) {
  return <div className={`${skeletonBase} ${className}`} aria-hidden />
}

/** Runder Skeleton (z. B. für Avatar/Icon) */
export function SkeletonCircle({ className = 'h-10 w-10' }: { className?: string }) {
  return <div className={`rounded-full ${skeletonBase} ${className}`} aria-hidden />
}

/** Karten-Skeleton: Platzhalter für StatCard/Content-Card */
export function SkeletonCard({ lines = 2 }: { lines?: number }) {
  return (
    <div className="card opacity-90">
      <div className="flex items-center justify-between">
        <div className="flex-1 space-y-2">
          <SkeletonText className="h-4 w-1/2" />
          <SkeletonText className="h-8 w-1/3" />
        </div>
        <SkeletonCircle className="h-12 w-12" />
      </div>
      {lines > 2 && (
        <div className="mt-4 space-y-2">
          {Array.from({ length: lines - 2 }).map((_, i) => (
            <SkeletonText key={i} className="h-3 w-full" />
          ))}
        </div>
      )}
    </div>
  )
}

/** Listen-Skeleton: mehrere Zeilen */
export function SkeletonList({ rows = 4 }: { rows?: number }) {
  return (
    <div className="space-y-2">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex items-center gap-3 p-3 rounded-lg bg-slate-200/50 dark:bg-slate-700/30">
          <SkeletonCircle className="h-8 w-8 shrink-0" />
          <div className="flex-1 space-y-1">
            <SkeletonText className="h-4 w-2/3" />
            <SkeletonText className="h-3 w-1/2" />
          </div>
        </div>
      ))}
    </div>
  )
}

/** Vollständiger Seiten-Skeleton: Titel + Bereich mit Karten/Listen */
export function PageSkeleton({
  title = true,
  subtitle = true,
  cards = 4,
  hasList = false,
  listRows = 3,
}: {
  title?: boolean
  subtitle?: boolean
  cards?: number
  hasList?: boolean
  listRows?: number
}) {
  return (
    <div className="space-y-8">
      <div>
        {title && (
          <div className="flex items-center gap-3 mb-2">
            <SkeletonCircle className="h-9 w-9" />
            <SkeletonText className="h-8 w-48" />
          </div>
        )}
        {subtitle && <SkeletonText className="h-4 w-64" />}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {Array.from({ length: cards }).map((_, i) => (
          <SkeletonCard key={i} lines={2} />
        ))}
      </div>

      {hasList && (
        <div className="card">
          <SkeletonText className="h-6 w-56 mb-4" />
          <SkeletonList rows={listRows} />
        </div>
      )}
    </div>
  )
}

export default { SkeletonText, SkeletonCircle, SkeletonCard, SkeletonList, PageSkeleton }
