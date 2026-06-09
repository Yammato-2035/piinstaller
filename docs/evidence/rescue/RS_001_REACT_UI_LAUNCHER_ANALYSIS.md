# RS-001 React UI Launcher — Analyse

**Datum:** 2026-06-09  
**HEAD:** `17ac7f7` (vor Fix)  
**Version:** `1.7.10.0` → Fix `1.7.10.1`

## Hardware-Befund

| Beobachtung | Ergebnis |
|-------------|----------|
| React Launcher erreicht | **ja** |
| URL sichtbar | `http://127.0.0.1:8765/rescue.html` |
| Grafisches Menü | **nein** |
| whiptail-Blocker | **nein** |
| network-onboarding failed | **ja** |
| networkd-wait-online failed | **ja** |
| telemetry-push failed | **ja** |

Bildnachweis: `IMG_31CF232F-F82B-4EF4-AAF7-4176D1539492.jpeg` (Operator)

## Analyse-Tabelle

| Component | Current behavior | Hardware result | Problem | Fix decision |
|-----------|------------------|-----------------|---------|--------------|
| `setuphelfer-rescue-ui-launch` | HTTP-Server + URL auf tty1 | URL sichtbar, kein Menü | Kein grafischer Browser im SquashFS; kein `review_required` Status | Browser-Erkennung, Fallback-TUI, Status-JSON |
| SquashFS Browser | nicht vorgesehen | Kiosk fehlt | Kein chromium/firefox | Kein apt; Fallback-TUI + optional Textbrowser |
| `setuphelfer-rescue-network-onboarding` | Boot `--boot-trigger` enabled | failed | Startet vor Menü, WLAN-Fehler | Boot-Skip; nur Nutzerwahl |
| `systemd-networkd-wait-online` | aktiv im Live-Image | failed | Blockiert Bootpfad | Drop-in → `/bin/true` |
| `setuphelfer-rescue-telemetry-push` | Boot enabled | failed | Hard-Fail ohne Netz | Opt-in only, default skipped exit 0 |
| Hook `010-enable` | enable network+telemetry | failed units sichtbar | Boot-Autostart | Entfernt aus hook/wants |

## Pflichtfragen (Antworten)

1. Nur HTTP-Server ohne Browser? **Ja** (vor Fix)
2. Browser im SquashFS? **Nein**
3. Browser-Prüfung? **Ja** (vor Fix, ohne Fallback-Qualität)
4. Fallback bei fehlendem Browser? **Nein** (nur URL + wait)
5. X11/Wayland? **Nein**
6. tty1? **Ja**
7. DISPLAY gesetzt? **Nein**
8. Lokale URL anzeigbar? **Ja, nur Text**
9. Launcher „erfolgreich“ bei URL-only? **Fälschlich implizit** → Fix: `review_required`
10. Evidence geschrieben? **Nein** → Fix: `rescue-ui-status.json` + Stick-Spiegel

## Fix (1.7.10.1)

- Launcher: Kiosk-Versuch → Textbrowser → Fallback-TUI → URL-only mit `review_required`
- Network onboarding: `SKIPPED_BOOT_WAIT_USER` bei `--boot-trigger`
- Telemetry: `telemetry_disabled_or_no_consent`, exit 0
- Units: nicht mehr `WantedBy=multi-user.target` für network/telemetry
- `systemd-networkd-wait-online` neutralisiert via Drop-in

## Next

Rebuild/Repack SquashFS + Payload-Update + Hardware-Retest (nutzbares Menü, nicht nur URL).
