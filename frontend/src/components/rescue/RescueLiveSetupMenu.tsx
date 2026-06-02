import React from 'react'

type RescueLiveSetupMenuProps = {
  language?: 'de' | 'en'
}

export function RescueLiveSetupMenu({ language = 'de' }: RescueLiveSetupMenuProps) {
  const de = language === 'de'
  return (
    <section className="rounded-xl border border-amber-700/50 bg-slate-900/70 p-4" data-testid="rescue-live-menu-stub">
      <h2 className="text-lg font-semibold text-white mb-1">Setuphelfer Rescue Live Menü</h2>
      <p className="text-xs text-amber-300 mb-4">
        {de
          ? 'Vorschau / Sicherheitsmenü - keine Reparatur ohne spätere Freigabe.'
          : 'Preview / safety menu - no repair without later approval.'}
      </p>
      <ul className="grid gap-2 text-sm text-slate-200">
        <li>Sicherheit: Firewall aktivieren (checked, locked, required), Schreiboperationen deaktiviert</li>
        <li>Development Server: Suche, Pairing-Code, Verbindungsstatus, Heartbeat, Report übertragen</li>
        <li>Hardware: CPU, RAM, Firmware, Secure Boot, Netzwerkadapter</li>
        <li>Festplatten: Datenträger, Systemdisk, externe Datenträger, Backup-Kandidaten, SMART (falls vorhanden)</li>
        <li>Bootoptionen: EFI-Partitionen, Betriebssysteme, Bootloader-Hinweise, Bootreparatur nur Vorschau</li>
        <li>Diagnose/Evidence: lokaler Bericht, verschlüsselter Report, USB-Log-Export deaktiviert</li>
        <li>Sprache/Tastatur/Anzeige: Deutsch/Englisch, Layout, Fallback-Textmodus</li>
      </ul>
    </section>
  )
}

