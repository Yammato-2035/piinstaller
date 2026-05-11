# DEPLOY_HARDWARE_GATE_METADATA_COMPLETENESS_FIX

- timestamp_utc: 2026-05-06T20:26:28.302875+00:00
- runtime_port: 8015
- target_device: /dev/sdb
- mode: STRICT_READ_ONLY

## Root Cause
- Inspect-Metadaten enthielten fuer Zielmapping teils keine vollstaendigen Felder (transport/removable/rotational/model), wodurch Hardware-Gate auf review_required fiel.
- Disk/Partition-Mapping war nicht robust genug fuer Parent-Child-Faelle (/dev/sdb1 -> /dev/sdb).

## Metadaten- und Mapping-Fix
- `modules/storage_detection.detect_block_devices` liefert jetzt zusaetzlich: rm, ro, tran, rota, model, vendor.
- Hardware-Gate mappt target partition defensiv auf Parent-Disk und nutzt Parent-Metadaten fuer Child-Targets.
- Fehlende optionale Metadaten erzeugen Warnungen, aber kein automatisches readiness-Downgrade bei sonst sauberem Target.

## Runtime-Ergebnis
- inspect_http: 200
- safety_http: 200 (GET_FALLBACK)
- safety_target: {"device": "/dev/sdb", "size": "59G", "classification": "allowed", "write_allowed": true, "reason_code": "SAFETY_EMPTY_DISK"}
- gate_http_1: 200, gate_http_2: 200
- gate_code_1: DEPLOY_HARDWARE_GATE_OK, gate_code_2: DEPLOY_HARDWARE_GATE_OK
- report_status: ok
- readiness_level: test_ready
- device_class: usb_hdd
- blocked_reasons: []
- partition_summary: {"count": 1, "target_device_resolved": "/dev/sdb"}
- filesystem_summary: {"types": ["exfat"], "count": 1}
- mount_state: {"mounted": false}

## Snapshot/Fingerprint
- stable: True
- fingerprint_1: 433b7b020da60277da93cc185061151e74df75b740d862c138d9d9fa0b257a32
- fingerprint_2: 433b7b020da60277da93cc185061151e74df75b740d862c138d9d9fa0b257a32

## Negativtests
- mounted: http=200, code=DEPLOY_HARDWARE_GATE_BLOCKED, blocked=["DEPLOY_REAL_WRITE_BLOCKED_MOUNTED"]
- readonly: http=200, code=DEPLOY_HARDWARE_GATE_BLOCKED, blocked=["DEPLOY_REAL_WRITE_BLOCKED_READONLY"]
- windows: http=200, code=DEPLOY_HARDWARE_GATE_BLOCKED, blocked=["DEPLOY_REAL_WRITE_BLOCKED_WINDOWS"]
- dualboot: http=200, code=DEPLOY_HARDWARE_GATE_BLOCKED, blocked=["DEPLOY_REAL_WRITE_BLOCKED_DUALBOOT"]
- raid: http=200, code=DEPLOY_HARDWARE_GATE_BLOCKED, blocked=["DEPLOY_REAL_WRITE_BLOCKED_RAID"]
- lvm: http=200, code=DEPLOY_HARDWARE_GATE_BLOCKED, blocked=["DEPLOY_REAL_WRITE_BLOCKED_LVM"]
- loop: http=200, code=DEPLOY_HARDWARE_GATE_BLOCKED, blocked=["DEPLOY_REAL_WRITE_BLOCKED_LOOP"]

## No-Write Evidence
- findmnt_unchanged: True
- mount_unchanged: True
- lsblk_unchanged: True
- no_write_operations: true

## Teststatus
- py_compile deploy/hardware_gate.py modules/storage_detection.py deploy/routes.py: OK
- tests.test_deploy_hardware_gate_metadata_v1: OK
- tests.test_deploy_hardware_gate_target_scoping_v1: OK
- tests.test_deploy_hardware_gate_v1: OK
- tests.test_deploy_real_write_guard_v1: OK
- tests.test_write_guard_v1: OK

## Abnahme
- result: BESTANDEN
- criterion: reales `/dev/sdb` liefert `readiness_level=test_ready`, `device_class` gesetzt, `blocked_reasons` leer und Fingerprint stabil
