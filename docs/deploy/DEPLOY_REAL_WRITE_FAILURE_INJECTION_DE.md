# Real-Write-Prototyp: Failure-Injection (nur Testmode)

## Voraussetzung

Alle unten genannten Hooks wirken **nur**, wenn **beide** gesetzt sind:

- `SETUPHELFER_ENABLE_REAL_WRITE=1`
- `SETUPHELFER_REAL_WRITE_TESTMODE=1`

Ohne Testmode werden `FAIL_*`-Variablen ignoriert (Normalbetrieb bleibt unveraendert).

## Umgebungs-Hooks

| Variable | Wirkung |
|----------|---------|
| `FAIL_BEFORE_OPEN=1` | Abbruch unmittelbar vor `open` des Ziel-Devices (`DEPLOY_REAL_WRITE_ABORTED`, Fehlerhinweis `FAIL_BEFORE_OPEN`). |
| `FAIL_AFTER_OPEN=1` | Abbruch direkt nach erfolgreichem Oeffnen des Ziels; Handles werden im `finally` geschlossen. |
| `FAIL_AFTER_CHUNKS=N` | Stoppt nach **N** geschriebenen Chunks (Teilwrite); anschliessendes Verify schlaegt fehl (`DEPLOY_REAL_WRITE_VERIFY_FAILED`). |
| `FAIL_VERIFY_MISMATCH=1` | Verify liest das Geraet von `SETUPHELFER_FAIL_VERIFY_DEVICE_PATH` statt vom Zielpfad (erzwungener Mismatch). |
| `FAIL_DURING_FSYNC=1` | `os.fsync` wirft einen injizierten `OSError` (Abbruch). |
| `FAIL_DEVICE_CHANGED=1` | Erzwingt `DEPLOY_REAL_WRITE_FINGERPRINT_CHANGED` beim Drift-Gate (Simulates Drift). |

## Device-Drift

Vor kritischen Schritten wird ein **Baseline-Snapshot** mit aktuellen Messwerten verglichen:

- Zielpfad, `realpath`, Transport, removable, mounted, readonly (aus Snapshot), Groesse, Fingerprint (Snapshot)

Abweichungen fuehren zu:

- `DEPLOY_REAL_WRITE_DEVICE_CHANGED`
- `DEPLOY_REAL_WRITE_TARGET_REMOUNTED`
- `DEPLOY_REAL_WRITE_READONLY_CHANGED`
- `DEPLOY_REAL_WRITE_FINGERPRINT_CHANGED`
- `DEPLOY_REAL_WRITE_SIZE_CHANGED`

## Verify

- Es werden genau **nbytes** (Imagegroesse) verglichen, chunkweise, ohne Retry.
- Antwortfelder `verify` / `verify_result`: u. a. `bytes_verified`, `expected_sha256`, `actual_sha256`, optional `mismatch_offset`.
- Teilwrites und kurze Geraete-Reads werden als **failed** oder **mismatch** erkannt.

## Abort & Ressourcen

- `src`/`dst` werden in einem `finally` geschlossen.
- Der globale Mutex wird im aeusseren `finally` immer freigegeben.
- Keine automatischen Retries, keine Reparatur.

## Grenzen

- Keine E2E-Garantie ohne Wegwerf-USB/SD; siehe Evidence-Dokument.
- Injection ist nur fuer kontrollierte Tests gedacht, nicht fuer Produktion.
