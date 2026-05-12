import type { PandaModuleType, PandaType } from "./pandaTypes";
import { PANDA_MODULE_TYPES } from "./pandaTypes";
import {
  getCompanionBaseDisplayUrl,
  getCompanionOverlayUrl,
} from "./companionAssetManifest";
import {
  COMPANION_NEUTRAL_BUNDLED_PNG_URL,
  COMPANION_USES_BUNDLED_VARIANT_PNG,
  COMPANION_VARIANT_BUNDLED_PNG_URL,
  getBundledCompanionVariantUrl,
  getPandaHelperBundledUrl,
} from "./companionVariantBundledPng";

export {
  COMPANION_ASSET_MANIFEST,
  COMPANION_OVERLAY_IDS,
  companionShouldUseLogoMainCrop,
  getCompanionBaseDisplayUrl,
  getCompanionOverlayUrl,
  getCompanionPandaOnlyUrl,
} from "./companionAssetManifest";

export {
  COMPANION_NEUTRAL_BUNDLED_PNG_URL,
  COMPANION_USES_BUNDLED_VARIANT_PNG,
  COMPANION_VARIANT_BUNDLED_PNG_URL,
  getBundledCompanionVariantUrl,
  getPandaHelperBundledUrl,
} from "./companionVariantBundledPng";

const buildCompanionImageUrlRecord = (): Record<PandaType, string> => {
  const r = {} as Record<PandaType, string>;
  for (const t of PANDA_MODULE_TYPES) {
    r[t] = getBundledCompanionVariantUrl(t);
  }
  r.neutral = COMPANION_NEUTRAL_BUNDLED_PNG_URL;
  return r;
};

export const COMPANION_IMAGE_URL: Record<PandaType, string> =
  buildCompanionImageUrlRecord();

export const COMPANION_NEUTRAL_URL = COMPANION_IMAGE_URL.neutral;

export const COMPANION_OVERLAY_URL: Partial<Record<PandaModuleType, string>> =
  COMPANION_USES_BUNDLED_VARIANT_PNG
    ? ({} as Partial<Record<PandaModuleType, string>>)
    : (Object.fromEntries(
        PANDA_MODULE_TYPES.map((t) => {
          const u = getCompanionOverlayUrl(t);
          return u ? ([t, u] as const) : null;
        }).filter(Boolean) as [PandaModuleType, string][],
      ) as Partial<Record<PandaModuleType, string>>);

export const PANDA_HELPER_IMAGE_URL = {
  base: getPandaHelperBundledUrl("base"),
  backup: getPandaHelperBundledUrl("backup"),
  bluetooth: getPandaHelperBundledUrl("bluetooth"),
  gpio: getPandaHelperBundledUrl("gpio"),
  security: getPandaHelperBundledUrl("security"),
  diagnostics: getPandaHelperBundledUrl("diagnostics"),
} as const;
