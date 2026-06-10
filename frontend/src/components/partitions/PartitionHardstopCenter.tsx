/**
 * Hardstop Center – verständliche Sicherheitsblockaden (read-only).
 */

import React from 'react'
import { useTranslation } from 'react-i18next'
import { ShieldAlert, AlertTriangle, Ban } from 'lucide-react'
import type { DiskInfo, HardstopMessage } from '../../api/partitionApi'
import { diskRoleLabel } from '../../lib/partition/partitionRoleUtils'
import { TOOL_SHELL } from '../../lib/theme/setuphelferToolTheme'

interface Props {
  disk: DiskInfo | null
  hardstops: HardstopMessage[]
  warnings?: HardstopMessage[]
}

function normalizeCode(code: string): string {
  return code.replace(/^partition\.hardstop\./, '').replace(/^partition\.warning\./, '')
}

function evidenceFromCode(code: string): string[] {
  const short = normalizeCode(code)
  const map: Record<string, string[]> = {
    target_is_windows_system_disk: ['EFI', 'NTFS', 'Recovery'],
    target_is_linux_system_disk: ['EFI', 'Linux Root', 'Boot'],
    target_is_rescue_stick: ['EFI', 'Rescue-Marker', 'USB'],
    target_is_backup_source: ['Backup-Quelle'],
    readonly_phase2: ['Read-Only-Phase'],
  }
  return map[short] ?? []
}

const PartitionHardstopCenter: React.FC<Props> = ({ disk, hardstops, warnings = [] }) => {
  const { t, i18n } = useTranslation()
  const lang = i18n.language.startsWith('de') ? 'de' : 'en'

  if (!disk && hardstops.length === 0 && warnings.length === 0) {
    return null
  }

  const roleLabel = disk ? diskRoleLabel(disk, lang) : null

  const resolve = (code: string) => {
    const short = normalizeCode(code)
    const base = `hardstops.codes.${short}`
    return {
      title: t(`${base}.title`, { defaultValue: t(`partition.phase2.code.${code}`, code) }),
      explanation: t(`${base}.explanation`, { defaultValue: '' }),
      action: t(`${base}.action`, { defaultValue: '' }),
      reasons: evidenceFromCode(code),
    }
  }

  return (
    <section className={`${TOOL_SHELL.panel} p-4 sm:p-5 space-y-4`} data-testid="partition-hardstop-center">
      <div className="border-b border-slate-700/50 pb-3">
        <h3 className={`${TOOL_SHELL.panelHeader} text-amber-200`}>
          {t('partitionWorkbench.hardstopCenter.title')}
        </h3>
        <p className="text-xs text-slate-500 mt-1">{t('partitionWorkbench.hardstopCenter.subtitle')}</p>
      </div>

      {hardstops.length === 0 && warnings.length === 0 && disk && (
        <div className="rounded-lg border border-emerald-600/35 bg-emerald-950/30 px-4 py-4 text-sm text-emerald-100" data-testid="partition-hardstop-center-clear">
          {t('partitionWorkbench.hardstopCenter.noBlockers')}
        </div>
      )}

      {hardstops.map((h) => {
        const info = resolve(h.code)
        const short = normalizeCode(h.code)
        return (
          <article
            key={h.code}
            className="rounded-lg border-2 border-red-500/50 bg-red-950/40 px-5 py-5"
            data-testid={`partition-hardstop-center-${short}`}
          >
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-lg bg-red-500/20 flex items-center justify-center shrink-0">
                <ShieldAlert className="w-7 h-7 text-red-300" />
              </div>
              <div className="min-w-0 flex-1 space-y-3">
                <h4 className="text-lg font-black text-red-50 uppercase tracking-wide">
                  {roleLabel ? `⚠ ${roleLabel}` : info.title}
                </h4>
                {info.explanation && <p className="text-sm text-red-100/90">{info.explanation}</p>}
                {info.reasons.length > 0 && (
                  <div>
                    <p className="text-xs font-bold uppercase tracking-wider text-red-300/80 mb-1">
                      {t('partitionWorkbench.hardstopCenter.reasons')}
                    </p>
                    <ul className="flex flex-wrap gap-2">
                      {info.reasons.map((r) => (
                        <li
                          key={r}
                          className="text-xs font-semibold px-2.5 py-1 rounded border border-red-500/35 bg-red-950/50 text-red-100"
                        >
                          {r}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                <p className="text-sm font-semibold text-red-200 flex items-center gap-2">
                  <Ban className="w-4 h-4" />
                  {t('partitionWorkbench.hardstopCenter.writeBlocked')}
                </p>
                {info.action && (
                  <p className="text-sm text-slate-300 border-t border-red-500/25 pt-3">
                    <strong>{t('partitionWorkbench.hardstopCenter.recommendation')}:</strong> {info.action}
                  </p>
                )}
              </div>
            </div>
          </article>
        )
      })}

      {warnings.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-xs font-bold uppercase tracking-widest text-amber-300 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4" />
            {t('hardstops.warningsTitle')}
          </h4>
          {warnings.map((w) => {
            const info = resolve(w.code)
            return (
              <div key={w.code} className="rounded-lg border border-amber-500/35 bg-amber-950/30 px-4 py-3 text-sm text-amber-100">
                <p className="font-bold">{info.title}</p>
                <p className="mt-1 opacity-90">{info.explanation || w.message}</p>
              </div>
            )
          })}
        </div>
      )}
    </section>
  )
}

export default PartitionHardstopCenter
