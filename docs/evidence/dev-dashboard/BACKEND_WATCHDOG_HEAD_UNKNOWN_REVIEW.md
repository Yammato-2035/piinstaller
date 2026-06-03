# Backend Watchdog — head unknown Review

**Datum:** 2026-06-03

## Ursache

`/opt/setuphelfer` ist **kein Git-Repository** (`git rev-parse` → fatal).  
Healthcheck nutzt `git -C "$REPO_ROOT" rev-parse --short HEAD` → **`unknown`**.

## Verfügbare Metadaten

- `VERSION` / `config/version.json`: **1.7.3.0**

## Pflichtbewertung

| Feld | Wert |
|------|------|
| head unknown Ursache | Kein `.git` unter `/opt` |
| Blockiert QEMU | **no** |
| Optionaler Follow-up | HEAD aus `config/version.json` + Deploy-Manifest in Healthcheck |
| **Status** | **yellow_non_blocking** |
