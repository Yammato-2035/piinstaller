import React from 'react'

interface BootSplashProps {
  text?: string
}

const BootSplash: React.FC<BootSplashProps> = ({ text = 'Setuphelfer wird gestartet…' }) => {
  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-100 dark:bg-slate-900">
      <div className="flex flex-col items-center gap-4 rounded-2xl border border-slate-300/80 dark:border-slate-700 bg-white/85 dark:bg-slate-800/85 px-8 py-7 shadow-xl">
        <img
          src="/assets/branding/splash/splash-source.svg"
          alt="SetupHelfer Startsymbol"
          className="h-24 w-24 object-contain"
          loading="eager"
          decoding="async"
        />
        <p className="text-sm font-medium text-slate-700 dark:text-slate-200">{text}</p>
      </div>
    </div>
  )
}

export default BootSplash
