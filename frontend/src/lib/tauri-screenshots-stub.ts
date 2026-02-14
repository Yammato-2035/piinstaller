/**
 * Stub für „tauri-plugin-screenshots-api“, wenn die App im Browser läuft
 * (ohne Tauri). Wird per Vite-Alias eingebunden, damit der echte Plugin-Import
 * nicht aufgelöst werden muss. Auf einem normalen Linux-PC ohne DSI/Tauri
 * wird dieser Stub verwendet; die Funktionen werden hier nicht aufgerufen,
 * da die UI die Screenshot-Funktion nur in der Tauri-App anbietet.
 */
export async function getScreenshotableWindows(): Promise<{ id?: number; title?: string }[]> {
  return []
}

export async function getWindowScreenshot(_windowId: number): Promise<string> {
  throw new Error('Nur in der Tauri-Desktop-App verfügbar.')
}
