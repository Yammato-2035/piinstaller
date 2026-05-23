# Setuphelfer Partitionshelfer

Geführtes Partitionierungstool für Linux – Anfängerfreundlich, auf Deutsch, mit Sicherheitsprüfungen vor jeder geplanten Aktion.

**Primäre Oberfläche:** React-Seite `frontend/src/pages/PartitionManager.tsx` (Setuphelfer-Frontend / Tauri), API unter `/api/partitions/*`.

**Fallback:** tkinter-App in diesem Ordner (`python3 start.py` oder `./scripts/start-partitionshelfer.sh`).

**Phase 1 (aktuell):** Festplatten scannen, grafische Darstellung, Sicherheitsanalyse, Use-Case-Wizards (ohne Schreiboperationen).

**Phase 2 (geplant):** Partitionen anlegen/löschen/formatieren/vergrößern – nur nach expliziter Bestätigung und Protokollierung (align mit `docs/architecture/BR-001_GATE_STRATEGY_DE.md`).

## Schnellstart

```bash
# Abhängigkeiten (einmalig)
sudo bash ./scripts/install-partitionshelfer-setup.sh

# Starten (aus Projektroot)
./scripts/start-partitionshelfer.sh
```

Oder direkt:

```bash
python3 apps/partitionshelfer/start.py
```

## Projektstruktur

```
apps/partitionshelfer/
├── core/
│   ├── disk_scanner.py      # lsblk/df – lesend, kein Root nötig
│   └── safety_checks.py     # Warnungen vor Löschen/Verkleinern
├── ui/
│   ├── main_window.py       # Hauptfenster
│   └── use_case_wizard.py   # Geführte Hilfe (4 Szenarien)
├── data/                    # Phase 2: Konfiguration/Cache
├── daemon/                  # Phase 2: privilegierte Schreiboperationen
├── start.py
├── install.sh               # tkinter + Desktop-Eintrag
└── README.md
```

## Voraussetzungen

- Linux (Debian/Ubuntu, Fedora, Arch, …)
- Python 3.10+
- `python3-tk` (tkinter)
- `util-linux` (`lsblk`)

## Sicherheit

- Systempartitionen (`/`, `/boot`, `/boot/efi`, EFI-Typ) werden beim Löschen blockiert.
- Eingehängte Partitionen werden nicht zum Löschen freigegeben.
- Schreiboperationen sind in Phase 1 **nicht** implementiert – Wizards erklären nur die Schritte.

## Einordnung in Setuphelfer

Der Partitionshelfer ist eine **eigenständige Begleit-App** (wie DSI-Radio oder Bilderrahmen), kein Ersatz für Backup/Restore/Deploy im Haupt-Backend. Er ergänzt Runbooks für neue Medien und Ersatzplatten (`docs/architecture/BR-001_GATE_STRATEGY_DE.md`).
