"""
safety_checks.py – Prüft jede Aktion VOR der Ausführung.
Gibt verständliche Warnungen auf Deutsch zurück.
"""

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .disk_scanner import Partition, Disk


# ──────────────────────────────────────────────────────────────
# Warnstufen
# ──────────────────────────────────────────────────────────────
class WarnStufe(Enum):
    INFO = "info"          # Grün  – Hinweis, alles OK
    WARNUNG = "warnung"    # Gelb  – Aufpassen
    GEFAHR = "gefahr"      # Orange – Ernstes Problem
    KRITISCH = "kritisch"  # Rot   – Stopp, zu riskant


WARNSTUFE_FARBEN = {
    WarnStufe.INFO:     "#4CAF50",
    WarnStufe.WARNUNG:  "#FF9800",
    WarnStufe.GEFAHR:   "#FF5722",
    WarnStufe.KRITISCH: "#F44336",
}

WARNSTUFE_ICONS = {
    WarnStufe.INFO:     "ℹ️",
    WarnStufe.WARNUNG:  "⚠️",
    WarnStufe.GEFAHR:   "🔶",
    WarnStufe.KRITISCH: "🛑",
}


@dataclass
class Warnung:
    stufe: WarnStufe
    titel: str
    erklaerung: str          # Verständlich für Anfänger
    empfehlung: str          # Was soll der Nutzer tun?
    blockiert: bool = False  # True = Aktion wird verhindert

    @property
    def farbe(self) -> str:
        return WARNSTUFE_FARBEN[self.stufe]

    @property
    def icon(self) -> str:
        return WARNSTUFE_ICONS[self.stufe]


# ──────────────────────────────────────────────────────────────
# Prüfungen für: Löschen einer Partition
# ──────────────────────────────────────────────────────────────
def pruefe_loeschen(partition) -> list[Warnung]:
    """
    Gibt eine Liste von Warnungen zurück.
    Wenn blockiert=True in einer Warnung: Aktion stoppen.
    """
    warnungen = []

    # 1. Systemkritische Partition?
    if partition.is_system_critical:
        warnungen.append(Warnung(
            stufe=WarnStufe.KRITISCH,
            titel="Systempartition – Löschen verhindert",
            erklaerung=(
                f"'{partition.mountpoint}' ist ein wichtiger Teil deines "
                "laufenden Betriebssystems. Wenn du diese Partition löschst, "
                "startet dein Computer danach nicht mehr."
            ),
            empfehlung="Diese Partition darf nicht gelöscht werden.",
            blockiert=True,
        ))

    # 2. Partition ist eingehängt (gemountet)?
    elif partition.is_mounted:
        warnungen.append(Warnung(
            stufe=WarnStufe.GEFAHR,
            titel="Partition ist gerade aktiv",
            erklaerung=(
                f"Diese Partition ist unter '{partition.mountpoint}' "
                "eingehängt und wird gerade vom System benutzt. "
                "Das Löschen könnte Datenverlust verursachen."
            ),
            empfehlung="Zuerst die Partition aushängen (unmount), dann löschen.",
            blockiert=True,
        ))

    # 3. Noch viel freier Speicher → vielleicht nicht nötig
    if not hat_blockierende_warnung(warnungen):
        if partition.size_bytes > 0 and partition.used_bytes > 0:
            freie_quote = partition.free_bytes / partition.size_bytes
            if freie_quote > 0.5:
                warnungen.append(Warnung(
                    stufe=WarnStufe.INFO,
                    titel="Noch viel Speicher frei",
                    erklaerung=(
                        f"Diese Partition ist nur zu "
                        f"{partition.used_percent:.0f}% belegt "
                        f"({partition.free_human} frei). "
                        "Vielleicht musst du sie gar nicht löschen?"
                    ),
                    empfehlung=(
                        "Überlege, ob du Dateien verschieben kannst, "
                        "anstatt die Partition zu löschen."
                    ),
                ))

    # 4. Swap-Partition?
    if partition.fstype == "swap":
        warnungen.append(Warnung(
            stufe=WarnStufe.WARNUNG,
            titel="Swap-Partition",
            erklaerung=(
                "Das ist eine Auslagerungspartition – Linux benutzt sie "
                "als Erweiterung des Arbeitsspeichers (RAM). "
                "Ohne Swap kann das System bei Speichermangel einfrieren."
            ),
            empfehlung=(
                "Swap nur löschen, wenn du genug RAM hast (8+ GB) "
                "oder eine andere Swap-Partition anlegst."
            ),
        ))

    # 5. EFI-Boot-Partition?
    if partition.parttypename and "EFI" in partition.parttypename.upper():
        warnungen.append(Warnung(
            stufe=WarnStufe.KRITISCH,
            titel="EFI-Boot-Partition – Löschen verhindert",
            erklaerung=(
                "Diese Partition enthält den Bootloader – also das Programm, "
                "das deinen Computer startet. Ohne sie startet "
                "weder Linux noch Windows."
            ),
            empfehlung=(
                "EFI-Partitionen niemals löschen, außer du weißt "
                "genau was du tust und hast eine Backup-Boot-Partition."
            ),
            blockiert=True,
        ))

    # Keine Warnungen = grünes Licht
    if not warnungen:
        warnungen.append(Warnung(
            stufe=WarnStufe.INFO,
            titel="Keine Risiken erkannt",
            erklaerung="Diese Partition kann sicher gelöscht werden.",
            empfehlung="Denk daran: Alle Daten darauf gehen verloren!",
        ))

    return warnungen


