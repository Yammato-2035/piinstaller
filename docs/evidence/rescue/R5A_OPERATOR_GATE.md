# R.5A — Operator Gate ISO Build

## Prüfung

```bash
echo "${OPERATOR_ISO_BUILD_FREIGABE:-0}"
```

Im Operator-Terminal: **1** (gesetzt).  
In Agent-Shell: initial **0**, für Versuch exportiert auf **1**.

## Build-Skript-Gate (zusätzlich)

`run-controlled-iso-build-with-logging.sh` erfordert:

```bash
--operator-confirm-build
```

Preview ohne Flag → Exit **20** (wie im Operator-Terminal-Log).

## Policy Guard (Agent-Versuch)

| Kontext | Wert |
|---------|------|
| `POLICY_IS_TTY` | **false** |
| `POLICY_ALREADY_ROOT` | false |
| `POLICY_SUDO_NONINTERACTIVE` | false |
| Ergebnis | **LB_EXIT=30** `blocked_requires_operator_sudo_policy` |

## Validator vor Build

```bash
./scripts/rescue-live/validate-controlled-live-build-tree.sh build/rescue/live-build/setuphelfer-rescue-live
# Exit 11: FORBIDDEN chroot/usr/lib/firmware/RTL8192E/main.img
```

→ Vor Build empfohlen: `clean-controlled-live-build-tree.sh --operator-confirm-clean` (Operator-Terminal + sudo).

## Freigabe erfüllt?

**Ja** (Intent) — Ausführung muss im **Operator-Terminal mit sudo** erfolgen.
