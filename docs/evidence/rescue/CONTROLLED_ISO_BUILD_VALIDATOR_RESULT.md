# Controlled ISO Build — Validator Result

**Datum:** 2026-06-02

## Skripte

| Skript | Vorhanden | Exit |
|--------|-----------|------|
| `validate-rescue-iso-artifact.sh` | **no** | 127 (missing) |
| `validate-rescue-iso-squashfs.sh` | **yes** | **0** |

## Squashfs-Validator (Exit 0)

```
OK: rescue ISO squashfs — bundle, systemd init, enabled units, de keyboard/locale, login hints
```

Prüft: Bundle, venv, frontend, systemd init bootappend, enabled backend/UI units, DE locale, login hints user/live.

## Bewertung

| Feld | Wert |
|------|------|
| artifact_validator_status | **missing_script_not_blocking** |
| squashfs_validator_status | **ok** |
| Gesamt | **ok** |

Dedicated Artifact-Validator fehlt; Squashfs-Validator deckt Integrationspflicht ab.

Log: `controlled_iso_build_squashfs_validator_latest.log` (gitignored).
