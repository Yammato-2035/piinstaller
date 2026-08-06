# ASUS_PREVIOUS_EVIDENCE_REVIEW — PI-RS-ASUS-EMERGENCY-LINUX-TELEMETRY-003

Stand: 2026-08-06  
Workspace: `/tmp/piinstaller-asus-emergency-linux-telemetry-003`  
Branch: `pi-rs-asus-emergency-linux-telemetry-003` @ `83126971`  
Basis: `origin/pi-rs-hw-baseline-diag-i18n-002`

Maschinenlesbar: `asus_previous_evidence_review.json`

## Methode

1. Vorgängerbericht `PI_RS_HW_BASELINE_DIAG_I18N_002_FINAL_REPORT.md` gelesen.
2. Dateisuche im **aktuellen** Worktree (`docs|build|data|scripts|backend`).
3. Zusätzlich **nur lesend** Evidence/Code auf dem lokalen Parallel-Workspace
   `/home/volker/piinstaller` (`wip/rescue-stick-extension`) erfasst — **nicht**
   ungeprüft in diesen Branch übernommen.
4. Keine alte Hardwareannahme als „gültig“ markiert ohne erneute physische Prüfung.

## Kurzfazit

Auf dem Ausgangsstand `83126971` ist G513QM nur als **experimental**-Katalogeintrag
mit Fan-Control-Evidence vorhanden. Detaillierte Boot-/GPU-/NVMe-Diagnostik und
Bootprofile liegen auf dem **nicht gemergten** Arbeitszweig und müssen für diese
Kampagne entweder kontrolliert portiert oder neu belegt werden.

