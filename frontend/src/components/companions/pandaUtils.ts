import type { PandaModuleType, PandaStatus, PandaType } from "./pandaTypes";
import { PANDA_MODULE_TYPES } from "./pandaTypes";

const VALID_STATUS: readonly PandaStatus[] = ["success", "info", "warning", "danger"];

/** Unbekannte oder fehlende Status-Werte → Gelb (warning), wie spezifiziert. */
export function normalizePandaStatus(status: string | undefined | null): PandaStatus {
  if (status && (VALID_STATUS as readonly string[]).includes(status)) {
    return status as PandaStatus;
  }
  return "warning";
}

export function isPandaModuleType(v: string): v is PandaModuleType {
  return (PANDA_MODULE_TYPES as readonly string[]).includes(v);
}

/** Für Bildwahl: nur die 10 Module; bei ungültigem String neutral. */
export function resolvePandaType(type: string): PandaType {
  return isPandaModuleType(type) ? type : "neutral";
}
