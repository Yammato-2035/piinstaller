import React from "react";
import {
  isYellowTrafficLightLamp,
  lampAreaBackgroundClass,
  lampAreaBorderClass,
  lampDotBackgroundClass,
} from "../../viewmodels/statusViewModel";

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
  const cls = lampDotBackgroundClass(lamp, quiet);
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
  const border = lampAreaBorderClass(lamp);
  const bg = lampAreaBackgroundClass(lamp);
  return (
    <div
      className={`rounded-md sm:rounded-lg border-l-[3px] sm:border-l-4 ${border} ${bg} px-2 py-1.5 sm:px-3 sm:py-2 flex items-center gap-1.5 sm:gap-2 min-h-[2.4rem] sm:min-h-[2.65rem] ${className}`.trim()}
      role="status"
    >
      <LampDot lamp={lamp} quiet={isYellowTrafficLightLamp(lamp)} />
      <span className="text-xs sm:text-sm font-medium text-slate-100 leading-tight">{label}</span>
    </div>
  );
};
