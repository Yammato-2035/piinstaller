# RS-001 Live Medium Retest Handoff — 1.7.11.0

**Datum:** 2026-06-10  
**Version:** `1.7.11.0`  
**RS-001:** **yellow**  
**Stick Acceptance:** **ok**  
**Ready for operator hardware retest:** **true**

## Stick-Stand

```text
Version (SquashFS): 1.7.11.0
SquashFS SHA256: a3e58964ffffe032fd7e543e5e28bd64156981347647a0ba9208101cb9d7726d
Acceptance: ok (Level 1–4)
GRUB Branding: ok
```

## Acceptance erneut prüfen (optional vor Boot)

```bash
cd /home/volker/piinstaller

./scripts/rescue-live/check-rs001-stick-acceptance.sh \
  --target /dev/sdb \
  --expected-squashfs-sha256 a3e58964ffffe032fd7e543e5e28bd64156981347647a0ba9208101cb9d7726d
```

Erwartung: `acceptance_status=ok`, `hardware_retest_allowed=true`

## Hardware-Retest Level 6 (Operator)

1. Rechner vollständig herunterfahren
2. Stick `/dev/sdb` (SETUPHELFER) einstecken
3. UEFI → USB → GRUB mit Setuphelfer-Theme
4. „Setuphelfer Rettung starten“ wählen
5. **Kein** Backup/Restore/Repair/Install starten

## Erfolgskriterium (RS-001 green)

```text
Nutzbares Setuphelfer-Menü (Kiosk ODER Fallback-TUI mit Auswahl)
Netzwerk verbinden crasht nicht — Rückkehr ins Menü
GRUB mit Logo/Theme sichtbar
Keine rohen failed-Units im Anfängerflow
```

## Nach Retest

Evidence: `RS_001_REACT_RESCUE_HARDWARE_RETEST_RESULT.md`, Stick-Logs von ESP exportieren.
