export type BackupSelection =
  | 'recommended'
  | 'fast-system'
  | 'user-data'
  | 'developer'
  | 'full-expert'
  | 'incremental'
  | 'data'

/**
 * Baut den JSON-Body für POST /api/backup/create (kein Netzwerk).
 * Abwärtskompatibel: `incremental` / `data`; Profile über `type: profile` + `profile`.
 */
export function buildBackupCreateBody(
  selection: BackupSelection,
  args: { backupDir: string; target: string; async: boolean; confirmFullExpert: boolean },
): Record<string, unknown> {
  const base: Record<string, unknown> = {
    backup_dir: args.backupDir,
    target: args.target,
    async: args.async,
  }
  if (selection === 'incremental') {
    return { ...base, type: 'incremental' }
  }
  if (selection === 'data') {
    return { ...base, type: 'data', profile: 'recommended' }
  }
  const body: Record<string, unknown> = { ...base, type: 'profile', profile: selection }
  if (selection === 'full-expert') {
    body.confirm_full_expert = args.confirmFullExpert
  }
  return body
}
