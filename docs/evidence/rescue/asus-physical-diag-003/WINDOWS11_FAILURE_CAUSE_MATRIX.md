# WINDOWS11_FAILURE_CAUSE_MATRIX — PI-RS-ASUS-PHYSICAL-DIAG-003

Stand: vor vollständigem Gabriel-`hardware_discovery`-Lauf (Stick vorbereitet, Capture-Pfad injiziert).

| Hypothese | Evidence dafür | Evidence dagegen | Bewertung | Nächster Test |
|---|---|---|---|---|
| NVMe-Hardwarefehler | — | bisher keine SMART-Daten vom Gabriel-Lauf | insufficient_evidence | nvme smart-log + error-log auf G513QM |
| NVMe-Firmware | Samsung SM981/PM981-Familie (lspci) | keine Firmware-Revision erfasst | insufficient_evidence | nvme id-ctrl |
| GPT-/Partitionsfehler | nvme0 hatte p1–p3, nvme1 leer (dmesg 20260722) | keine sgdisk-Prüfung | plausible | parted/sgdisk read-only |
| EFI-/Bootloaderfehler | — | — | insufficient_evidence | efibootmgr -v |
| Storage-Treiber | — | — | insufficient_evidence | Panther/setupapi |
| BIOS G513QM.331 | offiziell 335 verfügbar | kein Changelog-Beweis für Win11-Abort | plausible | Changelog prüfen; Flash nur Operator |
| Installationsmedium | — | — | insufficient_evidence | Media-Hash |
| RAM-Instabilität | — | keine MCE in bisherigem dmesg-Auszug | insufficient_evidence | Memtest-Smoke |
| Strom/Temperatur | — | — | insufficient_evidence | Netzteil-only Retest |
| Windows-Image | — | — | insufficient_evidence | kontrollierter Retest mit Log-Sammlung |
| zweite NVMe beeinflusst Setup | zwei interne Samsung-NVMe | — | plausible | Rollenbindung nach Identity |

**Wahrscheinlichste Ursache (vorläufig):** `unknown` — Confidence **low**. Fehlende Panther-/SMART-Evidence.
