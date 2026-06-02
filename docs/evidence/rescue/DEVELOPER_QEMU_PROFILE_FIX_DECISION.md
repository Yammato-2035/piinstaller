# Developer QEMU Profile Fix — Decision (Phase 4)

**Datum:** 2026-06-02

## Gewählte Variante

**Variante A — Developer-QEMU-Profil**

Separates Profil `developer-qemu` mit Serial-Konsole + Autopilot-Enable nur für QEMU-Lab-Smoke. Standard-ISO unverändert defensiv.

## Begründung

1. Operator-QEMU-Smoke lief gegen **Standard-ISO** (`quiet splash`, kein ttyS0) — Profil-Mismatch ist dokumentierte Mitursache.
2. Profil `developer-qemu` existiert bereits; Prepare-Logik materialisiert Serial + Hook 090.
3. Autopilot-Smoke erhält Preflight-Guard (`assert_developer_qemu_iso_ready`) — blockiert erneuten Mismatch.
4. Kein globales Dev-Agent-Enable im Release.

## Sicherheitsbewertung

| Aspekt | Bewertung |
|--------|-----------|
| Release-ISO | Unverändert (`quiet splash`, keine Autopilot-Enable) |
| Dev-Callback | Nur developer-qemu; Endpoint `http://10.0.2.2:8001` (QEMU-NAT, lab-only) |
| E2EE | `contract_stub_only` (unverändert) |
| nftables | `preview_only_apply_false` (unverändert) |
| USB/Restore/Host-Disk | Keine Pfade geändert |

## Nicht-Ziele (dieser Lauf)

Kein ISO-Build, kein QEMU, kein USB, kein Deploy, kein Profilwechsel Runtime, keine Safety-Gate-Schwächung.

## Erwarteter nächster Build-Typ

```bash
SETUPHELFER_RESCUE_BUILD_PROFILE=developer-qemu \
  ./scripts/rescue-live/prepare-controlled-live-build-tree.sh
# Operator-Terminal:
sudo ./auto/clean   # entfernt stale binary/ vom Standard-Build
scripts/rescue-live/run-controlled-iso-build-with-logging.sh --operator-confirm-build
```
