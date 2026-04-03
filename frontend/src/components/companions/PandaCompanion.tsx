import React, { useCallback, useMemo, useState } from "react";
import { COMPANION_IMAGE_URL, COMPANION_NEUTRAL_URL } from "./companionAssets";
import { TrafficLight } from "./TrafficLight";
import { PANDA_STATUS_TEXT } from "./pandaText";
import type { PandaModuleType, PandaSize, PandaStatus } from "./pandaTypes";
import { normalizePandaStatus } from "./pandaUtils";
import styles from "./PandaCompanion.module.css";

export interface PandaCompanionProps {
  type: PandaModuleType;
  status?: PandaStatus | string;
  size?: PandaSize;
  showTrafficLight?: boolean;
  /** Ampel unten rechts oder links (kleines Accessoire). */
  trafficLightPosition?: "bottom-right" | "bottom-left";
  /** Helle Kachel oder dunkle Einbettung (Dashboard & Co.). */
  surface?: "light" | "dark";
  title?: string;
  subtitle?: string;
  helperText?: string;
  className?: string;
  /** false = ohne eigene Kachel (einbetten in PandaRail / Seitenrahmen). */
  frame?: boolean;
}

const SIZE_MAP: Record<PandaSize, number> = {
  sm: 120,
  md: 180,
  lg: 240,
};

const STATUS_COLOR_MAP: Record<PandaStatus, string> = {
  success: "#166534",
  info: "#1d4ed8",
  warning: "#a16207",
  danger: "#b91c1c",
};

const STATUS_COLOR_MAP_DARK: Record<PandaStatus, string> = {
  success: "#4ade80",
  info: "#60a5fa",
  warning: "#fbbf24",
  danger: "#f87171",
};

export const PandaCompanion: React.FC<PandaCompanionProps> = ({
  type,
  status = "info",
  size = "md",
  showTrafficLight = true,
  trafficLightPosition = "bottom-right",
  surface = "light",
  title,
  subtitle,
  helperText,
  className = "",
  frame = true,
}) => {
  const resolvedStatus = normalizePandaStatus(
    typeof status === "string" ? status : String(status),
  );
  const imageSrc = COMPANION_IMAGE_URL[type] ?? COMPANION_NEUTRAL_URL;
  const textBlock = PANDA_STATUS_TEXT[resolvedStatus] ?? PANDA_STATUS_TEXT.warning;
  const width = SIZE_MAP[size];
  const colors = surface === "dark" ? STATUS_COLOR_MAP_DARK : STATUS_COLOR_MAP;

  const [pandaHeightPx, setPandaHeightPx] = useState<number | null>(null);

  const onImgLoad = useCallback(
    (e: React.SyntheticEvent<HTMLImageElement>) => {
      const el = e.currentTarget;
      const nh = el.naturalHeight;
      const nw = el.naturalWidth;
      if (nw > 0 && nh > 0) {
        const renderedH = (nh / nw) * width;
        setPandaHeightPx(renderedH);
      } else {
        setPandaHeightPx(width);
      }
    },
    [width],
  );

  const maxTrafficLightHeight = useMemo(() => {
    const h = pandaHeightPx ?? width * 1.05;
    return Math.max(24, h * 0.2);
  }, [pandaHeightPx, width]);

  const onImgError = useCallback((e: React.SyntheticEvent<HTMLImageElement>) => {
    const target = e.currentTarget;
    if (target.dataset.fallback === "1") return;
    target.dataset.fallback = "1";
    target.src = COMPANION_NEUTRAL_URL;
  }, []);

  const skin =
    surface === "dark" ? `${styles.root} ${styles.rootDark}` : styles.root;
  const rootClass = frame ? skin : `${skin} ${styles.rootBare}`;

  const tlStyle: React.CSSProperties =
    trafficLightPosition === "bottom-left"
      ? { position: "absolute", left: 6, bottom: 8 }
      : { position: "absolute", right: 6, bottom: 8 };

  return (
    <div className={`${rootClass} ${className}`.trim()}>
      <div
        className={styles.pandaWrap}
        style={{ width, minWidth: width, maxWidth: "100%" }}
      >
        <img
          src={imageSrc}
          alt={`Setuphelfer Panda für den Bereich ${type}`}
          className={styles.pandaImg}
          loading="eager"
          decoding="async"
          onLoad={onImgLoad}
          onError={onImgError}
        />

        {showTrafficLight && (
          <div style={tlStyle}>
            <TrafficLight status={resolvedStatus} maxHeightPx={maxTrafficLightHeight} />
          </div>
        )}
      </div>

      <div className={styles.textBlock}>
        <div className={styles.title}>{title || defaultTitle(type)}</div>

        <div className={styles.subtitle}>{subtitle || defaultSubtitle(type)}</div>

        <div
          className={styles.badge}
          style={{ color: colors[resolvedStatus] }}
        >
          {textBlock.label}
        </div>

        <div className={styles.helper}>{helperText || textBlock.helper}</div>
      </div>
    </div>
  );
};

function defaultTitle(type: PandaModuleType): string {
  switch (type) {
    case "start":
      return "Start-Panda";
    case "backup":
      return "Backup-Panda";
    case "network":
      return "Netzwerk-Panda";
    case "security":
      return "Security-Panda";
    case "docker":
      return "Docker-Panda";
    case "install":
      return "Installations-Panda";
    case "debug":
      return "Debug-Panda";
    case "cloud":
      return "Cloud-Panda";
    case "tutorial":
      return "Tutorial-Panda";
    case "warning":
      return "Warn-Panda";
    default:
      return "Setuphelfer-Panda";
  }
}

function defaultSubtitle(type: PandaModuleType): string {
  switch (type) {
    case "start":
      return "Dein Einstieg in den Setuphelfer.";
    case "backup":
      return "Sichert Daten, bevor etwas schiefgeht.";
    case "network":
      return "Analysiert Verbindungen und findet Probleme.";
    case "security":
      return "Hilft beim Schutz deines Systems.";
    case "docker":
      return "Bringt Ordnung in Dienste und Container.";
    case "install":
      return "Begleitet dich durch Installation und Einrichtung.";
    case "debug":
      return "Liest Spuren und hilft bei der Fehlersuche.";
    case "cloud":
      return "Zeigt den Status von Synchronisation und Zugriff.";
    case "tutorial":
      return "Erklärt die Schritte verständlich und nachvollziehbar.";
    case "warning":
      return "Hält dich an, bevor du ein Risiko eingehst.";
    default:
      return "Allgemeiner Begleiter im Setuphelfer.";
  }
}
