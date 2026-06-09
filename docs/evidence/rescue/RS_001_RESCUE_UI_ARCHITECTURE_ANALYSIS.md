# RS-001 Rescue UI Architecture Analysis

**Datum:** 2026-06-09 · **HEAD:** `0bbe01b` · **RS-001:** yellow

## Hardware-Befund (Phase 3 Retest)

| Check | Result |
|-------|--------|
| UEFI | reached |
| GRUB | reached |
| Old dialog visible | yes (whiptail start-assistant) |
| Modern rescue shell visible | **no** |
| Only OK dialog | yes |
| Live-Medium warning | yes (historisch; SquashFS fix on stick) |
| Network/WLAN wizard before failure | partial |
| „Keine WLAN-Netze gefunden“ | yes |
| systemd-networkd-wait-online failed | yes |
| setuphelfer-rescue-telemetry-push failed | yes |
| User-facing flow quality | **failed** |
| RS-001 | yellow |

## Entscheidungstabelle

| Area | Existing | Reuse? | Rescue risk | Decision |
|------|----------|--------|-------------|----------|
| React/Vite | `frontend/` | yes | low | Rescue entry `rescue.html` |
| Dashboard components | `DevelopmentDashboard` etc. | partial | high coupling | **not** in boot menu |
| i18n DE/EN | `react-i18next` + rescue local JSON | yes | low | rescue `i18n/` |
| Tauri wrapper | `src-tauri/` | later | GTK/WebKit deps | **not** hard dependency |
| Start assistant | whiptail bash | replace | **UX blocker** | fallback only |
| Network onboarding | bash + NM | optional | blocks boot today | user-initiated only |
| Telemetry push | systemd unit | optional | blocks boot today | disabled/skipped default |
| Logging/evidence | partial JSON in `/run` | extend | medium | FAT32 ESP spool |
| Fallback TUI | start-assistant text mode | yes | low | keep |

## Nächster Schritt

Foundation implementiert — SquashFS rebuild + payload update + HW retest mit React Shell.
