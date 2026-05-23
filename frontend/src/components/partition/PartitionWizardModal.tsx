/**
 * PartitionWizardModal.tsx – Geführter Anfänger-Wizard.
 */

import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { X } from 'lucide-react'

interface WizardStep {
  nr: number
  titel: string
  text: string
  warn?: string
  tipp?: string
}
interface UseCase {
  key: string
  icon: string
  titel: string
  sub: string
  schwierigkeit: string
  dauer: string
  farbe: string
  schritte: WizardStep[]
  abschluss: string
}

const USE_CASES: UseCase[] = [
  {
    key: 'externe',
    icon: '💾',
    titel: 'Externe Festplatte formatieren',
    sub: 'Für Windows, Mac und Linux nutzbar machen',
    schwierigkeit: 'Einfach',
    dauer: '3–5 Min',
    farbe: '#4CAF50',
    abschluss: 'Fertig! Dein Laufwerk ist jetzt formatiert und kann sicher ausgeworfen werden.',
    schritte: [
      {
        nr: 1,
        titel: 'Laufwerk identifizieren',
        text: 'Schau in der Liste, welches dein externes Laufwerk ist. Externe Platten heißen meist sdb, sdc usw.\n\nTipp: Stecke die Platte aus und wieder ein – das Laufwerk das neu auftaucht ist deins.',
        tipp: 'Achte auf die Größenangabe.',
      },
      {
        nr: 2,
        titel: 'Vorhandene Partitionen löschen',
        text: 'Klicke auf jede Partition des Laufwerks und lösche sie.',
        warn: 'Lösche NUR Partitionen auf deinem externen Laufwerk!',
      },
      {
        nr: 3,
        titel: 'Neue Partition erstellen',
        text: 'Erstelle eine neue Partition über den gesamten Speicher.',
        tipp: 'Eine einzige große Partition für maximale Kompatibilität.',
      },
      {
        nr: 4,
        titel: 'Dateisystem wählen',
        text: '• exFAT → Windows + Mac + Linux (empfohlen)\n• NTFS → Nur Windows\n• ext4 → Nur Linux',
        tipp: 'exFAT ist meistens die beste Wahl.',
      },
      {
        nr: 5,
        titel: 'Änderungen anwenden',
        text: 'Klicke auf Anwenden.',
        warn: 'Alle Daten werden unwiderruflich gelöscht!',
      },
    ],
  },
  {
    key: 'dualboot',
    icon: '🖥️',
    titel: 'Dual-Boot vorbereiten',
    sub: 'Windows und Linux auf einer Festplatte',
    schwierigkeit: 'Mittel',
    dauer: '15–30 Min',
    farbe: '#2196F3',
    abschluss: 'Nach der Linux-Installation wird GRUB installiert – das Startmenü für Windows und Linux.',
    schritte: [
      {
        nr: 1,
        titel: 'EFI-Partition suchen',
        text: 'Es gibt eine kleine Partition (100–500 MB) als EFI System Partition.',
        warn: 'EFI = Startprogramm für alle Betriebssysteme. Nicht anfassen!',
      },
      {
        nr: 2,
        titel: 'Windows-Partition identifizieren',
        text: 'Die größte NTFS-Partition ist Windows.',
        tipp: 'Windows ist NTFS, Linux wäre ext4.',
      },
      {
        nr: 3,
        titel: 'Windows-Partition verkleinern',
        text: 'Verkleinere um 30–50 GB für Linux.',
        warn: 'Starte Windows danach einmal und lass chkdsk laufen.',
      },
      {
        nr: 4,
        titel: 'Linux-Partition erstellen',
        text: 'Neue Partition mit ext4 im freien Bereich.',
        tipp: 'Linux-Installer kann das auch selbst.',
      },
      {
        nr: 5,
        titel: 'Anwenden & Linux installieren',
        text: 'Wende Änderungen an, starte mit Linux-USB und wähle Neben Windows installieren.',
      },
    ],
  },
  {
    key: 'linux',
    icon: '🐧',
    titel: 'Linux frisch installieren',
    sub: 'Gesamte Festplatte für Linux vorbereiten',
    schwierigkeit: 'Einfach',
    dauer: '10–15 Min',
    farbe: '#9C27B0',
    abschluss: 'Starte den Linux-Installer und wähle Partitionen manuell belegen.',
    schritte: [
      {
        nr: 1,
        titel: 'Alle Partitionen löschen',
        text: 'Lösche alle vorhandenen Partitionen.',
        warn: 'Wähle die richtige Festplatte! Externe Laufwerke vorher abziehen.',
      },
      {
        nr: 2,
        titel: 'EFI-Partition erstellen',
        text: '512 MB, FAT32, Typ: EFI System Partition.',
        tipp: 'Diese braucht dein Computer zum Starten.',
      },
      {
        nr: 3,
        titel: 'Swap-Partition (optional)',
        text: '< 4 GB RAM: doppelter RAM\n4–8 GB RAM: RAM-Größe\n> 8 GB RAM: 2–4 GB',
        tipp: 'Linux richtet Swap-Dateien automatisch ein.',
      },
      { nr: 4, titel: 'Root-Partition erstellen', text: 'Rest der Festplatte, ext4, Einhängepunkt: /' },
      {
        nr: 5,
        titel: 'Anwenden & Linux installieren',
        text: 'Wende Änderungen an und starte mit dem Linux-USB-Stick.',
      },
    ],
  },
  {
    key: 'speicher',
    icon: '📊',
    titel: 'Speicherplatz freimachen',
    sub: 'Partition vergrößern wenn der Platz knapp wird',
    schwierigkeit: 'Mittel',
    dauer: '10–20 Min',
    farbe: '#FF9800',
    abschluss: 'Prüfe mit df -h im Terminal die neue Größe.',
    schritte: [
      {
        nr: 1,
        titel: 'Platzsituation analysieren',
        text: 'Suche eine Nachbarpartition mit viel freiem Speicher.',
        tipp: 'Partitionen können nur vergrößert werden wenn direkt daneben freier Platz ist.',
      },
      {
        nr: 2,
        titel: 'Nachbarpartition verkleinern',
        text: 'Verkleinere um den benötigten Betrag.',
        warn: 'Systempartitionen nur von Live-USB aus ändern!',
      },
      { nr: 3, titel: 'Volle Partition vergrößern', text: 'Klicke die Partition an und wähle Vergrößern.' },
      { nr: 4, titel: 'Anwenden & prüfen', text: 'Anwenden, dann Neustart.', tipp: 'Nach dem Anwenden: Neustart empfohlen.' },
    ],
  },
]

