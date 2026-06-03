import React from 'react'
import { useTranslation } from 'react-i18next'

type RescueLiveSetupMenuProps = {
  language?: 'de' | 'en'
}

export function RescueLiveSetupMenu({ language = 'de' }: RescueLiveSetupMenuProps) {
  const { t, i18n } = useTranslation()
  const de = (language || i18n.language || 'de').startsWith('de')

  const preview = de
    ? 'Vorschau / Sicherheitsmenü – keine Reparatur ohne spätere Freigabe.'
    : 'Preview / safety menu – no repair without later approval.'

  return (
    <section className="rounded-xl border border-amber-700/50 bg-slate-900/70 p-4" data-testid="rescue-live-menu-stub">
      <h2 className="text-lg font-semibold text-white mb-1">
        {t('rescueLiveMenu.title', 'Setuphelfer Rescue Live Menü')}
      </h2>
      <p className="text-xs text-amber-300 mb-4">{preview}</p>

      <div className="grid gap-4 text-sm text-slate-200">
        <section>
          <h3 className="font-semibold text-white mb-2">{de ? '1. Sicherheit' : '1. Security'}</h3>
          <label className="flex items-center gap-2 opacity-90">
            <input type="checkbox" checked readOnly disabled className="accent-emerald-500" />
            <span>{de ? 'Firewall aktivieren – erforderlich (gesperrt)' : 'Enable firewall – required (locked)'}</span>
          </label>
          <p className="text-xs text-slate-400 mt-1">
            {de ? 'Schreiboperationen, Restore und Backup sind deaktiviert.' : 'Write ops, restore and backup are disabled.'}
          </p>
          <p className="text-xs text-slate-400">{de ? 'E2EE-Verbindung: erforderlich' : 'E2EE connection: required'}</p>
        </section>

        <section>
          <h3 className="font-semibold text-white mb-2">{de ? '2. Development Server' : '2. Development Server'}</h3>
          <ul className="list-disc pl-5 space-y-1 text-xs">
            <li>{de ? 'Server suchen (Discovery-Stub)' : 'Search server (discovery stub)'}</li>
            <li>{de ? 'Pairing-Code anzeigen' : 'Show pairing code'}</li>
            <li>{de ? 'Verbindungsstatus / letzter Heartbeat' : 'Connection status / last heartbeat'}</li>
            <li>{de ? 'Verschlüsselten Report übertragen' : 'Send encrypted report'}</li>
          </ul>
        </section>

        <section>
          <h3 className="font-semibold text-white mb-2">{de ? '3. Hardware' : '3. Hardware'}</h3>
          <p className="text-xs text-slate-400">CPU · RAM · UEFI/BIOS · Secure Boot · Netzwerkadapter (Stub)</p>
        </section>

        <section>
          <h3 className="font-semibold text-white mb-2">{de ? '4. Festplatten' : '4. Storage'}</h3>
          <p className="text-xs text-slate-400">
            {de
              ? 'Datenträgerliste, Systemdisk, externe Datenträger, Backup-Kandidaten, SMART (falls vorhanden)'
              : 'Device list, system disk, external disks, backup candidates, SMART if available'}
          </p>
        </section>

        <section>
          <h3 className="font-semibold text-white mb-2">{de ? '5. Bootoptionen' : '5. Boot options'}</h3>
          <p className="text-xs text-slate-400">
            {de ? 'EFI-Partitionen, erkannte OS, Bootloader-Hinweise – Bootreparatur nur Vorschau' : 'EFI partitions, detected OS, bootloader hints – repair preview only'}
          </p>
        </section>

        <section>
          <h3 className="font-semibold text-white mb-2">{de ? '6. Diagnose / Evidence' : '6. Diagnostics / evidence'}</h3>
          <button type="button" disabled className="text-xs px-2 py-1 rounded bg-slate-800 text-slate-500 mr-2">
            {de ? 'USB-Log exportieren (deaktiviert)' : 'Export USB log (disabled)'}
          </button>
          <span className="text-xs text-slate-400">{de ? 'Lokalen / verschlüsselten Bericht erzeugen (Stub)' : 'Generate local / encrypted report (stub)'}</span>
        </section>

        <section>
          <h3 className="font-semibold text-white mb-2">{de ? '7. Sprache / Tastatur' : '7. Language / keyboard'}</h3>
          <p className="text-xs text-slate-400">{de ? 'Deutsch / Englisch, Layout, Fallback-Textmodus' : 'German / English, layout, fallback text mode'}</p>
        </section>
      </div>
    </section>
  )
}
