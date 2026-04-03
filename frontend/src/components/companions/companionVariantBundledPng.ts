import type { PandaModuleType } from "./pandaTypes";

import backupPng from "../../assets/pandas/backup.png";
import cloudPng from "../../assets/pandas/cloud.png";
import debugPng from "../../assets/pandas/debug.png";
import dockerPng from "../../assets/pandas/docker.png";
import installPng from "../../assets/pandas/install.png";
import networkPng from "../../assets/pandas/network.png";
import neutralPng from "../../assets/pandas/neutral.png";
import securityPng from "../../assets/pandas/security.png";
import startPng from "../../assets/pandas/start.png";
import tutorialPng from "../../assets/pandas/tutorial.png";
import warningPng from "../../assets/pandas/warning.png";

/** Varianten-Grafiken aus dem Bundle (Vite-URL), keine public-Pfade. */
export const COMPANION_USES_BUNDLED_VARIANT_PNG = true as const;

export const COMPANION_VARIANT_BUNDLED_PNG_URL: Record<PandaModuleType, string> =
  {
    start: startPng,
    backup: backupPng,
    network: networkPng,
    security: securityPng,
    docker: dockerPng,
    install: installPng,
    debug: debugPng,
    cloud: cloudPng,
    tutorial: tutorialPng,
    warning: warningPng,
  };

export const COMPANION_NEUTRAL_BUNDLED_PNG_URL: string = neutralPng;

export function getBundledCompanionVariantUrl(type: PandaModuleType): string {
  return COMPANION_VARIANT_BUNDLED_PNG_URL[type];
}

export function getPandaHelperBundledUrl(
  variant:
    | "base"
    | "backup"
    | "bluetooth"
    | "gpio"
    | "security"
    | "diagnostics",
): string {
  switch (variant) {
    case "base":
      return COMPANION_NEUTRAL_BUNDLED_PNG_URL;
    case "backup":
      return backupPng;
    case "bluetooth":
      return networkPng;
    case "gpio":
      return networkPng;
    case "security":
      return securityPng;
    case "diagnostics":
      return debugPng;
    default:
      return COMPANION_NEUTRAL_BUNDLED_PNG_URL;
  }
}
