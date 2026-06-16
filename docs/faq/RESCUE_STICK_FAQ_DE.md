# Rescue Stick FAQ (DE)

Stand: **2026-06-07** · Workspace-Version **1.7.7.0**

Ausführlicher Überblick: [RESCUE_START_ASSISTANT_OVERVIEW.md](../knowledge-base/rescue/RESCUE_START_ASSISTANT_OVERVIEW.md)

---

## Was ist der Setuphelfer Rettungsstick heute?

Ein **Debian-Live-System** mit geführtem **Start Assistant** (TUI), automatischer Netzwerk-/Telemetrie-Vorbereitung und **read-only** Festplattenanalyse. Schreibende Aktionen (Backup, Restore, Reparatur, Neuinstallation) werden nur als **Plan** angeboten — nicht automatisch ausgeführt.

---

## Warum wurde kein ISO gebaut?

Jeder ISO-Build bleibt ein **separater Operator-Schritt** mit eigenem Gate (`--operator-confirm-build`). Workspace-Änderungen (z. B. 1.7.7.0) sind erst nach Rebuild + Validierung auf dem Stick wirksam.

---

## Was ist der Start Assistant?

Das Programm `setuphelfer-rescue-start-assistant` führt durch:

1. Willkommen / Branding  
2. Live-Medium prüfen  
3. Netzwerk (WLAN-Menü mit Passwortabfrage)  
4. Telemetrie senden (oder spoolen)  
5. Festplatten erkennen (read-only)  
6. Empfehlung + Hauptmenü (Backup / Restore / Reparatur / Install / Diagnose / Expertenmodus)

Zustand wird in `/run/setuphelfer-rescue/wizard-state.json` gespeichert (später auch für GUI nutzbar).

---

## Warum crashte WLAN-OK/Return früher?

Zwei Ursachen wurden behoben:

1. **Falscher whiptail-Tag:** Auswahl per Index statt SSID-String  
2. **`set -e`:** Abbruch bei whiptail-Escape — Onboarding nutzt jetzt robustere Exit-Codes (Offline = 20, kein Crash)

Passwort wird über **`whiptail --passwordbox`** abgefragt — **nicht** geloggt.

---

## Wie verbindet sich der Stick mit dem Developer-Laptop?

Standard-Telemetrie-Ziel: **`http://192.168.178.140:8001`** (LAN-Proxy zum Backend).

Vor dem MSI-Test auf dem Developer-Rechner:

```bash
SETUPHELFER_RESCUE_TELEMETRY_BIND=192.168.178.140 \
  ./scripts/rescue-live/start-rescue-telemetry-lan-proxy.sh
```

UFW muss den MSI (`192.168.178.96` o. ä.) auf Port **8001** erlauben.

---

## Was passiert ohne WLAN?

Der Assistent bietet **Offline fortfahren** an. Telemetrie wird nach `/run/setuphelfer-rescue/telemetry-spool/` geschrieben und per **Retry-Timer** erneut gesendet, sobald Health erreichbar ist.

---

## Was war der Telemetrie-SyntaxError?

`setuphelfer-rescue-telemetry-push` baute JSON früher per **Inline-Python-Heredoc** — bei echtem `lsblk -J` entstand `SyntaxError: unterminated string literal`.

**Fix ab 1.7.6.0:** separates Modul `setuphelfer-rescue-telemetry-build-payload.py`.

---

## Warum fehlten Boot-Menüeinträge in der ISO?

Der Binary-Hook schrieb **falsche ISOLINUX-Syntax** (`LABEL`/`LINUX` statt `label`/`kernel`). Ab **1.7.7.0** werden Einträge zusätzlich in **`live.cfg.in`** beim Prepare eingetragen.

Menü-Titel: **Setuphelfer Rettungsstick**.

---

## Darf der Stick meine Platte reparieren oder neu installieren?

**Nein — automatisch nicht.** Pläne zeigen nur Vorschau und Blocker (`execution_allowed: false`). Bei instabilem USB/SquashFS blockiert der Media-Check Reparatur/Installation.

Bei erkannten Systemfehlern: **zuerst Backup empfehlen**.

---

## Wann ist Windows-Inspect erlaubt?

Erst wenn **physisch belegt:** Boot vom Stick, Netzwerk, echter Telemetrie-ACK. Bis dahin: **blockiert** (`RESCUE-UEFI-005`).

---

## Welche Daten sendet Telemetrie?

Netzwerk-Diagnose, Hardware-Überblick, Media-Check, Onboarding-Status — **keine** WLAN-Passwörter, Tokens oder private Schlüssel.

---

## Warum E2EE zusätzlich zu TLS?

TLS schützt den Kanal, E2EE schützt die Payload Ende-zu-Ende zwischen Agent und Server (Developer-Edition-Kontext).

---

## Warum ist Pairing Pflicht?

Der Rettungsstick darf sich nicht blind anmelden; Operator-Bestätigung ist Sicherheitsanforderung.

---

## Warum ist nftables Pflicht?

Default-deny reduziert Angriffsfläche im Rettungsszenario.

---

## Wo finde ich Build- und ISO-Details?

[rescue_iso_build_faq.md](rescue_iso_build_faq.md)

---

## Wo finde ich Evidence und Gates?

`docs/evidence/runtime-results/rescue/` — aktuell u. a. `rescue_iso_usb_gate_status_latest.json`, `RESCUE_START_ASSISTANT_PRODUCTIZATION_RESULT.md`.
