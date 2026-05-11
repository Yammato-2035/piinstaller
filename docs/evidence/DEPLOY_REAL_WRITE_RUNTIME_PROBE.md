# DEPLOY_REAL_WRITE_RUNTIME_PROBE

- timestamp_utc: 2026-05-06T17:23:53.425579+00:00
- runtime_port: 8012
- kernel: Linux volker-ROG-Strix 6.8.0-111-generic #111-Ubuntu SMP PREEMPT_DYNAMIC Sat Apr 11 23:16:02 UTC 2026 x86_64 x86_64 x86_64 GNU/Linux
- selected_test_medium: /dev/sda

## lsblk (excerpt)
```text
NAME        PATH           TYPE   SIZE RM RO TRAN   MOUNTPOINTS
sda         /dev/sda       disk   1,8T  0  0 usb    
├─sda1      /dev/sda1      part 931,5G  0  0        /media/gabriel/setuphelfer-back
└─sda2      /dev/sda2      part 931,5G  0  0        /media/gabriel/windows-backup
nvme1n1     /dev/nvme1n1   disk   1,8T  0  0 nvme   
├─nvme1n1p1 /dev/nvme1n1p1 part   757M  0  0 nvme   
├─nvme1n1p2 /dev/nvme1n1p2 part 512,1M  0  0 nvme   
├─nvme1n1p3 /dev/nvme1n1p3 part    16M  0  0 nvme   
├─nvme1n1p4 /dev/nvme1n1p4 part 928,8G  0  0 nvme   
├─nvme1n1p5 /dev/nvme1n1p5 part   860M  0  0 nvme   
└─nvme1n1p6 /dev/nvme1n1p6 part   931G  0  0 nvme   
nvme0n1     /dev/nvme0n1   disk   1,8T  0  0 nvme   
├─nvme0n1p1 /dev/nvme0n1p1 part   512M  0  0 nvme   /boot/efi
└─nvme0n1p2 /dev/nvme0n1p2 part   1,8T  0  0 nvme   /
```

## Inspect Result (high-level)
- http_code: 200
- classification: {"system_type": "DUALBOOT", "confidence": 0.72, "indicators": ["classifier.indicator.ntfs_present", "classifier.indicator.linux_fs_present", "classifier.indicator.esp_present", "classifier.indicator.fstab_ok", "classifier.indicator.linux_kernel_artifacts", "classifier.indicator.dualboot_filesystem_pattern"], "risk_level": "high"}
- devices_classified_count: 3
- devices_raw_count: 3
- filesystems_count: 0
- mountpoints_count: 0
- network: {"interfaces": ["enp3s0", "enx00e04c6823d7", "lo", "wlp4s0"], "ipv4": [{"interface": "enp3s0", "address": "192.168.178.140"}, {"interface": "wlp4s0", "address": "192.168.178.72"}], "gateway": "192.168.178.1", "gateway_reachable": true, "code": "rescue.network.summary"}
- boot: {"boot_dir_exists": true, "firmware_dir_used": false, "primary_boot": "/boot", "kernel_files": ["vmlinuz", "vmlinuz-6.8.0-110-generic", "vmlinuz-6.8.0-111-generic", "vmlinuz-6.8.0-38-generic", "vmlinuz-6.8.0-52-generic", "vmlinuz-6.8.0-53-generic", "vmlinuz-6.8.0-85-generic", "vmlinuz.old"], "initrd_files": ["initrd.img", "initrd.img-6.8.0-110-generic", "initrd.img-6.8.0-111-generic", "initrd.img-6.8.0-38-generic", "initrd.img-6.8.0-52-generic", "initrd.img-6.8.0-53-generic", "initrd.img-6.8.0-85-generic", "initrd.img.old"], "fstab_exists": true, "fstab_lines": 3, "fstab_parse_ok": true, "fstab_code": "rescue.boot.fstab_ok", "esp": {"present": true, "source": "/dev/nvme0n1p1", "fstype": "vfat", "target": "/boot/efi"}, "codes": ["rescue.boot.layout_ok"]}

## Safety Result
- http_code: 200
- targets_count: 3
- selected_target_entry: {"device": "/dev/sda", "size": "1,8T", "classification": "allowed", "write_allowed": true, "reason_code": "SAFETY_BACKUP_TARGET_OK"}

## Hardware Gate
- gate_http_1: 200
- gate_http_2: 200
- gate_code_1: DEPLOY_HARDWARE_GATE_BLOCKED
- gate_code_2: DEPLOY_HARDWARE_GATE_BLOCKED
- readiness_level: blocked
- device_class: None
- removable: None
- transport: None
- size_bytes: None
- mount_state: {'mounted': True}
- fingerprint_stable: True
- fingerprint_1: 1d0722abd0915a6ec7d2ae23ae073b7f55cff87768f35097cf3dd173da1b4299
- fingerprint_2: 1d0722abd0915a6ec7d2ae23ae073b7f55cff87768f35097cf3dd173da1b4299
- blocked_reasons: ["DEPLOY_REAL_WRITE_BLOCKED_NON_REMOVABLE", "DEPLOY_REAL_WRITE_BLOCKED_UNKNOWN", "DEPLOY_REAL_WRITE_BLOCKED_MOUNTED", "DEPLOY_REAL_WRITE_BLOCKED_DUALBOOT"]

## Operator Protocol
- protocol_http: 200
- protocol_code: DEPLOY_HARDWARE_GATE_OPERATOR_PROTOCOL_OK
- protocol_steps_count: 10
- abort_conditions_count: 7
- confirmations_count: 0

## Negative Tests
- systemdisk: http=200, code=DEPLOY_HARDWARE_GATE_BLOCKED, readiness=blocked, blocked=["DEPLOY_REAL_WRITE_BLOCKED_NON_REMOVABLE", "DEPLOY_REAL_WRITE_BLOCKED_UNKNOWN", "DEPLOY_REAL_WRITE_BLOCKED_SYSTEM_DISK"]
- loop: http=200, code=DEPLOY_HARDWARE_GATE_BLOCKED, readiness=blocked, blocked=["DEPLOY_REAL_WRITE_BLOCKED_NON_REMOVABLE", "DEPLOY_REAL_WRITE_BLOCKED_UNKNOWN", "DEPLOY_REAL_WRITE_BLOCKED_LOOP"]
- non_removable: http=200, code=DEPLOY_HARDWARE_GATE_BLOCKED, readiness=blocked, blocked=["DEPLOY_REAL_WRITE_BLOCKED_NON_REMOVABLE"]
- mounted: http=200, code=DEPLOY_HARDWARE_GATE_BLOCKED, readiness=blocked, blocked=["DEPLOY_REAL_WRITE_BLOCKED_MOUNTED"]

## No-Write Evidence
- mounts_changed: False
- lsblk_changed: False
- no_write_operations_performed: true
- no_mount_commands_executed: true
- no_blockdevice_write_commands_executed: true

## dmesg read-only check
```text
<unavailable: Command '['dmesg', '-T']' returned non-zero exit status 1.>
```
