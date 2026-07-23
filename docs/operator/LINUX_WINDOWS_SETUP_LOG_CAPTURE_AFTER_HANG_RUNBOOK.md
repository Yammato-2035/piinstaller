# Linux: Windows-Setup-Logs nach Hang auslesen

**Kontext:** Stage A hing. PowerShell/WinPE-Collector nicht nutzbar.  
**Ziel:** Panther / Rollback / setupact / setuperr **read-only** von der Windows-NVMe auf `SETUP_LOGS` kopieren.

## Regeln

- Keine zweite Windows-Installation
- Kein BIOS-Update
- Kein Schreiben auf die Linux-NVMe
- NTFS nur **ro** (ggf. `ro,force` als Recovery, nie rw/chkdsk automatisch)
- Zielbindung über Identity Hash / EUI / PCI — nicht über `/dev/nvme0`

## Bevorzugt: Rescue-Menü

1. Ultra-Line-Rettungsstick booten (Payload **1.10.2.3**).
2. **ASUS Hardwarediagnose** / Hardware Discovery starten.
3. Phase `windows_setup_logs` abwarten.
4. Stick entnehmen, `SETUP_LOGS`-Lauf importieren.

## Manuell (falls Menü mount blockiert)

Auf dem Rettungssystem (Root-Shell):

```bash
# 1) Partitionen sehen
lsblk -o NAME,SIZE,FSTYPE,LABEL,PARTLABEL,MOUNTPOINTS
blkid

# 2) Nur Windows-Ziel-NTFS wählen (Identity aus Stage-A-Bindung)
# Beispiel: große NTFS auf der Windows-NVMe — Hash/PCI prüfen!

sudo mkdir -p /mnt/win-ro /media/SETUP_LOGS/linux-panther-capture-$(date -u +%Y%m%dT%H%M%SZ)
OUT=/media/SETUP_LOGS/linux-panther-capture-$(date -u +%Y%m%dT%H%M%SZ)
# SETUP_LOGS-Mountpunkt anpassen (oft /media/*/SETUP_LOGS*)

# 3) RO-Mount (Reihenfolge)
DEV=/dev/nvmeXn1pY   # NUR Windows-Ziel, nach Identity
sudo mount -t ntfs3 -o ro,norecover "$DEV" /mnt/win-ro \
  || sudo mount -t ntfs-3g -o ro,norecover "$DEV" /mnt/win-ro \
  || sudo mount -t ntfs-3g -o ro,force "$DEV" /mnt/win-ro

findmnt /mnt/win-ro   # muss "ro" zeigen

# 4) Logs suchen und kopieren
sudo mkdir -p "$OUT"
sudo cp -a /mnt/win-ro/\$WINDOWS.~BT/Sources/Panther "$OUT/" 2>/dev/null || true
sudo cp -a /mnt/win-ro/\$WINDOWS.~BT/Sources/Rollback "$OUT/" 2>/dev/null || true
sudo cp -a /mnt/win-ro/Windows/Panther "$OUT/" 2>/dev/null || true
sudo cp -a /mnt/win-ro/Windows/Logs/SetupDiag "$OUT/" 2>/dev/null || true
sudo cp -a /mnt/win-ro/Windows/INF/setupapi*.log "$OUT/" 2>/dev/null || true
sudo find /mnt/win-ro -iname 'setupact.log' -o -iname 'setuperr.log' -o -iname 'SetupDiagResults*' \
  | sudo tee "$OUT/find_index.txt"

sudo umount /mnt/win-ro
sync
```

## Danach

1. Gerät kontrolliert herunterfahren.
2. Stick zum Entwicklungsrechner.
3. Identity-gated Import nach `docs/evidence/rescue/asus-win11-stage-a-006/physical_runs/<run-id>/`.
4. Auswertung: Phase, HRESULT, SetupDiag — **erst dann** BIOS-335-Entscheidung.

## Hinweis zu WinPE

`collect-win11-setup-logs.cmd` braucht **kein** PowerShell. Wenn WinPE später wieder erreichbar ist, ist CMD der Fallback — aktuell reicht Linux-Auslese.
