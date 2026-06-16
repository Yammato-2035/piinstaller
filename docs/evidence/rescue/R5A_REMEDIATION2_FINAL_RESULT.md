# R.5A Remediation-2 — Abschlussbericht

**Datum:** 2026-06-13

## Pflichtfelder

| Feld | Wert |
|------|------|
| **x-www-browser entfernt** | **ja** (47 Zeilen, kein grep-Treffer) |
| **chromium vorhanden** | **ja** |
| **Kiosk Browser-Fallback chromium-first** | **ja** (+ optional `x-www-browser` Runtime) |
| **Validator Exit** | **0** |
| **Build gestartet (Agent)** | versucht, **nein** (Policy-Guard) |
| **LB_EXIT (Agent)** | **30** (`blocked_requires_operator_sudo_policy`, kein TTY) |
| **LB_EXIT=123 behoben** | **ja** (package-list); Rebuild muss im Operator-TTY laufen |

## Code-Änderungen

| Datei | Änderung |
|-------|----------|
| `prepare-controlled-live-build-tree.sh` | `x-www-browser` aus Heredoc entfernt |
| `validate-controlled-live-build-tree.sh` | invalid-package + browser/display checks |
| `validate-live-build-dpkg-preflight.sh` | `x-www-browser` forbidden |
| `setuphelfer-rescue-kiosk-start` | Runtime-Fallback `x-www-browser` |
| `setuphelfer-rescue-kiosk-health` | Runtime-Fallback `x-www-browser` |
| `setuphelfer-rescue-ui-launch` | Runtime-Fallback `x-www-browser` |

## Statische Tests

`bash -n` auf prepare, validate, kiosk-start, kiosk-health → **OK**

## Erfolgskriterium (Remediation)

- [x] `setuphelfer.list.chroot` enthält kein `x-www-browser`
- [x] Validator erkennt und blockiert `x-www-browser` künftig
- [x] chromium + Display-Stack in list.chroot

## Nächste Aktion (Operator-TTY)

```bash
cd /home/volker/piinstaller

# Falls noch root-owned lb-Artefakte:
sudo ./scripts/rescue-live/clean-controlled-live-build-tree.sh --operator-confirm-clean

export OPERATOR_ISO_BUILD_FREIGABE=1
export SETUPHELFER_RESCUE_BUILD_PROFILE=standard

./scripts/rescue-live/run-controlled-iso-build-with-logging.sh \
  --operator-confirm-build \
  --profile standard \
  --run-id r5a_rebuild_pkgfix_$(date -u +%Y%m%d_%H%M%S)
```

**Erwartung:** Build passiert LB_EXIT=123 (x-www-browser). Bei LB_EXIT=0 → Post-Build Validation (SHA256, SquashFS, GRUB, USB-Entscheidung).

## Verboten (eingehalten)

Kein USB-Write, MSI-Boot, Backup, Restore, Deploy, Host-apt.
