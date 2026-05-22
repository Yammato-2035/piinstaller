"""
disk_scanner.py – Liest alle Festplatten und Partitionen aus.
Benötigt KEINE Root-Rechte (nur lesend).
"""

import subprocess
import json
import shutil
from dataclasses import dataclass, field
from typing import Optional


# ──────────────────────────────────────────────────────────────
# Dateisystem-Erklärungen (für die Anfänger-Ansicht)
# ──────────────────────────────────────────────────────────────
FILESYSTEM_INFO = {
    "ext4": {
        "name": "ext4",
        "beschreibung": "Standard-Linux-Dateisystem. Stabil und bewährt.",
        "empfehlung": "Für Linux-Partitionen erste Wahl.",
        "farbe": "#4CAF50",
    },
    "ext3": {
        "name": "ext3",
        "beschreibung": "Älteres Linux-Dateisystem (Vorgänger von ext4).",
        "empfehlung": "Besser auf ext4 umsteigen.",
        "farbe": "#8BC34A",
    },
    "ntfs": {
        "name": "NTFS",
        "beschreibung": "Windows-Dateisystem. Wird von Linux nur teilweise unterstützt.",
        "empfehlung": "Für Windows-Partitionen oder gemeinsame Datenlaufwerke.",
        "farbe": "#2196F3",
    },
    "vfat": {
        "name": "FAT32",
        "beschreibung": "Älteres Dateisystem, überall kompatibel.",
        "empfehlung": "Für USB-Sticks oder EFI-Boot-Partitionen.",
        "farbe": "#FF9800",
    },
    "exfat": {
        "name": "exFAT",
        "beschreibung": "Modernes FAT-Dateisystem für große Dateien.",
        "empfehlung": "Für externe Festplatten, die mit Windows und Mac geteilt werden.",
        "farbe": "#FF5722",
    },
    "btrfs": {
        "name": "Btrfs",
        "beschreibung": "Modernes Linux-Dateisystem mit Snapshots und RAID.",
        "empfehlung": "Für Fortgeschrittene oder Fedora-Nutzer.",
        "farbe": "#9C27B0",
    },
    "xfs": {
        "name": "XFS",
        "beschreibung": "Hochperformantes Linux-Dateisystem.",
        "empfehlung": "Für Server oder große Datenlaufwerke.",
        "farbe": "#00BCD4",
    },
    "swap": {
        "name": "Linux Swap",
        "beschreibung": "Auslagerungsspeicher – Erweiterung des RAMs.",
        "empfehlung": "Wird von Linux automatisch verwaltet. Nicht anfassen.",
        "farbe": "#F44336",
    },
    None: {
        "name": "Unformatiert",
        "beschreibung": "Kein Dateisystem erkannt.",
        "empfehlung": "Diese Partition wurde noch nicht formatiert.",
        "farbe": "#9E9E9E",
    },
}


def get_fs_info(fstype: Optional[str]) -> dict:
    """Gibt Dateisystem-Infos zurück, mit Fallback auf 'unbekannt'."""
    info = FILESYSTEM_INFO.get(fstype)
    if info:
        return info
    return {
        "name": fstype or "Unbekannt",
        "beschreibung": f"Dateisystem-Typ: {fstype}",
        "empfehlung": "Keine spezifische Empfehlung verfügbar.",
        "farbe": "#607D8B",
    }


# ──────────────────────────────────────────────────────────────
# Datenstrukturen
# ──────────────────────────────────────────────────────────────
@dataclass
class Partition:
    name: str                        # z.B. "sda1"
    size_bytes: int
    fstype: Optional[str]
    mountpoint: Optional[str]
    label: Optional[str]
    uuid: Optional[str]
    parttypename: Optional[str]
    children: list = field(default_factory=list)

    # Werden von disk_scanner befüllt
    used_bytes: int = 0
    free_bytes: int = 0

    @property
    def size_human(self) -> str:
        return bytes_to_human(self.size_bytes)

    @property
    def used_human(self) -> str:
        return bytes_to_human(self.used_bytes)

    @property
    def free_human(self) -> str:
        return bytes_to_human(self.free_bytes)

    @property
    def used_percent(self) -> float:
        if self.size_bytes == 0:
            return 0.0
        return (self.used_bytes / self.size_bytes) * 100

    @property
    def is_mounted(self) -> bool:
        return bool(self.mountpoint)

    @property
    def is_system_critical(self) -> bool:
        """Ist diese Partition fürs laufende System kritisch?"""
        critical = {"/", "/boot", "/boot/efi", "/usr", "/var"}
        return self.mountpoint in critical

    @property
    def display_name(self) -> str:
        if self.label:
            return f"{self.label} ({self.name})"
        return self.name

    @property
    def fs_info(self) -> dict:
        return get_fs_info(self.fstype)


