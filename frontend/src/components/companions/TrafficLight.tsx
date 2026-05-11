import React from "react";
import type { PandaStatus } from "./pandaTypes";
import { normalizePandaStatus } from "./pandaUtils";

/** Farben wie Dashboard TrafficLightDot / AreaLightCard (Emerald / Amber / Red). */
const LAMP = {
  greenOn: "#34d399",
  greenDim: "#065f46",
  yellowOn: "#fbbf24",
  yellowDim: "#713f12",
  redOn: "#ef4444",
  redDim: "#7f1d1d",
} as const;

const HOUSING_BG = "#0f172a";
const HOUSING_BORDER = "#1e293b";

/** Referenzhöhe der Ampel (md); Skalierung über maxHeightPx. */
const REF_HEIGHT = 66;
const REF = { width: 26, lamp: 10, padV: 6, border: 2 } as const;

export interface TrafficLightProps {
  status: PandaStatus | string;
  /** Max. Höhe der Ampel in px (z. B. 20 % der Panda-Höhe). */
  maxHeightPx: number;
  className?: string;
}

function getActiveLamp(status: PandaStatus): "green" | "yellow" | "red" {
  switch (status) {
    case "success":
    case "info":
      return "green";
    case "warning":
      return "yellow";
    case "danger":
      return "red";
    default:
      return "yellow";
  }
}

export const TrafficLight: React.FC<TrafficLightProps> = ({
  status,
  maxHeightPx,
  className = "",
}) => {
  const normalized = normalizePandaStatus(String(status ?? ""));
  const active = getActiveLamp(normalized);
  const scale = Math.max(0.3, Math.min(1.35, maxHeightPx / REF_HEIGHT));
  const w = REF.width * scale;
  const h = REF_HEIGHT * scale;
  const lamp = REF.lamp * scale;
  const padV = REF.padV * scale;
  const border = Math.max(1, REF.border * scale);

  const lampStyle = (lampColor: "red" | "yellow" | "green"): React.CSSProperties => ({
    width: lamp,
    height: lamp,
    borderRadius: "50%",
    background:
      lampColor === "red"
        ? active === "red"
          ? LAMP.redOn
          : LAMP.redDim
        : lampColor === "yellow"
          ? active === "yellow"
            ? LAMP.yellowOn
            : LAMP.yellowDim
          : active === "green"
            ? LAMP.greenOn
            : LAMP.greenDim,
    boxShadow:
      active === lampColor
        ? lampColor === "green"
          ? "0 0 10px rgba(52, 211, 153, 0.45)"
          : lampColor === "yellow"
            ? "0 0 8px rgba(251, 191, 36, 0.4)"
            : "0 0 10px rgba(239, 68, 68, 0.5)"
        : "none",
  });

  return (
    <div
      className={className}
      aria-label={`Statusampel: ${active}`}
      title={`Status: ${active}`}
      style={{
        width: w,
        height: h,
        maxHeight: maxHeightPx,
        background: HOUSING_BG,
        borderRadius: 999,
        border: `${border}px solid ${HOUSING_BORDER}`,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "space-evenly",
        padding: `${padV}px 0`,
        boxSizing: "border-box",
        flexShrink: 0,
      }}
    >
      <div style={lampStyle("red")} />
      <div style={lampStyle("yellow")} />
      <div style={lampStyle("green")} />
    </div>
  );
};
