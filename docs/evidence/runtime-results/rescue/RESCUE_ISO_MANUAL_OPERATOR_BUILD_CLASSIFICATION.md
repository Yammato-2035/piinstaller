# Rescue ISO Manual Operator Build — Classification

**Datum:** 2026-05-27 · **HEAD:** `11e27b6`

## Ergebnis: **A) operator_policy_blocked**

| Feld | Wert |
|------|------|
| Wrapper Exit | **30** |
| `error_code` | `blocked_requires_operator_sudo_policy` |
| Build gestartet | **nein** |
| ISO vorhanden | **nein** |
| SHA256 / Manifest | **nein** |

## Ursache

Agent-/Cursor-Shell ohne TTY (`POLICY_IS_TTY=false`), `sudo -n` nicht verfügbar. Der Wrapper verweigert `lb build` bewusst — kein Askpass, kein `sudo -S`, kein NOPASSWD-Zwang.

## Operator-Nächstschritt (echtes Terminal)

```bash
cd /home/volker/piinstaller
sudo -v   # interaktiv im Operator-Terminal
scripts/rescue-live/run-controlled-iso-build-with-logging.sh --operator-confirm-build
echo "wrapper_exit=$?"
```

Logs: `build/rescue/logs/controlled-iso-build/latest.log`  
Summary: `docs/evidence/runtime-results/rescue/controlled_iso_build_latest_summary.json`

## Rescue-Ampel

Bleibt **blocked** / nicht full-green — kein Boot-/VM-Nachweis, kein ISO aus diesem Lauf.

JSON: `rescue_iso_manual_operator_build_classification_latest.json`
