# PI-RS-MSI-GUI-003 FAQ (DE)

Stand: **2026-07-13**  
Payload: **1.10.0.20** auf physischem Stick · Retest **passed** (Session `20260713_003100_boot`)

Ausführlich: [MSI_TUI_CONSOLE_ISOLATION_KB_DE.md](../knowledge-base/rescue/MSI_TUI_CONSOLE_ISOLATION_KB_DE.md)

---

## Warum war die Textoberfläche auf dem MSI GE63 trotz GUI-Sperre kaputt?

**Kurz:** PI-RS-MSI-GUI-002 blockierte den echten X11-Start (`openvt`, `startx`), aber der **Boot-Progress** zeigte weiter die Phase `x11_starting` und die Meldung „Grafische Oberfläche wird gestartet …“. Boot-Progress und Whiptail nutzen dieselbe Konsole **tty1** — das führte zur visuellen Zerstörung der TUI.

**Evidence:** PI-RS-MSI-RETEST-002, Session `20260712_111206_boot`.

---

## Was ändert PI-RS-MSI-GUI-003?

| Vorher (1.10.0.15) | Nachher (1.10.0.16) |
|--------------------|---------------------|
| Timeline: `x11_starting` unter MSI-Compat | Timeline: **`tui_mode_selected`** |
| GUI-Meldung auf tty1 möglich | **`gui_progress_allowed=false`** — kein GUI-Text auf tty1 |
| Kein tty1-Besitzmodell | **Console Ownership** — nach TUI-Start kein Boot-Progress-Write |
| Stale `gui-start.log` von alter Session | **Session-ID** + Stale-Guard beim Evidence-Mirror |
| `version.json` im SquashFS veraltet | Alle Versionsträger synchron **1.10.0.16** |

---

## Ist die GUI auf dem MSI jetzt wieder verfügbar?

**Nein.** Unter MSI-Kompatibilitätsprofil (`setuphelfer_msi_compat=1`, `nomodeset`) bleibt die GUI **bewusst gesperrt**. Der Textmodus ist die Primär-UI.

---

## Ist das Problem am MSI jetzt gelöst?

**Ja — physisch bestätigt.** Session `20260713_003100_boot` mit Payload **1.10.0.20** via **PI-RS-MSI-AUTO-EVIDENCE-001**: TUI stabil ≥120 s, kein `x11_starting`, Spät-Evidence maschinell, `lab-auto-result.json` **passed**.

Details: [PI_RS_MSI_AUTO_EVIDENCE_001_FAQ.de.md](PI_RS_MSI_AUTO_EVIDENCE_001_FAQ.de.md)

---

## Was sehe ich in `boot-timeline.jsonl` nach dem Fix?

Unter MSI-Compat **nicht** `x11_starting`, sondern z. B.:

- `msi_compat_detected`
- `gui_availability_checked`
- **`tui_mode_selected`**
- optional `gui_skipped` (nur Audit, nicht auf tty1)

---

## Warum meldet `/api/version` auf dem alten Stick noch 1.10.0.12?

Der USB-Stick trägt noch Payload **1.10.0.15**; intern war `config/version.json` beim Repack nicht synchronisiert. Ab **1.10.0.16** schreibt der Repack alle Versionsträger konsistent.

Nach **PI-RS-USB-UPDATER-001** müssen ESP-Metadaten und SquashFS-intern übereinstimmen.

---

## Wie erkenne ich stale GUI-Logs?

Prüfen Sie `session_id` und `boot_id` in:

- `SETUP_LOGS/setuphelfer/logs/boot/gui-start.log`
- `SETUP_LOGS/setuphelfer/evidence/boot/gui-availability.json`

Stimmt die Session-ID **nicht** mit der aktuellen Boot-Session überein → **stale**, nicht als aktueller GUI-Nachweis werten.

---

## Welche Kernelparameter für den MSI-Retest?

```text
setuphelfer_msi_compat=1
nomodeset
nouveau.modeset=0
pci=noaer
setuphelfer_mode=text
setuphelfer_kiosk=0
```

---

## Nächste Operator-Schritte

1. **PI-RS-USB-UPDATER-001** — Stick auf **1.10.0.16** (atomar, keine manuelle Versionskorrektur)
2. GE63 booten, TUI **≥2 Minuten** stabil beobachten
3. SETUP_LOGS importieren → **PI-RS-MSI-RETEST-003**

---

## Siehe auch

- [RESCUE_MSI_EVIDENCE_FAQ_DE.md](RESCUE_MSI_EVIDENCE_FAQ_DE.md)
- [PI_RS_MSI_GUI_002_DISABLE_GUI_UNDER_MSI_COMPAT.md](../rescue-stick/PI_RS_MSI_GUI_002_DISABLE_GUI_UNDER_MSI_COMPAT.md)
- [PI_RS_MSI_RETEST_002_RESULT.md](../evidence/pi_rs_msi_retest_002/PI_RS_MSI_RETEST_002_RESULT.md)
