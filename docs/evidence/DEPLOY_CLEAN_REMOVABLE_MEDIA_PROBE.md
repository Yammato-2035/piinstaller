# DEPLOY_CLEAN_REMOVABLE_MEDIA_PROBE

- timestamp_utc: 2026-05-06T17:51:43.105745+00:00
- mode: STRICT_READ_ONLY
- runtime_port: 8013
- verwendetes_testmedium: /dev/sdb

## lsblk-Auszug
```text
NAME          SIZE RM RO TYPE MOUNTPOINT                      FSTYPE TRAN   PATH
sda           1,8T  0  0 disk                                        usb    /dev/sda
├─sda1      931,5G  0  0 part /media/gabriel/setuphelfer-back ext4          /dev/sda1
└─sda2      931,5G  0  0 part /media/gabriel/windows-backup   ntfs          /dev/sda2
sdb            59G  1  0 disk                                        usb    /dev/sdb
└─sdb1         59G  1  0 part                                 exfat         /dev/sdb1
nvme1n1       1,8T  0  0 disk                                        nvme   /dev/nvme1n1
├─nvme1n1p1   757M  0  0 part                                 ntfs   nvme   /dev/nvme1n1p1
├─nvme1n1p2 512,1M  0  0 part                                 vfat   nvme   /dev/nvme1n1p2
├─nvme1n1p3    16M  0  0 part                                        nvme   /dev/nvme1n1p3
├─nvme1n1p4 928,8G  0  0 part                                 ntfs   nvme   /dev/nvme1n1p4
├─nvme1n1p5   860M  0  0 part                                 ntfs   nvme   /dev/nvme1n1p5
└─nvme1n1p6   931G  0  0 part                                 ntfs   nvme   /dev/nvme1n1p6
nvme0n1       1,8T  0  0 disk                                        nvme   /dev/nvme0n1
├─nvme0n1p1   512M  0  0 part /boot/efi                       vfat   nvme   /dev/nvme0n1p1
└─nvme0n1p2   1,8T  0  0 part /                               ext4   nvme   /dev/nvme0n1p2
```

## Safety-Ergebnis
- methode: GET_FALLBACK
- safety_http: 200
- target_entry: {"device": "/dev/sdb", "size": "59G", "classification": "allowed", "write_allowed": true, "reason_code": "SAFETY_EMPTY_DISK"}

## Hardware-Gate-Ergebnis
- gate_http_1: 200
- gate_http_2: 200
- gate_code_1: DEPLOY_HARDWARE_GATE_BLOCKED
- gate_code_2: DEPLOY_HARDWARE_GATE_BLOCKED
- readiness_level: blocked
- report_status: blocked
- blocked_reasons: ["DEPLOY_REAL_WRITE_BLOCKED_NON_REMOVABLE", "DEPLOY_REAL_WRITE_BLOCKED_UNKNOWN", "DEPLOY_REAL_WRITE_BLOCKED_DUALBOOT"]
- eligible: None
- device_class: None
- required_operator_checks_count: 3

## Snapshot-Fingerprint
- stabil: True
- fingerprint_1: 27ff78fa16070fe707e0f7cbbfdae5df7b7d6d4cf11f81d4a787a45638425949
- fingerprint_2: 27ff78fa16070fe707e0f7cbbfdae5df7b7d6d4cf11f81d4a787a45638425949

## Operator-Protocol
- protocol_http: 200
- protocol_code: DEPLOY_HARDWARE_GATE_OPERATOR_PROTOCOL_OK
- protocol_steps_count: 10
- abort_conditions_count: 7
- confirmations_count: 0

## Negativtests
- mounted: http=200, code=DEPLOY_HARDWARE_GATE_BLOCKED, readiness=blocked, blocked=["DEPLOY_REAL_WRITE_BLOCKED_MOUNTED"]
- non_removable: http=200, code=DEPLOY_HARDWARE_GATE_BLOCKED, readiness=blocked, blocked=["DEPLOY_REAL_WRITE_BLOCKED_NON_REMOVABLE"]
- transport_unknown: http=200, code=DEPLOY_HARDWARE_GATE_BLOCKED, readiness=blocked, blocked=["DEPLOY_REAL_WRITE_BLOCKED_UNKNOWN"]
- windows_hint: http=200, code=DEPLOY_HARDWARE_GATE_BLOCKED, readiness=blocked, blocked=["DEPLOY_REAL_WRITE_BLOCKED_WINDOWS", "DEPLOY_REAL_WRITE_BLOCKED_UNKNOWN"]
- dualboot_hint: http=200, code=DEPLOY_HARDWARE_GATE_BLOCKED, readiness=blocked, blocked=["DEPLOY_REAL_WRITE_BLOCKED_DUALBOOT", "DEPLOY_REAL_WRITE_BLOCKED_UNKNOWN"]

## Nachweis keine Schreiboperation / keine Mountaenderung
- findmnt_vor_nach_identisch: True
- mount_vor_nach_identisch: True
- lsblk_vor_nach_identisch: True
- verbotene_kommandos_ausgefuehrt: false
- neue_eintraege_unter_/mnt/setuphelfer: 0

## Teststatus
- py_compile deploy/hardware_gate.py deploy/routes.py: OK
- tests.test_deploy_hardware_gate_v1: OK (15/15)
- tests.test_deploy_real_write_guard_v1: OK (15/15)
- tests.test_write_guard_v1: OK (6/6)

## Finale Abnahmeentscheidung
- result: NICHT_BESTANDEN
- grund: readiness_level blieb auf blocked (nicht test_ready), trotz geeignetem ungemountetem Medium /dev/sdb
