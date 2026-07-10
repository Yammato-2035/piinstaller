# PI-RS-MSI-RETEST-001 — Operator Runbook (Vorbereitung)

**Hinweis:** Dieser Sprint führt **keinen** Boot-Retest aus. Operator-Go für PI-RS-MSI-RETEST-002 erforderlich.

## Vorbereitung (am Entwicklungsrechner)

1. Stick-Version bestätigt: **1.10.0.12** (`SETUPHELFER/setuphelfer/rescue/version.json`)
2. SquashFS-SHA256: `1a72046a40a504e62771a8fc8cd4b6360951c3ac0a4e352a8248fc68f14487e6`
3. **Kein USB-Update** in diesem Sprint
4. Foto/Notiz: SETUPHELFER + SETUP_LOGS Labels, Größen

## Am MSI GE63 Raider

1. USB-Stick einstecken (SETUPHELFER + SETUP_LOGS)
2. UEFI-Boot vom Stick wählen
3. GRUB-Menü abwarten
4. **Zuerst TUI** testen (Text-Modus)
5. **Dann GUI** testen (falls vorgesehen)
6. **Keine Reparatur** ausführen
7. **Keine produktive Telemetry** aktivieren (`preview_only` beibehalten)
8. Netzwerk nur wenn Lab-Preview benötigt (localhost-Kontext)

## Nach dem Test

1. Normal herunterfahren
2. Stick an Entwicklungsrechner
3. `SETUP_LOGS` sichern gemäß `PI_RS_MSI_RETEST_001_IMPORT_AND_REVIEW.md`
4. Ergebnis an PI-RS-MSI-RETEST-002 übergeben

## Verboten ohne separates Go

- USB beschreiben / Payload aktualisieren
- `dd`, `mkfs`, `parted`, Repack-Scripts
- Produktiver Telemetry/Diagnostics Send
