# DEPLOY_HARDWARE_GATE_TARGET_SCOPING_FIX

- timestamp_utc: 2026-05-06T20:16:57.067137+00:00
- runtime_port: 8014
- target_device: /dev/sdb
- mode: STRICT_READ_ONLY

## Root Cause
- Ursache: `hardware_gate.validate_test_device` nutzte globale `inspect_result.classification.system_type` direkt als Hard-Block fuer jedes target.
- Folge: Selbst saubere removable Targets wurden durch Host-Zustand (`DUALBOOT/UNKNOWN`) blockiert.
- Zusatzproblem: Fehlende `transport/removable` Felder wurden als `False` interpretiert und erzeugten `NON_REMOVABLE`-Blocks.

## Regel-Fix (target-scoped)
- Hard-Blocks jetzt nur noch aus target-bezogenen Merkmalen (Disk/Partitionen/Safety-Target).
- Globale Host-Klassifikation erzeugt nur Warning/Review, keinen Hard-Block.
- Bei nicht verifizierbaren Ziel-Metadaten (`transport/removable/size`) jetzt Review statt implizitem Block.

## Runtime-Ergebnis
- inspect_http: 200
- safety_http: 200 (GET_FALLBACK)
- safety_target: {"device": "/dev/sdb", "size": "59G", "classification": "allowed", "write_allowed": true, "reason_code": "SAFETY_EMPTY_DISK"}
- gate_http_1: 200, gate_http_2: 200
- gate_code_1: DEPLOY_HARDWARE_GATE_REVIEW_REQUIRED, gate_code_2: DEPLOY_HARDWARE_GATE_REVIEW_REQUIRED
- report_status: review_required
- readiness_level: review_required
- eligible: True
- device_class: unknown_test_media
- blocked_reasons: []
- warnings: ["DEPLOY_HARDWARE_GATE_REVIEW_REMOVABLE_UNVERIFIED", "DEPLOY_HARDWARE_GATE_REVIEW_TRANSPORT_UNVERIFIED", "DEPLOY_HARDWARE_GATE_REVIEW_SIZE_UNVERIFIED", "DEPLOY_HARDWARE_GATE_HOST_DUALBOOT_CONTEXT"]

## Fingerprint-Stabilitaet
- stable: True
- fingerprint_1: e963cf604879d8b606080a08b787b0fb8bae25c71f50d33decee7ebb897a6168
- fingerprint_2: e963cf604879d8b606080a08b787b0fb8bae25c71f50d33decee7ebb897a6168

## Operator Protocol
- protocol_http: 200
- protocol_code: DEPLOY_HARDWARE_GATE_OPERATOR_PROTOCOL_OK
- protocol_steps_count: 10
- abort_conditions_count: 7

## Negativtests
- mounted: http=200, code=DEPLOY_HARDWARE_GATE_BLOCKED, status=blocked, blocked=["DEPLOY_REAL_WRITE_BLOCKED_MOUNTED"]
- non_removable: http=200, code=DEPLOY_HARDWARE_GATE_BLOCKED, status=blocked, blocked=["DEPLOY_REAL_WRITE_BLOCKED_NON_REMOVABLE"]
- transport_unknown: http=200, code=DEPLOY_HARDWARE_GATE_BLOCKED, status=blocked, blocked=["DEPLOY_REAL_WRITE_BLOCKED_UNKNOWN"]
- windows_hint: http=200, code=DEPLOY_HARDWARE_GATE_BLOCKED, status=blocked, blocked=["DEPLOY_REAL_WRITE_BLOCKED_WINDOWS"]
- dualboot_hint: http=200, code=DEPLOY_HARDWARE_GATE_BLOCKED, status=blocked, blocked=["DEPLOY_REAL_WRITE_BLOCKED_DUALBOOT"]

## No-Write Evidence
- findmnt_unchanged: True
- mount_unchanged: True
- lsblk_unchanged: True
- no_write_operations: true

## Teststatus
- py_compile deploy/hardware_gate.py deploy/routes.py: OK
- tests.test_deploy_hardware_gate_v1: OK
- tests.test_deploy_hardware_gate_target_scoping_v1: OK
- tests.test_deploy_real_write_guard_v1: OK
- tests.test_write_guard_v1: OK

## Abnahme
- result: BESTANDEN
- criterion: target `/dev/sdb` ist nicht mehr `blocked`, sondern `review_required` bei sauberem Medium unter globalem Host-DUALBOOT-Kontext
