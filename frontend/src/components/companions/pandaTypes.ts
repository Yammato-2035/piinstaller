/** Öffentliche Module (Panda-Motiv pro Bereich). */
export const PANDA_MODULE_TYPES = [
  "start",
  "backup",
  "network",
  "security",
  "docker",
  "install",
  "debug",
  "cloud",
  "tutorial",
  "warning",
] as const;

export type PandaModuleType = (typeof PANDA_MODULE_TYPES)[number];

/** Inkl. internes Fallback-Motiv für fehlende Assets. */
export type PandaType = PandaModuleType | "neutral";

export type PandaStatus = "success" | "info" | "warning" | "danger";

export type PandaSize = "sm" | "md" | "lg";
