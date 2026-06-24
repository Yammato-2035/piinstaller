import de from './i18n/de.json';
import en from './i18n/en.json';
import fr from './i18n/fr.json';
import nl from './i18n/nl.json';

export type RescueLocale = 'de' | 'en' | 'fr' | 'nl';

export const RESCUE_LOCALES: { code: RescueLocale; flag: string }[] = [
  { code: 'de', flag: '🇩🇪' },
  { code: 'en', flag: '🇬🇧' },
  { code: 'fr', flag: '🇫🇷' },
  { code: 'nl', flag: '🇳🇱' },
];

const DICTS: Record<RescueLocale, Record<string, unknown>> = { de, en, fr, nl };

export function getRescueDict(locale: RescueLocale): Record<string, unknown> {
  return DICTS[locale] ?? en;
}

function resolvePath(dict: Record<string, unknown>, key: string): string | null {
  const parts = key.split('.');
  let cur: unknown = dict;
  for (const p of parts) {
    if (cur && typeof cur === 'object' && p in (cur as object)) {
      cur = (cur as Record<string, unknown>)[p];
    } else {
      return null;
    }
  }
  return typeof cur === 'string' ? cur : null;
}

function fallbackChain(dict: Record<string, unknown>): Record<string, unknown>[] {
  if (dict === en) return [en];
  if (dict === de) return [de, en];
  return [dict, de, en];
}

/** Resolve i18n key with DE→EN fallback; never expose raw key names in UI. */
export function tPath(dict: Record<string, unknown>, key: string): string {
  for (const candidate of fallbackChain(dict)) {
    const value = resolvePath(candidate, key);
    if (value !== null) return value;
  }
  const last = resolvePath(en, key);
  if (last !== null) return last;
  const leaf = key.split('.').pop() || key;
  return leaf.replace(/([A-Z])/g, ' $1').replace(/^./, (c) => c.toUpperCase()).trim();
}

export function languageLabel(dict: Record<string, unknown>, locale: RescueLocale): string {
  return tPath(dict, `language.${locale}`);
}
