# Sensitive Identifier History Audit — PI-RS-ASUS-CAPTURE-FINALIZE-004

## Ergebnis

| Check | Wert |
|-------|------|
| Worktree (nach Redaction) | kein Roh-Identifier |
| Lokale Feature-Historie (vor Rewrite) | Roh-Identifier erreichbar |
| Remote Feature-Historie | Roh-Identifier erreichbar |
| origin/main | sauber |
| Tags | keine betroffen |
| Remediation | Fall B — neue saubere Branch-Historie |

## Betroffene Artefakte (ohne Rohwerte)

- `90-journal-boot.txt` unter ASUS-Evidence-Pfaden (Kernel `SerialNumber:`-Zeilen)
- kurzzeitig `protected_raw/nvme_inventory_raw.json` in Commit `b421022a` (später im Tip gelöscht, Historie blieb)

## Quarantäne

Remote-Branches mit erreichbaren Roh-Identifiern:

- `origin/pi-rs-asus-physical-diag-003` — **sensitive_history_quarantined**
- `origin/pi-rs-asus-diag-bind-002` — **sensitive_history_quarantined**
- `origin/pi-rs-asus-win11-linux-001` — **sensitive_history_quarantined**

Löschung der Remote-Branches nur nach ausdrücklicher Operatorentscheidung. Kein unkontrollierter Force-Push.

## Push-Gate

Push auf `origin/pi-rs-asus-capture-finalize-004` erst nach:

1. Historien-Rewrite / sauberem Neuaufbau ohne Rohwerte
2. `scripts/check-sensitive-hardware-identifiers.sh` Exit 0
3. erneuter Reachability-Scan gegen Stick-Secrets (lokal, nicht committen)

Vollständige Seriennummern: **nicht im Bericht**.