# ──────────────────────────────────────────────────────────────
# Prüfungen für: Verkleinern einer Partition
# ──────────────────────────────────────────────────────────────
def pruefe_verkleinern(partition, neue_groesse_bytes: int) -> list[Warnung]:
    warnungen = []

    if partition.is_system_critical:
        warnungen.append(Warnung(
            stufe=WarnStufe.KRITISCH,
            titel="Systempartition – Sehr riskant",
            erklaerung=(
                "Das Verkleinern der laufenden Systempartition ist "
                "sehr riskant. Ein Fehler kann dein System unbootbar machen."
            ),
            empfehlung=(
                "Starte von einem Live-USB-System (z.B. Ubuntu Live) "
                "und führe die Aktion dort aus."
            ),
            blockiert=False,  # Warnung, aber nicht blockiert
        ))

    # Neue Größe kleiner als belegter Speicher?
    if neue_groesse_bytes < partition.used_bytes:
        warnungen.append(Warnung(
            stufe=WarnStufe.KRITISCH,
            titel="Neue Größe zu klein – Datenverlust!",
            erklaerung=(
                f"Die Partition enthält {partition.used_human} an Daten, "
                f"aber die neue Zielgröße ist nur "
                f"{bytes_to_human(neue_groesse_bytes)}. "
                "Das würde deine Daten abschneiden."
            ),
            empfehlung=(
                f"Wähle mindestens {partition.used_human} plus "
                "10% Puffer als neue Mindestgröße."
            ),
            blockiert=True,
        ))

    # Zu wenig Puffer?
    puffer = neue_groesse_bytes - partition.used_bytes
    if 0 < puffer < (partition.size_bytes * 0.1):
        warnungen.append(Warnung(
            stufe=WarnStufe.WARNUNG,
            titel="Sehr wenig freier Speicher übrig",
            erklaerung=(
                f"Nach dem Verkleinern bleiben nur "
                f"{bytes_to_human(puffer)} frei. "
                "Das kann zu Problemen führen, wenn das System Platz braucht."
            ),
            empfehlung="Empfohlen: Mindestens 10-15% der Partitionsgröße als Puffer lassen.",
        ))

    return warnungen


# ──────────────────────────────────────────────────────────────
# Hilfsfunktionen
# ──────────────────────────────────────────────────────────────
from .disk_scanner import bytes_to_human


def hat_blockierende_warnung(warnungen: list[Warnung]) -> bool:
    """Gibt True zurück wenn mindestens eine Warnung die Aktion blockiert."""
    return any(w.blockiert for w in warnungen)


# ──────────────────────────────────────────────────────────────
# Quick-Test
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    sys.path.insert(0, "..")
    from core.disk_scanner import scan_all_disks

    disks = scan_all_disks()
    for disk in disks:
        print(f"\n{'='*50}")
        print(f"Disk: {disk.display_name}")
        for p in disk.partitions:
            print(f"\n  Prüfe Partition: {p.name}")
            warnungen = pruefe_loeschen(p)
            for w in warnungen:
                print(f"  {w.icon} [{w.stufe.value.upper()}] {w.titel}")
                print(f"     → {w.erklaerung[:80]}...")
