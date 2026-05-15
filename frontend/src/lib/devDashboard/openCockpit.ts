import { cockpitUrl, COCKPIT_WINDOW_LABEL, isCockpitWindow } from './cockpitWindow'
import { isTauriRuntime } from './isTauri'

export async function openDevelopmentCockpit(): Promise<'tauri' | 'window' | 'already'> {
  if (isCockpitWindow()) return 'already'

  if (isTauriRuntime()) {
    const tauri = (window as Window & { __TAURI__?: { core?: { invoke: (cmd: string) => Promise<unknown> } } })
      .__TAURI__
    if (tauri?.core?.invoke) {
      await tauri.core.invoke('open_development_cockpit')
      return 'tauri'
    }
  }

  window.open(cockpitUrl(), COCKPIT_WINDOW_LABEL, 'noopener,noreferrer,width=1440,height=900')
  return 'window'
}
