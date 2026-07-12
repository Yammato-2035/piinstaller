# PI-RS-MSI-RETEST-002 — Ergebnis (nach physischem Boot)

Stand: 2026-07-12  
Session: **`20260712_111206_boot`**  
Gesamtstatus: **`failed`**

## Zusammenfassung

Der physische Boot-Retest auf dem MSI GE63 mit Payload **1.10.0.15** (SHA256 verifiziert) ist **fehlgeschlagen**. Der Operator berichtet: **Text-GUI (TUI) wurde wieder zerstört**.

## Was funktionierte

| Prüfung | Ergebnis |
|---------|----------|
| GE63 bootet | ja |
| MSI-Compat in cmdline | ja (`setuphelfer_msi_compat=1`) |
| `gui-availability.json` | `gui_available=false`, Grund `msi_compat_nomodeset` |
| `gui-fallback.json` | `openvt_attempted=false`, `startx_attempted=false` |
| Xorg-Log | nicht vorhanden (kein Xorg-Start) |
| Interne Platte beschrieben | nein |

## Was fehlschlug

| Problem | Evidence |
|---------|----------|
| **TUI visuell zerstört** | Operator-Meldung |
| **Boot-Progress startet GUI-Pfad** | `boot-timeline.jsonl` 11:12:22: Phase `x11_starting` — „Grafische Oberfläche wird gestartet …“ |
| **Runtime-Version-Drift** | ESP-Metadaten `1.10.0.15`, aber `/api/version` und `opt/setuphelfer-rescue/config/version.json` im SquashFS = **1.10.0.12** |
| **Stale GUI-Logs** | `gui-start.log` / `rescue-ui-status.json` noch von Session `20260712_015909` (openvt-Fehler) |

## Root-Cause-Hypothese (kein Fix in diesem Sprint)

1. **Boot-Progress** (`setuphelfer-rescue-boot-progress`) zeigt unter MSI-Compat weiterhin die Phase `x11_starting` auf tty1 — das kann die TUI optisch zerstören, obwohl der GUI-Watchdog blockiert ist.
2. **Console-Shield** (`tty1_clear_allowed=false` während `early_boot_progress`) verhindert tty1-Bereinigung während Boot-Meldungen.
3. **Versions-Sync** im Repack/Updater unvollständig — Runtime meldet noch 1.10.0.12.

## Korrekte Aussage

Die GUI-Sperre unter MSI-Compat ist in den Metadaten (`gui-availability.json`) vorhanden, aber die **Textoberfläche bleibt nicht stabil** — der Retest ist **nicht bestanden**.

**Nicht** schreiben: „Die GUI funktioniert auf dem MSI.“

## Nächster empfohlener Schritt

**PI-RS-MSI-GUI-003** — Boot-Progress und tty1-Shield unter MSI-Compat: keine `x11_starting`-Phase, keine tty1-Überlagerung während TUI-Start.

Parallel:

- **PI-RS-USB-UPDATER-001** — Runtime-`project_version` im SquashFS atomar synchronisieren

## Evidence

`docs/evidence/pi_rs_msi_retest_002/msi_session/` (Session `20260712_111206_boot`)
