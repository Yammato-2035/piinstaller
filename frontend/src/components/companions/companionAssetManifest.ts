/**
 * Audit-Stand: Pfade relativ zu `frontend/public/`.
 * Keine Laufzeit-Dateisystem-Prüfung im Browser — Wahrheit aus Repo- und Build-Kontext.
 */
import { mascotPublicUrl } from "../../lib/mascotPublicUrl";
import { COMPANION_USES_BUNDLED_VARIANT_PNG } from "./companionVariantBundledPng";
import type { PandaModuleType } from "./pandaTypes";

export type CompanionFallbackMode =
  | "none"
  | "placeholderCard"
  | "logoMainCrop";

export interface CompanionAssetEntry {
  assetPath: string;
  exists: boolean;
  isPlaceholder: boolean;
  usableAsCompanionBase: boolean;
  fallbackMode: CompanionFallbackMode;
  /** Kurznotiz für Maintainer, kein UI-Text */
  auditNote?: string;
}

export const COMPANION_OVERLAY_IDS = [
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
] as const satisfies readonly PandaModuleType[];

export const COMPANION_ASSET_MANIFEST = {
  /** Eingebettetes Raster in SVG — einzige zuverlässige Vollgrafik-Basis für &lt;img&gt;. */
  brandingLogoMain: {
    assetPath: "assets/branding/logo/logo-main.svg",
    exists: true,
    isPlaceholder: false,
    usableAsCompanionBase: true,
    fallbackMode: "none",
  } satisfies CompanionAssetEntry,

  /** Nur Wrapper mit svg:image → logo-main; als Companion-Basis in WebView unzuverlässig. */
  brandingPandaOnly: {
    assetPath: "assets/branding/logo/panda-only.svg",
    exists: true,
    isPlaceholder: false,
    usableAsCompanionBase: false,
    fallbackMode: "logoMainCrop",
    auditNote: "references ./logo-main.svg inside SVG",
  } satisfies CompanionAssetEntry,

  /** Varianten-PNGs unter src/assets/pandas — per Vite-Import gebündelt. */
  srcAssetsPandasPng: {
    assetPath: "src/assets/pandas/*.png",
    exists: true,
    isPlaceholder: false,
    usableAsCompanionBase: true,
    fallbackMode: "none",
    auditNote: "companionVariantBundledPng.ts",
  } satisfies CompanionAssetEntry,

  companionOverlays: {
    assetPath: "assets/mascot/companion-overlays/",
    exists: true,
    isPlaceholder: false,
    usableAsCompanionBase: false,
    fallbackMode: "none",
    auditNote: "vector-only overlays, no nested href",
  } satisfies CompanionAssetEntry,
} as const;

/** Öffentliche URL für die Companion-Basis (logo-main + CSS-Crop) oder null = nicht nutzbar. */
export function getCompanionBaseDisplayUrl(): string | null {
  const m = COMPANION_ASSET_MANIFEST.brandingLogoMain;
  if (!m.exists || !m.usableAsCompanionBase) return null;
  return mascotPublicUrl(m.assetPath);
}

export function getCompanionPandaOnlyUrl(): string | null {
  const m = COMPANION_ASSET_MANIFEST.brandingPandaOnly;
  if (!m.exists || !m.usableAsCompanionBase) return null;
  return mascotPublicUrl(m.assetPath);
}

export function getCompanionOverlayUrl(
  type: PandaModuleType,
): string | null {
  if (COMPANION_USES_BUNDLED_VARIANT_PNG) return null;
  const dir = COMPANION_ASSET_MANIFEST.companionOverlays;
  if (!dir.exists || dir.isPlaceholder) return null;
  if (!COMPANION_OVERLAY_IDS.includes(type as (typeof COMPANION_OVERLAY_IDS)[number])) {
    return null;
  }
  return mascotPublicUrl(`${dir.assetPath}${type}.svg`);
}

export function companionShouldUseLogoMainCrop(): boolean {
  return (
    COMPANION_ASSET_MANIFEST.brandingLogoMain.usableAsCompanionBase &&
    !COMPANION_ASSET_MANIFEST.brandingPandaOnly.usableAsCompanionBase
  );
}
