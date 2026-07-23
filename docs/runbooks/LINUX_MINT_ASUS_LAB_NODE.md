# LINUX_MINT_ASUS_LAB_NODE

## Status im Auftrag 006

**Plan-only / deferred** bis nach instrumentiertem Win11-Live-Capture.

## Zielplatte

Rolle `linux_lab_nvme`, Fingerprint `nvme_identity_hash=ed84d453…` — nie allein `/dev/nvme1n1`.

## Geplante Struktur

- Eigene EFI auf Linux-NVMe
- Root (+ optional Home)
- Separates SETUP_LAB / Evidence-Volume

Windows-EFI nicht als primärer Linux-Bootloader-Speicher.

## Nach Installation

Lab-Agent, Enrollment, DCC, Telemetrie, Hardwareinventar, Remote-Shell/Reboot, Job-Fortsetzung, Evidence-Upload, lokaler Kill-Switch. Keine BitLocker-Mutation.
