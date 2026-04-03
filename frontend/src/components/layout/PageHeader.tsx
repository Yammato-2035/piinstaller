import React from 'react'

export type PageHeaderVisualStyle = 'tech-panel' | 'hero-card' | 'clean-pro'
export type PageHeaderTone =
  | 'dashboard'
  | 'backup'
  | 'monitoring'
  | 'docs'
  | 'appstore'
  | 'setup'
  | 'settings'

export interface PageHeaderProps {
  title: string
  subtitle?: string
  badge?: React.ReactNode
  status?: React.ReactNode
  companion?: React.ReactNode
  className?: string
  visualStyle?: PageHeaderVisualStyle
  tone?: PageHeaderTone
}

type ToneSkin = {
  gradTech: string
  gradHero: string
  gradClean: string
  border: string
  ring: string
  inset: string
  title: string
  subtitle: string
  status: string
}

const TONE_SKIN: Record<PageHeaderTone, ToneSkin> = {
  dashboard: {
    gradTech: 'bg-gradient-to-br from-slate-950 via-teal-950/80 to-slate-950',
    gradHero: 'bg-gradient-to-br from-slate-950 via-cyan-950/65 to-emerald-950/50',
    gradClean: 'bg-gradient-to-br from-slate-900 via-slate-800/95 to-slate-900',
    border: 'border-teal-500/30',
    ring: 'ring-1 ring-teal-400/20',
    inset: 'shadow-[inset_0_1px_0_0_rgba(45,212,191,0.14)]',
    title: 'text-white',
    subtitle: 'text-teal-100/85',
    status: 'text-slate-300',
  },
  backup: {
    gradTech: 'bg-gradient-to-br from-slate-950 via-sky-950/75 to-slate-950',
    gradHero: 'bg-gradient-to-br from-slate-950 via-cyan-900/55 to-indigo-950/55',
    gradClean: 'bg-gradient-to-br from-slate-900 via-sky-950/35 to-slate-900',
    border: 'border-sky-400/35',
    ring: 'ring-1 ring-amber-400/25',
    inset: 'shadow-[inset_0_1px_0_0_rgba(56,189,248,0.16)]',
    title: 'text-white',
    subtitle: 'text-sky-100/88',
    status: 'text-slate-300',
  },
  monitoring: {
    gradTech: 'bg-gradient-to-br from-slate-950 via-cyan-950/55 to-blue-950/70',
    gradHero: 'bg-gradient-to-br from-slate-950 via-blue-950/50 to-cyan-950/40',
    gradClean: 'bg-gradient-to-br from-slate-950 via-slate-800 to-cyan-950/35',
    border: 'border-cyan-500/28',
    ring: 'ring-1 ring-cyan-400/18',
    inset: 'shadow-[inset_0_1px_0_0_rgba(34,211,238,0.11)]',
    title: 'text-slate-50',
    subtitle: 'text-cyan-100/78',
    status: 'text-slate-400',
  },
  docs: {
    gradTech: 'bg-gradient-to-br from-slate-900 via-sky-950/40 to-indigo-950/55',
    gradHero: 'bg-gradient-to-br from-slate-900 via-indigo-950/45 to-sky-950/35',
    gradClean:
      'bg-gradient-to-br from-slate-50 via-sky-100/70 to-indigo-100/80 dark:from-slate-900 dark:via-sky-950/35 dark:to-indigo-950/45',
    border: 'border-slate-400/25 dark:border-slate-500/35',
    ring: 'ring-1 ring-slate-300/40 dark:ring-slate-400/15',
    inset: 'shadow-[inset_0_1px_0_0_rgba(255,255,255,0.45)] dark:shadow-[inset_0_1px_0_0_rgba(148,163,184,0.12)]',
    title: 'text-white',
    subtitle: 'text-sky-100/88',
    status: 'text-slate-300',
  },
  appstore: {
    gradTech: 'bg-gradient-to-br from-slate-950 via-indigo-950/70 to-slate-950',
    gradHero: 'bg-gradient-to-br from-slate-950 via-violet-950/50 to-slate-950',
    gradClean: 'bg-gradient-to-br from-slate-900 via-indigo-950/40 to-slate-900',
    border: 'border-violet-500/28',
    ring: 'ring-1 ring-emerald-400/18',
    inset: 'shadow-[inset_0_1px_0_0_rgba(52,211,153,0.12)]',
    title: 'text-white',
    subtitle: 'text-violet-100/82',
    status: 'text-slate-300',
  },
  setup: {
    gradTech: 'bg-gradient-to-br from-slate-950 via-sky-950/60 to-emerald-950/55',
    gradHero: 'bg-gradient-to-br from-slate-950 via-teal-900/50 to-sky-950/55',
    gradClean: 'bg-gradient-to-br from-slate-900 via-emerald-950/30 to-sky-950/35',
    border: 'border-emerald-500/30',
    ring: 'ring-1 ring-sky-400/22',
    inset: 'shadow-[inset_0_1px_0_0_rgba(56,189,248,0.14)]',
    title: 'text-white',
    subtitle: 'text-emerald-100/85',
    status: 'text-slate-300',
  },
  settings: {
    gradTech: 'bg-gradient-to-br from-slate-950 via-slate-800 to-sky-950/50',
    gradHero: 'bg-gradient-to-br from-slate-950 via-sky-900/45 to-slate-900',
    gradClean: 'bg-gradient-to-br from-slate-900 via-slate-800/95 to-sky-950/30',
    border: 'border-sky-500/28',
    ring: 'ring-1 ring-slate-400/15',
    inset: 'shadow-[inset_0_1px_0_0_rgba(56,189,248,0.1)]',
    title: 'text-white',
    subtitle: 'text-white/95',
    status: 'text-slate-300',
  },
}