| Vorbefund | Quelle | noch gültig | erneut zu prüfen | Risiko |
|-----------|--------|------------:|-----------------:|--------|
| Modell ASUS ROG Strix G513QM | `data/hardware/hardware_compat_catalog.json` (`asus-rog-strix-g513qm`); Windows-Precheck auf Parallel-Branch | teilweise (Katalog-ID vorhanden; physische Bindung offen) | ja | mittel — falsche Gerätebindung |
| DMI-Produkt `G513QM` | Katalog-Match | unbestätigt auf diesem Stick-Lauf | ja | hoch bei Write/Boot wenn falsch |
| Hybridgrafik Ryzen + RTX 3060 | `docs/hardware/g513qm-windows-precheck.md` (Parallel-Branch) | Arbeitshypothese / Doku | ja | mittel — GPU-Pfadwahl |
| BIOS-335 als Eskalation (nicht erster Schritt) | Windows-Precheck Parallel-Branch | Empfehlung dokumentiert, **nicht** als Ist-BIOS belegt | ja (Ist-BIOS lesen) | hoch bei ungeprüftem Flash — **Flash in dieser Phase verboten** |
| BIOS-331 historisch | Prompt-Annahme; **kein** belastbarer Beleg im Ausgangs-Worktree | nein / unbelegt | ja | niedrig für Code; mittel für Operator-Annahmen |
| Host-Sample BIOS `G713PI.334` | `hardware_inventory_host_sample_20260802.json` Parallel-Branch | **anderes Modell** (G713PI), nicht G513QM | nein als G513QM-Beweis | hoch bei Verwechslung |
| AMD-Grafikpfad bevorzugt | `rescue_g513qm_boot_profile.py` / lab_boot Parallel-Branch | Code-Hypothese, nicht physisch verifiziert auf 83126971 | ja | hoch (Blackscreen) |
| NVIDIA + Nouveau Blacklist in AMD-Profilen | Parallel-Branch Bootprofile | Code vorhanden außerhalb Branch | ja | mittel — Treiberkonflikt |
| `nomodeset` in Emergency/TUI | Parallel-Branch `g513qm_emergency`; MSI-Safe-Tiers auch auf 83126971 | Muster bekannt | ja (ASUS-00) | mittel |
| `amdgpu.modeset=0` in Baseline **verboten** | Parallel-Branch `cmdline_forbids_amdgpu_modeset_zero` | Policy auf Parallel-Branch | ja | mittel |
| Fehlende proprietäre NVIDIA-Module für Live-Kernel | Kernel-Pin + Vermagic-Gate Parallel-Branch; Katalog MSI-Hinweis | wahrscheinlich für Debian-Live 6.1 | ja | hoch für GUI/NVIDIA |
| Kernel-Ist Debian `6.1.0-49-amd64`, Ziel 6.8 `not_implemented` | `config/rescue/g513qm_kernel_pin.json` Parallel-Branch | Repo-Policy; nicht auf 83126971 gemergt | ja nach Build | hoch bei Modul-Mismatch |
| Zwei interne NVMe | Windows-Inspect-Sample `2x2TB_NVMe` (allgemein); Prompt | **nicht** modellspezifisch belegt für G513QM auf 83126971 | ja (Identity, nicht nvme0/1-Order) | **kritisch** bei Write/Install |
| Samsung 970 EVO Plus 2 TB | Prompt / ältere Operator-Annahme; **kein** bestätigter G513QM-Capture auf 83126971 | unbelegt hier | ja | hoch bei Gerätezuordnung |
| Windows-/Linux-Partitionen | diverse Inspect-Samples, nicht G513QM-spezifisch auf 83126971 | unbelegt für dieses Gerät | ja (read-only) | hoch bei Verwechslung |
| Schwarze Bildschirme / Hardlock bei amdgpu-Probe | Netconsole-Klassifikationen `not_conclusive` (2026-07-27) | Capture unvollständig | ja mit Netconsole/ASUS-00 | hoch |
| TUI-Pfad früher funktionierend | Emergency-Profil + MSI-TUI-Erfahrungen; G513QM physisch nicht abschließend belegt | teilweise | ja | mittel |
| Auto-Capture / Hardware-Binding | Capture-Module Parallel-Branch; Netconsole ohne MODPROBE-Marker | unvollständig | ja | mittel |
| Hardware-Baseline 1.10.1.0 vorhanden | Vorgängerbericht Phase 2–18 | **gültig als Code** auf 83126971 | Runtime auf ASUS | niedrig für Suite; hoch ohne physischen Lauf |
| Detaillierte G513QM-Evidence „pending merge“ | Katalog `known_issues.detailed_boot_diagnostics_pending_merge` | **gültig** als Meta-Befund | Port/Merge-Entscheidung | mittel |
| Fan-Control-Docs/Scripts | `docs/ASUS_ROG_FAN_CONTROL.md`, `scripts/asus-rog-fan-control.sh` | vorhanden; nicht Boot-kritisch | optional | niedrig |
| Gabriel Dual-Display-Scripts | `scripts/fix-gabriel-dual-display-*.sh` | Host-Display-Fixes, nicht Rescue-Carrier | nein für Stick-Boot | niedrig |

## Quellen auf dem Ausgangs-Branch (83126971)

- `docs/evidence/rescue/hardware-baseline-002/PI_RS_HW_BASELINE_DIAG_I18N_002_FINAL_REPORT.md`
- `data/hardware/hardware_compat_catalog.json` → `asus-rog-strix-g513qm` (experimental)
- `docs/ASUS_ROG_FAN_CONTROL.md`, `scripts/asus-rog-fan-control.sh`, `scripts/install-asusctl.sh`
- Baseline-/Compat-Module unter `backend/core/*baseline*`, `backend/rescue/hardware_baseline_*`

## Quellen nur auf Parallel-Workspace (nicht gemergt; lesend)

- `backend/core/rescue_g513qm_*.py`, `rescue_asus_rog_*.py`, `rescue_boot_tier_menu.py`
- `config/rescue/g513qm_kernel_pin.json`, `known_issues.json`
- `docs/evidence/rescue-stick/g513qm-*.md`, `kernel-pin-g513qm.md`, `README-g513qm.md`
- `docs/hardware/g513qm-windows-precheck.md`

## Verbindliche Regel für diese Kampagne

Jeder Eintrag mit „erneut zu prüfen = ja“ darf erst nach ASUS-00-Evidence
(DMI, BIOS, lspci, lsblk-Identität, Baseline) als „noch gültig“ hochgestuft werden.
Samsung-970-/BIOS-331-/„alles grün“-Claims sind bis dahin **unzulässig**.
