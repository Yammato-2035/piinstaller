# R.6 — Persistence Boot-Hook Audit

**Datum:** 2026-06-10  
**Scope:** Read-only Code-Audit (Workspace)

## Komponenten

| Komponente | Rolle |
|------------|-------|
| `setuphelfer-rescue-start-assistant` | systemd `--boot-trigger`, TUI/Kiosk-Einstieg |
| `setuphelfer-rescue-common.sh` | `fat_esp_mount`, `mirror_evidence_file`, `record_menu_evidence` |
| `setuphelfer-rescue-evidence.py` | CLI: bundle, matrix, boot, menu-action |
| `core/rescue_persistence.py` | Stick-Erkennung, Evidence-Baum, **R.6** `initialize_boot_evidence_marker` |
| `core/rescue_boot_logger.py` | Boot-Bundle (spät, unter `boot/`) |
| `core/rescue_evidence_bundle.py` | Gesamt-Bundle am Assistenten-Ende |

## Audit-Fragen

| Frage | Befund (vor R.6) | Befund (nach R.6) |
|-------|------------------|-------------------|
| Wer erzeugt `/setuphelfer-evidence`? | `ensure_rescue_evidence_tree()` in `rescue_persistence.py` | unverändert |
| Wann wird es erzeugt? | Nur bei explizitem `bundle`/matrix/menu — **nicht früh** | **früh** via `boot-evidence-init` am Assistenten-Start |
| FAT32-Stick-Mount gefunden? | `detect_rescue_stick_mount`: `/run/live/medium`, `/lib/live/mount/medium`, `/media/*/SETUPHELFER` | + remount rw Versuch |
| `/run/live/medium` im Live-System? | **ja** (Debian live-boot Standard) | **ja** |
| Fallback `/tmp/setuphelfer-evidence`? | **ja**, mit `warning` | **ja** |
| Fallback sichtbar auf Stick kopiert? | **nein** (nur Legacy-Mirror nach `setuphelfer/evidence/`) | **nein** (by design; TUI zeigt RAM-Fallback) |
| `evidence.py` beim Boot/TUI-Start? | **nein** (nur Ende + menu-action) | **ja** (`boot-init` Subcommand) |

## Kritischer Pfad (vor Fix)

```
systemd → start-assistant --boot-trigger
  → (optional) exec ui-launch SOFORT
  → … TUI-Schritte …
  → setuphelfer_rescue_run_evidence_bundle (Ende)
```

**Lücke:** Kein früher Aufruf von `initialize_boot_evidence_marker`. Bei Kiosk-`exec` ohne TUI-Welcome entstand **gar kein** kanonischer Boot-Marker.

## Legacy-Mirror (nicht kanonisch)

`setuphelfer_rescue_mirror_evidence_file` schreibt nach `setuphelfer/evidence/` und `setuphelfer/logs/` auf FAT — **nicht** nach `/setuphelfer-evidence/`.

## R.6-Fix

1. Skript `setuphelfer-rescue-boot-evidence-init` → `evidence.py boot-init`
2. `initialize_boot_evidence_marker()` schreibt `boot/boot_marker.json` + `boot/boot_marker.md`
3. `start-assistant` ruft Hook **vor** `--boot-trigger`/UI-`exec` auf
4. TUI zeigt: `Evidence: Stick` | `Evidence: RAM fallback` | `Evidence: failed`
5. Menüaktionen loggen weiter nach `menu/` via `record_menu_evidence`

## Ampel

| Check | Status |
|-------|--------|
| Früher Hook vorhanden (pre-fix) | **rot** |
| Hook implementiert (workspace) | **grün** |
| Im aktuellen Stick-Image | **gelb** (Rebuild/Write ausstehend) |
