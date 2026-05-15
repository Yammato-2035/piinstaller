export function isTauriRuntime(): boolean {
  if (typeof window === 'undefined') return false
  return !!(window as Window & { __TAURI__?: unknown }).__TAURI__
}

export async function invokeTauriWorkspaceScan(
  workspaceRoot?: string,
): Promise<unknown> {
  const tauri = (window as Window & { __TAURI__?: { core?: { invoke: (cmd: string, args?: object) => Promise<unknown> } } })
    .__TAURI__
  if (!tauri?.core?.invoke) {
    throw new Error('tauri_invoke_unavailable')
  }
  return tauri.core.invoke('get_dev_dashboard_workspace_status', {
    workspace_root: workspaceRoot ?? null,
  })
}