function surfaceFor(visualStyle: PageHeaderVisualStyle, skin: ToneSkin) {
  if (visualStyle === 'hero-card') {
    return `${skin.gradHero} ${skin.border} ${skin.ring} ${skin.inset} shadow-2xl shadow-black/45`
  }
  if (visualStyle === 'clean-pro') {
    return `${skin.gradClean} ${skin.border} ${skin.ring} ${skin.inset} shadow-md shadow-black/25`
  }
  return `${skin.gradTech} ${skin.border} ${skin.ring} ${skin.inset} shadow-lg shadow-black/35`
}

function paddingFor(visualStyle: PageHeaderVisualStyle) {
  if (visualStyle === 'hero-card') return 'p-6 sm:p-8'
  if (visualStyle === 'clean-pro') return 'p-5 sm:p-6'
  return 'p-5 sm:p-6'
}

function titleSizeFor(visualStyle: PageHeaderVisualStyle) {
  if (visualStyle === 'hero-card') return 'text-3xl sm:text-4xl font-bold tracking-tight'
  return 'text-2xl sm:text-3xl font-bold tracking-tight'
}

function subtitleSizeFor(visualStyle: PageHeaderVisualStyle) {
  if (visualStyle === 'hero-card') return 'mt-2 text-sm sm:text-base leading-relaxed'
  return 'mt-1.5 text-sm sm:text-base leading-snug'
}

const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  subtitle,
  badge,
  status,
  companion,
  className = '',
  visualStyle = 'tech-panel',
  tone = 'docs',
}) => {
  const skin = TONE_SKIN[tone]
  const docsCleanProText =
    tone === 'docs' && visualStyle === 'clean-pro'
      ? {
          title: 'text-slate-900 dark:text-white',
          subtitle: 'text-slate-600 dark:text-slate-300',
          status: 'text-slate-600 dark:text-slate-400',
        }
      : null
  const titleClass = docsCleanProText?.title ?? skin.title
  const subtitleClass = docsCleanProText?.subtitle ?? skin.subtitle
  const statusClass = docsCleanProText?.status ?? skin.status

  const cardClass = [
    'relative overflow-hidden rounded-2xl sm:rounded-3xl border backdrop-blur-md',
    surfaceFor(visualStyle, skin),
    paddingFor(visualStyle),
  ].join(' ')

  return (
    <header className={`mb-6 sm:mb-8 ${className}`.trim()}>
      <div className={cardClass}>
        <div
          className="pointer-events-none absolute inset-0 bg-gradient-to-t from-black/15 via-transparent to-white/[0.06]"
          aria-hidden
        />
        <div className="relative flex items-start justify-between gap-3 sm:gap-4">
          <div className="min-w-0 flex-1">
            <h1 className={`${titleSizeFor(visualStyle)} ${titleClass} leading-tight`}>{title}</h1>
            {subtitle ? (
              <p className={`${subtitleSizeFor(visualStyle)} ${subtitleClass}`}>{subtitle}</p>
            ) : null}
          </div>
          {badge ? <div className="shrink-0 ml-2 pt-0.5">{badge}</div> : null}
        </div>

        {status ? (
          <div
            className={`relative mt-4 pt-3 border-t border-slate-300/45 dark:border-white/10 ${statusClass} text-xs sm:text-sm leading-snug`}
          >
            {status}
          </div>
        ) : null}
      </div>

      {companion ? <div className="mt-4">{companion}</div> : null}
    </header>
  )
}

export default PageHeader
