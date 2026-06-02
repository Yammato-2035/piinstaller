# Rescue ISO — dangerous_path_override Fix Ergebnis

**Datum:** 2026-06-02  
**Entscheidung:** `narrow_allowlist_for_systemd_environment_pythonpath` (Fall A)

## Änderungen

| Datei | Änderung |
|-------|----------|
| `scripts/rescue-live/validate-live-build-dpkg-preflight.sh` | Regex `(^|[^A-Z_])PATH=` statt bare `PATH=`; Allowlist nur für `setuphelfer-dev-agent.service:Environment=PYTHONPATH=/opt/setuphelfer-rescue` |
| `backend/tests/test_rescue_iso_dangerous_path_validator_v1.py` | 5 Unit-Tests (allowed PYTHONPATH, blocked PATH=/opt/evil, export PATH, Syntax) |

## Kein Build

- Kein ISO-Build, kein `lb build`, kein QEMU, kein USB, kein apt, kein Backup/Restore/Deploy.

## Ergebnis

| Prüfung | Exit |
|---------|------|
| Prepare nach Fix | **0** |
| Validate nach Fix | **0** |
| dangerous_path_override behoben | **yes** |
| stale squashfs weiterhin blockiert | **yes** (FORBIDDEN scan unverändert in validate-controlled-live-build-tree.sh) |
| Globale `/opt`-Allowlist | **no** |

Logs:
- `rescue_iso_prepare_after_dangerous_path_fix_latest.log`
- `rescue_iso_validate_after_dangerous_path_fix_latest.log`

## Tests

```
python3 -m unittest backend.tests.test_rescue_iso_dangerous_path_validator_v1 -v
→ 5 tests OK
```

## Hinweis

Validate Exit 0 ist **Voraussetzung** für den Operator-Build, kein Boot-/ISO-Nachweis. Rescue bleibt **nicht grün** ohne neues ISO + Bootnachweis.
