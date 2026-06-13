# Rescue Stick Persistence (R.3)

## Ziel

Kanonisches Evidence-Verzeichnis auf dem Setuphelfer-Rettungsstick, ohne Schreibzugriffe auf interne Systemdatenträger.

## Pfad

```
<stick-mount>/setuphelfer-evidence/
  boot/
  menu/
  hardware/
  network/
  telemetry/
  rescue-ui/
  tests/
  matrix/
  summaries/
  raw/
```

RAM-Fallback (mit Warnung):

```
/tmp/setuphelfer-evidence/
```

## Modul

`backend/core/rescue_persistence.py` — Version `RESCUE_PERSISTENCE_VERSION = 3`.

### Öffentliche API

| Funktion | Zweck |
|----------|-------|
| `detect_rescue_stick_mount()` | Erkennt Live-Medium und `/media/*/SETUPHELFER*` |
| `build_rescue_evidence_root()` | Baut Evidence-Root-Pfad |
| `ensure_rescue_evidence_tree()` | Legt Unterverzeichnisse an |
| `write_rescue_json_evidence()` | JSON in Subdir schreiben |
| `write_rescue_text_evidence()` | Text in Subdir schreiben |
| `write_rescue_summary()` | Kurz-Zusammenfassung |
| `build_rescue_persistence_diagnostics()` | Diagnose-Dokument |

## Erkennungsregeln

1. **Live-Medium:** `/run/live/medium` (Debian live-boot)
2. **Label-Mounts:** `SETUPHELFER`, `SETUPHELFER_RESCUE`, `SETUPHELFER_RESCUE_LIVE`
3. **Media-Pfad:** `/media/<user>/SETUPHELFER*`
4. **Dateisysteme:** `vfat`, `exfat`, `ext2/3/4` → schreibbar plausibel
5. **Read-only:** `iso9660`, `udf`, `squashfs`, `erofs` → RAM-Fallback + Warnung

## Sicherheit

- Interne Systemdisks (`is_system_disk`) werden als Schreibziel **abgelehnt**
- Nutzt `storage_discovery.discover_findmnt_mounts_flat` und `safe_device.list_classified_devices`
- Keine parallele Storage-Discovery-Duplikate

## Live-Integration

- CLI: `scripts/rescue-live/image/setuphelfer-rescue-evidence.py`
- Shell: `setuphelfer-rescue-common.sh` — `setuphelfer_rescue_record_menu_evidence`, `setuphelfer_rescue_run_evidence_bundle`
