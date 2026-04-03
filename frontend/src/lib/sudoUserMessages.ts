/** Verständliche Toasts statt roher Backend-Texte (Einsteiger). */
export function sudoSaveErrorToast(raw: string | undefined, t: (key: string) => string): string {
  const m = (raw || '').toLowerCase()
  if (!raw?.trim()) return t('sudo.dialog.toast.saveFailed')
  if (
    m.includes('falsch') ||
    m.includes('incorrect password') ||
    m.includes('wrong password') ||
    m.includes('ungültig')
  ) {
    return t('sudo.dialog.toast.wrongPassword')
  }
  if (m.includes('timeout') || m.includes('lange gedauert') || m.includes('too long') || m.includes('timed out')) {
    return t('sudo.dialog.toast.sudoTestTimeout')
  }
  if (m.includes('passwort erforderlich') || m.includes('password required')) {
    return t('sudo.dialog.toast.enterPassword')
  }
  return t('sudo.dialog.toast.saveFailedGeneric')
}
