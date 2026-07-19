# PI-RS-MSI-RETEST-003B — Spät-Evidence Runbook

**Payload:** 1.10.0.16  
**Vorgänger-Session (nicht wiederverwenden):** `20260712_225043_boot`

## Vor dem Boot (Entwicklungsrechner — erledigt)

- Payload SHA256 + Gates verifiziert
- SETUP_LOGS Vorher-Inventar: `/tmp/pi_rs_msi_retest_003b_before.txt`
- Stick power-off

## Boot am MSI

1. MSI herunterfahren, nur Setuphelfer-Stick.
2. **„Setuphelfer MSI/NVIDIA Kompatibilitaetsmodus (Text)“** wählen.
3. TUI erscheint → **Startzeit notieren**.
4. **Mindestens 120 Sekunden warten** — keinen Evidence-Collector starten.
5. TUI-Stabilität prüfen (kein Boottext über Whiptail, Tastatur ok).

## Spät-Evidence (erst nach ≥120 s) — auf dem MSI ausführen

Shell/TUI-Diagnose öffnen (read-only). Block **einmal** ausführen:

```bash
LATE_DIR="/run/setuphelfer/esp-rw/setuphelfer/evidence/msi-rs011b"
mkdir -p "$LATE_DIR"
OUT="$LATE_DIR/late-evidence-003b-$(date -u +%Y%m%d_%H%M%S).txt"
{
  echo "=== LATE EVIDENCE PI-RS-MSI-RETEST-003B ==="
  date --iso-8601=seconds
  echo "--- uptime ---"
  cat /proc/uptime
  echo "--- cmdline ---"
  cat /proc/cmdline
  echo "--- run/setuphelfer files ---"
  find /run/setuphelfer -maxdepth 6 -type f 2>/dev/null | sort
  echo "--- console ownership grep ---"
  grep -R -nE 'console_owner|tui_owned|boot_progress_write_allowed|boot_progress_clear_allowed|tty1_write_allowed|tty1_clear_allowed|gui_transition_allowed|RESCUE_CONSOLE_WRITE_BLOCKED_TUI_OWNED' \
    /run/setuphelfer /var/log/setuphelfer /tmp/setuphelfer 2>/dev/null || true
  echo "--- timeline grep ---"
  grep -R -nE 'tui_mode_selected|tui_owned|x11_starting|gui_starting|openvt|startx|Xorg|chromium|msi_compat' \
    /run/setuphelfer /var/log/setuphelfer /tmp/setuphelfer 2>/dev/null || true
  echo "--- console-ownership.json ---"
  cat /run/setuphelfer/console-ownership.json 2>/dev/null || echo "MISSING"
  echo "--- current-session.json ---"
  cat /run/setuphelfer/current-session.json 2>/dev/null || echo "MISSING"
  echo "--- boot-timeline tail ---"
  tail -30 /run/setuphelfer-rescue/boot-timeline.jsonl 2>/dev/null \
    || tail -30 /var/log/setuphelfer/boot-timeline.jsonl 2>/dev/null || echo "MISSING"
  echo "--- processes ---"
  ps -ef | grep -E 'openvt|chvt|startx|Xorg|Xorg.bin|chromium|whiptail' | grep -v grep || true
  echo "--- X11 sockets ---"
  find /tmp/.X11-unix -maxdepth 1 -type s -print 2>/dev/null || true
} | tee "$OUT"
echo "Wrote: $OUT"
sync
```

**Wichtig:** Nicht vor 120 s ausführen. Nicht `collect-msi-rs011b-evidence.sh` vorher starten.

## Nach Spät-Evidence

1. Read-only Menünavigation + GUI-Sperrmeldung testen.
2. Über TUI herunterfahren.
3. Stick am Entwicklungsrechner einstecken → Agent importiert **nur neue Session**.

## Erwartete Zielwerte

| Feld | Erwartung |
|------|-----------|
| uptime | ≥ 120 s |
| console_owner | `tui` |
| boot_progress_write_allowed | false |
| boot_progress_clear_allowed | false |
| x11_starting | nicht in aktueller Timeline |
| openvt/startx/Xorg | nicht laufend |
