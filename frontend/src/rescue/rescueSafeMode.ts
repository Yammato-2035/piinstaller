/** Non-destructive UI walk — blocks execute paths when RESCUE_UI_SAFE_WALK=1 or ?safe_walk=1 */

declare global {
  interface Window {
    RESCUE_UI_SAFE_WALK?: string;
  }
}

export function isRescueUiSafeWalk(): boolean {
  if (typeof window === 'undefined') return false;
  const params = new URLSearchParams(window.location.search);
  if (params.get('safe_walk') === '1') return true;
  if (window.RESCUE_UI_SAFE_WALK === '1') return true;
  const env = (import.meta as { env?: Record<string, string> }).env?.VITE_RESCUE_UI_SAFE_WALK;
  if (env === '1') return true;
  return false;
}

export function safeWalkBlockedMessage(action: string): string {
  return `Safe-Walk: ${action} blockiert (keine destruktive Aktion).`;
}