@dataclass
class Disk:
    name: str                        # z.B. "sda"
    size_bytes: int
    vendor: Optional[str]
    model: Optional[str]
    partitions: list = field(default_factory=list)

    @property
    def size_human(self) -> str:
        return bytes_to_human(self.size_bytes)

    @property
    def display_name(self) -> str:
        parts = [f"/dev/{self.name}"]
        if self.model:
            parts.append(self.model)
        if self.vendor:
            parts.append(f"({self.vendor.strip()})")
        return " – ".join(parts)


# ──────────────────────────────────────────────────────────────
# Hilfsfunktionen
# ──────────────────────────────────────────────────────────────
def bytes_to_human(b: int) -> str:
    """Konvertiert Bytes in lesbare Darstellung."""
    if b == 0:
        return "0 B"
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} PB"


def _get_disk_usage() -> dict:
    """
    Liest df-Ausgabe: gemountete Partitionen mit Belegung.
    Gibt dict zurück: {mountpoint: (used_bytes, free_bytes)}
    """
    usage = {}
    try:
        result = subprocess.run(
            ["df", "--output=source,size,used,avail,target", "-B1"],
            capture_output=True, text=True, timeout=5
        )
        lines = result.stdout.strip().split("\n")[1:]  # Header überspringen
        for line in lines:
            parts = line.split()
            if len(parts) >= 5:
                mountpoint = parts[4]
                try:
                    size_b = int(parts[1])
                    used_b = int(parts[2])
                    free_b = int(parts[3])
                    usage[mountpoint] = (used_b, free_b, size_b)
                except ValueError:
                    pass
    except Exception:
        pass
    return usage


# ──────────────────────────────────────────────────────────────
# Hauptfunktion
# ──────────────────────────────────────────────────────────────
def scan_all_disks() -> list[Disk]:
    """
    Scannt alle Festplatten und Partitionen.
    Gibt eine Liste von Disk-Objekten zurück.
    Benötigt keine Root-Rechte.
    """
    # lsblk aufrufen – strukturierte JSON-Ausgabe
    result = subprocess.run(
        [
            "lsblk", "--json", "--bytes",
            "--output",
            "NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT,LABEL,UUID,PARTTYPENAME,VENDOR,MODEL"
        ],
        capture_output=True, text=True, timeout=10
    )
    data = json.loads(result.stdout)
    usage_map = _get_disk_usage()

    disks = []
    for dev in data.get("blockdevices", []):
        if dev.get("type") != "disk":
            continue

        disk = Disk(
            name=dev["name"],
            size_bytes=dev.get("size") or 0,
            vendor=dev.get("vendor"),
            model=dev.get("model"),
        )

        # Partitionen (children) verarbeiten
        children = dev.get("children") or []

        if children:
            for child in children:
                part = _build_partition(child, usage_map)
                disk.partitions.append(part)
        else:
            # Disk ohne Partitionstabelle (z.B. direkt formatiert)
            part = _build_partition(dev, usage_map)
            part.name = dev["name"]
            disk.partitions.append(part)

        disks.append(disk)

    return disks


def _build_partition(dev: dict, usage_map: dict) -> Partition:
    """Erstellt ein Partition-Objekt aus lsblk-Daten."""
    mountpoint = dev.get("mountpoint")
    used_b = 0
    free_b = 0

    if mountpoint and mountpoint in usage_map:
        used_b, free_b, _ = usage_map[mountpoint]

    part = Partition(
        name=dev.get("name", "?"),
        size_bytes=dev.get("size") or 0,
        fstype=dev.get("fstype"),
        mountpoint=mountpoint,
        label=dev.get("label"),
        uuid=dev.get("uuid"),
        parttypename=dev.get("parttypename"),
        used_bytes=used_b,
        free_bytes=free_b,
    )

    # Rekursiv: Partitionen können selbst Children haben (LVM etc.)
    for child in dev.get("children") or []:
        part.children.append(_build_partition(child, usage_map))

    return part


# ──────────────────────────────────────────────────────────────
# Quick-Test (direkt ausführbar)
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    disks = scan_all_disks()
    for disk in disks:
        print(f"\n{'='*50}")
        print(f"  Festplatte: {disk.display_name}")
        print(f"  Größe:      {disk.size_human}")
        for p in disk.partitions:
            mounted = f"→ {p.mountpoint}" if p.is_mounted else "  (nicht eingehängt)"
            critical = " ⚠️ SYSTEM" if p.is_system_critical else ""
            print(f"\n    [{p.name}] {p.size_human:>8}  {p.fs_info['name']:10} {mounted}{critical}")
            if p.is_mounted and p.used_bytes > 0:
                print(f"            Belegt: {p.used_human} / Frei: {p.free_human} ({p.used_percent:.0f}%)")
