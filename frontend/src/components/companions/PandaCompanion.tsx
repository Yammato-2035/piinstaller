import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  COMPANION_ASSET_MANIFEST,
  companionShouldUseLogoMainCrop,
  getCompanionBaseDisplayUrl,
  getBundledCompanionVariantUrl,
} from "./companionAssets";
import { TrafficLight } from "./TrafficLight";
import { PANDA_STATUS_TEXT } from "./pandaText";
import type { PandaModuleType, PandaSize, PandaStatus } from "./pandaTypes";
import { normalizePandaStatus } from "./pandaUtils";
import styles from "./PandaCompanion.module.css";

export interface PandaCompanionProps {
  type: PandaModuleType;
  status?: PandaStatus | string;
  mood?: PandaStatus | string;
  size?: PandaSize;
  showTrafficLight?: boolean;
  trafficLightPosition?: "bottom-right" | "bottom-left";
  surface?: "light" | "dark";
  title?: string;
  subtitle?: string;
  helperText?: string;
  className?: string;
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
  mood,
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
    String(status ?? mood ?? "info"),
  );
  const bundledUrl = getBundledCompanionVariantUrl(type);
  const logoFallbackUrl = getCompanionBaseDisplayUrl();
  const [displayTier, setDisplayTier] = useState<"bundle" | "logo">("bundle");
  const tierRef = useRef(displayTier);
  tierRef.current = displayTier;

  const activeSrc =
    displayTier === "bundle" ? bundledUrl : logoFallbackUrl ?? "";
  const useLogoCrop =
    displayTier === "logo" &&
    Boolean(logoFallbackUrl) &&
    companionShouldUseLogoMainCrop();

  const textBlock = PANDA_STATUS_TEXT[resolvedStatus] ?? PANDA_STATUS_TEXT.warning;
  const width = SIZE_MAP[size];
  const colors = surface === "dark" ? STATUS_COLOR_MAP_DARK : STATUS_COLOR_MAP;

  const [pandaHeightPx, setPandaHeightPx] = useState<number | null>(null);
  const [hardFailed, setHardFailed] = useState(false);

  useEffect(() => {
    setDisplayTier("bundle");
    setHardFailed(false);
    setPandaHeightPx(null);
  }, [type]);

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

  const onImgError = useCallback(() => {
    if (tierRef.current === "bundle" && logoFallbackUrl) {
      setDisplayTier("logo");
      setPandaHeightPx(null);
      return;
    }
    setHardFailed(true);
    setPandaHeightPx(null);
  }, [logoFallbackUrl]);

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
        {hardFailed ? (
          <div
            className={styles.assetMissing}
            style={{ minHeight: Math.max(64, width * 0.85) }}
            role="img"
            aria-label={`Companion Asset fehlt: ${type}`}
          >
            <span>Companion Asset fehlt</span>
            <span className={styles.assetMissingCode}>variant: {type}</span>
            <span className={styles.assetMissingCode}>bundle: {bundledUrl}</span>
            {logoFallbackUrl ? (
              <span className={styles.assetMissingCode}>
                logo-fallback: {COMPANION_ASSET_MANIFEST.brandingLogoMain.assetPath}
              </span>
            ) : null}
            {hardFailed && activeSrc ? (
              <span className={styles.assetMissingCode}>Ladefehler: {activeSrc}</span>
            ) : null}
          </div>
        ) : (
          <div className={styles.pandaStack}>
            <img
              key={`${type}-${displayTier}`}
              src={activeSrc}
              alt={`Setuphelfer Panda für den Bereich ${type}`}
              className={`${styles.pandaImg} ${useLogoCrop ? styles.pandaImgCropFromFullLogo : ""}`.trim()}
              loading="eager"
              decoding="async"
              onLoad={onImgLoad}
              onError={onImgError}
            />
          </div>
        )}

        {showTrafficLight && !hardFailed && (
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
