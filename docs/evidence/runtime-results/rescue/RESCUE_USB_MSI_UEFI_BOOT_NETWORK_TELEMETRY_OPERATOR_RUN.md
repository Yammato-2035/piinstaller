# RESCUE_USB_MSI_UEFI_BOOT_NETWORK_TELEMETRY_OPERATOR_RUN

**Status:** Operator-Handoff (noch nicht ausgeführt)  
**Version:** `1.7.4.5`  
**Gate:** USB-Write vollständig verifiziert; MSI-Boot/Netzwerk/Telemetrie ausstehend

## Ausgangslage

### USB-Stick

| Feld | Wert |
|------|------|
| Device | `/dev/sdb` |
| Modell | Ultra Line |
| Serial | `24111412110212` |
| Partition | `sdb1` 592M iso9660 `SETUPHELFER_RESCUE` |
| ISO SHA256 | `9ef1b330c6ec774dfa1966c2f87c3c3ef31b3adf421f64fa2375c90408f21f3a` |
| Block-Readback SHA256 | **identisch** |
| UEFI-Artefakte | `BOOTX64.EFI`, `boot/grub/efi.img`, `isolinux/isolinux.bin` (byte-identisch zur ISO) |

### ISO-Inhalt (SquashFS, vorab validiert)

- Intel WLAN: `iwlwifi-9000*.ucode` vorhanden
- Intel BT: `intel/ibt-17-16-1.sfi` vorhanden
- `wireless-regdb` / `regulatory.db` vorhanden
- `NetworkManager` + `/usr/bin/nmcli` vorhanden
- `setuphelfer-serial-boot-markers.service`: `ConditionVirtualization=qemu` (kein `TTYPath` auf Hardware)

## Operator-Test auf MSI-Laptop

### Hardware (erwartet)

- Intel Core i7
- GeForce-Grafik (NVIDIA)
- Intel WLAN/Bluetooth (iwlwifi-9000 + ibt-17-16-1)

### Vorbereitung

1. Stick sicher auswerfen: `udisksctl power-off -b /dev/sdb`
2. MSI-Laptop herunterfahren
3. **Secure Boot aus**
4. UEFI-Bootmenü → USB-Stick als **UEFI**-Medium wählen

---

## Prüfpunkte beim Boot

### 1. UEFI-Bootmenü

- [ ] USB-Stick als UEFI-Medium sichtbar?
- [ ] Secure Boot aus?
- [ ] Boot startet vom Stick (nicht interne NVMe)?

### 2. Bootscreen / Live-System

- [ ] GRUB/UEFI-Boot sichtbar?
- [ ] Live-System startet (Setuphelfer Rescue)?
- [ ] Keine `iwlwifi` firmware-missing-Fehler in `dmesg`?
- [ ] Keine `intel/ibt-17-16-1.sfi`-Fehler?
- [ ] `setuphelfer-serial-boot-markers.service` **nicht** failed (QEMU-only Unit)?

### 3. Login / Shell

- [ ] Login `user` / Passwort `live` funktioniert?
- [ ] systemd aktiv (`init=/lib/systemd/systemd`)?
- [ ] `systemctl --failed` ohne unerwartete FAILED-Units?

### 4. Netzwerk

- [ ] `systemctl status NetworkManager` → active
- [ ] `nmcli dev status` → WLAN-Gerät sichtbar?
- [ ] WLAN-Verbindung möglich?
- [ ] IP-Adresse erhalten (`ip addr`)?

### 5. Telemetrie zum Developer-Laptop

- [ ] Developer-Laptop im gleichen Netz erreichbar?
- [ ] Rescue-Telemetrie-Endpoint erreichbar (falls Agent aktiv)?
- [ ] DCC zeigt Rescue-Boot/Telemetry-Ereignis?

---

## Operator-Kommandos im Live-System

```bash
systemctl --failed
systemctl status NetworkManager --no-pager
nmcli dev status
ip addr
ip route
dmesg | grep -Ei 'iwlwifi|firmware|bluetooth|ibt|nvidia|nouveau|failed'
ls /lib/firmware | grep -E 'iwlwifi-9000|regulatory'
find /lib/firmware/intel -name 'ibt-17-16-1.sfi' -print
```

Falls Setuphelfer-Rescue-Agent/Telemetrie vorhanden:

```bash
# Nur falls im Live-System konfiguriert — IP des Developer-Laptops einsetzen:
curl -sS http://<DEVELOPER_LAPTOP_IP>:8000/api/rescue/telemetry/health
```

**Keine Windows-Partitionen mounten.**

---

## Windows-Inspect

**Nicht ausführen**, solange Netzwerk/Telemetrie nicht grün validiert wurde.

Gate bleibt:

```text
target_laptop_booted_from_stick: false  → true erst nach MSI-Boot-Dokumentation
target_network_telemetry_validated: false  → true erst nach Netzwerk/Telemetrie-OK
windows_inspect_executable: false
```

---

## Ergebnis dokumentieren in

```text
docs/evidence/runtime-results/rescue/RESCUE_USB_MSI_UEFI_BOOT_OPERATOR_RESULT.md
```

Bei Boot-Fehler: **`RESCUE_USB_UEFI_BOOT_FAILURE_MSI_TRIAGE`**

Bei Netzwerk-Fehler: **`RESCUE_MSI_WLAN_NETWORKMANAGER_OPERATOR_TRIAGE`**

Nach erfolgreichem Boot + Netzwerk: **`WINDOWS11_RESCUE_OPERATOR_HARDWARE_READONLY_RUN`** (nur wenn Gate freigegeben)

---

## Nicht ausführen in diesem Handoff

dd, erneutes USB-Schreiben, Windows-Inspect, Backup, Restore, Deploy.
