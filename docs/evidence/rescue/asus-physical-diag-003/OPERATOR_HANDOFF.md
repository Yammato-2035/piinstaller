# Operator-Handoff — PI-RS-ASUS-PHYSICAL-DIAG-003

## Stick

- Ultra Line USB (`/dev/sda`), Labels **SETUPHELFER** + **SETUP_LOGS**
- Payload **1.10.2.0** (inject), SHA256 `5c1ebd83d756250bf60cbc237bf1f9091d099fb96571ed784e43e53f1e96190f`

## Auf Gabriels G513QM

1. Netzteil anschließen.
2. Stick booten.
3. GRUB: **Setuphelfer ASUS Hardwarediagnose (nur Lesen)**  
   (kein MSI-Lab, kein Auto-Shutdown, `setuphelfer_hardware_discovery=1`).
4. Im Textmenü: **Hardwarediagnose (nur Lesen / Gabriel)**.
5. Phrase bestätigen: `Dies ist Gabriels ASUS ROG Strix G513QM.`
6. Keine Storage-/BIOS-Schreibfreigabe.
7. Stick erst nach Evidence-Finalizer entfernen.
8. Stick zurück zum Entwicklungsrechner → Import.

## Verboten

- BIOS-Flash, Partitionierung, Installer, NTFS rw, `nvme format`.
