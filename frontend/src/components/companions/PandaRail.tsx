import React from "react";

/**
 * Gemeinsamer „Panda-Bereich“ pro Seite: ein Rahmen, innen meist
 * {@link PandaCompanion} mit `frame={false}`.
 */
export const PandaRail: React.FC<{
  children: React.ReactNode;
  className?: string;
}> = ({ children, className = "" }) => (
  <section
    aria-label="Setuphelfer Begleiter"
    className={`rounded-xl border border-slate-600/80 bg-slate-900/50 backdrop-blur-sm px-3 py-3 sm:px-4 sm:py-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.05),0_4px_24px_rgba(0,0,0,0.2)] ${className}`.trim()}
  >
    {children}
  </section>
);