interface Props {
  onClose: () => void
}

const PartitionWizardModal: React.FC<Props> = ({ onClose }) => {
  const { t } = useTranslation()
  const [selected, setSelected] = useState<UseCase | null>(null)
  const [schritt, setSchritt] = useState(0)
  const [fertig, setFertig] = useState(false)

  const handleWeiter = () => {
    if (!selected) return
    if (schritt < selected.schritte.length - 1) setSchritt((s) => s + 1)
    else setFertig(true)
  }

  const handleBack = () => {
    if (fertig) {
      setFertig(false)
      return
    }
    if (schritt > 0) {
      setSchritt((s) => s - 1)
      return
    }
    setSelected(null)
  }

  return (
    <div
      className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="bg-slate-800 border border-slate-700 rounded-2xl w-full max-w-xl overflow-hidden flex flex-col max-h-[85vh]">
        <div className="bg-slate-800/80 border-b border-slate-700/50 px-5 py-4 flex items-center justify-between">
          <h2 className="text-base font-bold text-teal-400">
            {selected ? `${selected.icon} ${selected.titel}` : t('partition.wizard.title')}
          </h2>
          <button type="button" onClick={onClose} className="text-slate-500 hover:text-slate-300">
            <X className="w-5 h-5" />
          </button>
        </div>

        {selected && !fertig && (
          <div className="px-5 pt-3">
            <div className="flex justify-between text-xs text-slate-500 mb-1.5">
              <span>{t('partition.wizard.step', { current: schritt + 1, total: selected.schritte.length })}</span>
              <div className="flex gap-1">
                {selected.schritte.map((_, i) => (
                  <span
                    key={i}
                    style={{ color: i < schritt ? '#4CAF50' : i === schritt ? selected.farbe : '#334155' }}
                    className="text-[10px]"
                  >
                    ●
                  </span>
                ))}
              </div>
            </div>
            <div className="h-0.5 bg-slate-700 rounded-full overflow-hidden mb-1">
              <div
                className="h-full rounded-full transition-all duration-300"
                style={{
                  width: `${((schritt + 1) / selected.schritte.length) * 100}%`,
                  background: selected.farbe,
                }}
              />
            </div>
          </div>
        )}

        <div className="flex-1 overflow-y-auto px-5 py-4">
          {!selected && (
            <div className="space-y-2">
              {USE_CASES.map((uc) => (
                <button
                  key={uc.key}
                  type="button"
                  onClick={() => {
                    setSelected(uc)
                    setSchritt(0)
                    setFertig(false)
                  }}
                  className="w-full flex items-center gap-0 bg-slate-700/40 hover:bg-slate-700/70 border border-slate-700/50 rounded-xl overflow-hidden transition-colors text-left"
                >
                  <div className="w-1 self-stretch" style={{ background: uc.farbe }} />
                  <span className="text-3xl px-3 py-3">{uc.icon}</span>
                  <div className="flex-1 py-3">
                    <div className="font-semibold text-slate-200 text-sm">{uc.titel}</div>
                    <div className="text-xs text-slate-500 mt-0.5">{uc.sub}</div>
                    <div className="flex gap-3 mt-1.5">
                      <span
                        className={`text-[10px] font-medium ${uc.schwierigkeit === 'Einfach' ? 'text-emerald-400' : 'text-amber-400'}`}
                      >
                        ● {uc.schwierigkeit}
                      </span>
                      <span className="text-[10px] text-slate-600">⏱ {uc.dauer}</span>
                    </div>
                  </div>
                  <span className="text-2xl px-3" style={{ color: uc.farbe }}>
                    ›
                  </span>
                </button>
              ))}
            </div>
          )}
          {selected &&
            !fertig &&
            (() => {
              const s = selected.schritte[schritt]
              return (
                <div className="space-y-4">
                  <h3 className="font-bold text-slate-200 text-base">
                    {s.nr}. {s.titel}
                  </h3>
                  <p className="text-sm text-slate-400 leading-relaxed whitespace-pre-line">{s.text}</p>
                  {s.warn && (
                    <div className="border-l-2 border-amber-400 bg-amber-900/20 rounded-r-lg px-3 py-2">
                      <p className="text-xs text-amber-200">⚠️ {s.warn}</p>
                    </div>
                  )}
                  {s.tipp && (
                    <div className="border-l-2 border-emerald-500 bg-emerald-900/20 rounded-r-lg px-3 py-2">
                      <p className="text-xs text-emerald-300 italic">💡 {s.tipp}</p>
                    </div>
                  )}
                </div>
              )
            })()}
          {selected && fertig && (
            <div className="text-center py-6">
              <div className="text-5xl mb-4" style={{ color: selected.farbe }}>
                ✓
              </div>
              <h3 className="font-bold text-slate-200 text-lg mb-3">{t('partition.wizard.allDone')}</h3>
              <p className="text-sm text-slate-400 leading-relaxed max-w-sm mx-auto">{selected.abschluss}</p>
            </div>
          )}
        </div>

        <div className="border-t border-slate-700/50 bg-slate-800/60 px-5 py-3 flex items-center justify-between">
          <button
            type="button"
            onClick={selected ? handleBack : onClose}
            className="px-4 py-2 rounded-lg bg-slate-700/60 text-slate-400 text-sm hover:bg-slate-700 transition-colors"
          >
            {!selected
              ? t('partition.wizard.close')
              : schritt === 0 && !fertig
                ? `← ${t('partition.wizard.overview')}`
                : `← ${t('partition.wizard.back')}`}
          </button>
          {selected && !fertig && (
            <button
              type="button"
              onClick={handleWeiter}
              style={{ background: selected.farbe }}
              className="px-5 py-2 rounded-lg text-slate-900 text-sm font-bold hover:opacity-90"
            >
              {schritt === selected.schritte.length - 1
                ? `✓ ${t('partition.wizard.done')}`
                : `${t('partition.wizard.next')} →`}
            </button>
          )}
          {selected && fertig && (
            <button
              type="button"
              onClick={onClose}
              style={{ background: selected.farbe }}
              className="px-5 py-2 rounded-lg text-slate-900 text-sm font-bold"
            >
              {t('partition.wizard.close')}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

export default PartitionWizardModal
