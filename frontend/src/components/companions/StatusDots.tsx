import React from "react";

/** Drei Ampel-Stufen wie im Dashboard (Backup/Restore/Security/Updates). */
export type LampTriState = "red" | "yellow" | "green";

export interface LampDotProps {
  lamp: LampTriState;
  /** Gelb ohne starkes Leuchten (wie bisher im Dashboard). */
  quiet?: boolean;
  className?: string;
}

/** Einzelner Punkt – gleiche Tailwind-Farben wie ehemals `TrafficLightDot` im Dashboard. */
export const LampDot: React.FC<LampDotProps> = ({ lamp, quiet, className = "" }) => {
  const glow =
    quiet || lamp === "green"
      ? ""
      : lamp === "yellow"
        ? " shadow-[0_0_4px_rgba(251,191,36,0.35)]"
        : " shadow-[0_0_8px_rgba(239,68,68,0.55)]";
  const cls =
    lamp === "green"
      ? "bg-emerald-400" + (quiet ? "" : " shadow-[0_0_6px_rgba(52,211,153,0.45)]")
      : lamp === "yellow"
        ? "bg-amber-400" + glow
        : "bg-red-500" + glow;
  return (
    <span
      className={`inline-block w-2.5 h-2.5 sm:w-3 sm:h-3 rounded-full shrink-0 ${cls} ${className}`.trim()}
      aria-hidden
    />
  );
};

export interface LampAreaCardProps {
  label: string;
  lamp: LampTriState;
  className?: string;
}

/** Kompakte Bereichskachel mit Punkt (ehemals `AreaLightCard`). */
export const LampAreaCard: React.FC<LampAreaCardProps> = ({ label, lamp, className = "" }) => {
  const border =
    lamp === "green"
      ? "border-emerald-500/90"
      : lamp === "yellow"
        ? "border-amber-500/60"
        : "border-red-500";
  const bg =
    lamp === "green"
      ? "bg-emerald-950/30"
      : lamp === "yellow"
        ? "bg-amber-950/15"
        : "bg-red-950/35";
  return (
    <div
      className={`rounded-md sm:rounded-lg border-l-[3px] sm:border-l-4 ${border} ${bg} px-2 py-1.5 sm:px-3 sm:py-2 flex items-center gap-1.5 sm:gap-2 min-h-[2.4rem] sm:min-h-[2.65rem] ${className}`.trim()}
      role="status"
    >
      <LampDot lamp={lamp} quiet={lamp === "yellow"} />
      <span className="text-xs sm:text-sm font-medium text-slate-100 leading-tight">{label}</span>
    </div>
  );
};
