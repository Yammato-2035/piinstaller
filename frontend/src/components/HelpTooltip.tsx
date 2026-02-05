import React, { useState } from 'react'
import { HelpCircle } from 'lucide-react'

interface HelpTooltipProps {
  text: string
  className?: string
  size?: number
}

/** Kontextsensitive Hilfe: "?" Icon mit Tooltip (Transformationsplan 3.2). */
const HelpTooltip: React.FC<HelpTooltipProps> = ({ text, className = '', size = 16 }) => {
  const [visible, setVisible] = useState(false)
  return (
    <span className="relative inline-flex">
      <button
        type="button"
        onFocus={() => setVisible(true)}
        onBlur={() => setVisible(false)}
        onMouseEnter={() => setVisible(true)}
        onMouseLeave={() => setVisible(false)}
        className={`text-slate-400 hover:text-sky-500 focus:text-sky-500 focus:outline-none rounded-full p-0.5 ${className}`}
        aria-label="Hilfe"
      >
        <HelpCircle size={size} />
      </button>
      {visible && (
        <span
          className="absolute left-1/2 -translate-x-1/2 bottom-full mb-1 px-3 py-2 text-xs text-slate-100 bg-slate-800 dark:bg-slate-900 border border-slate-600 rounded-lg shadow-xl whitespace-normal max-w-xs z-50 pointer-events-none"
          role="tooltip"
        >
          {text}
        </span>
      )}
    </span>
  )
}

export default HelpTooltip
