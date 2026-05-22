"""
use_case_wizard.py – Anfängerführung durch typische Szenarien.
Kernstück des Alleinstellungsmerkmals von Setuphelfer.

Statt: "Klick auf Partition, dann auf Formatieren"
Bietet: "Was willst du erreichen?" → Schritt-für-Schritt-Anleitung
"""

import tkinter as tk
from dataclasses import dataclass, field
from typing import Optional, Callable

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.disk_scanner import scan_all_disks  # noqa: F401 — für spätere Laufwerksauswahl

# ──────────────────────────────────────────────────────────────
# Farbschema (konsistent mit main_window.py)
# ──────────────────────────────────────────────────────────────
F = {
    "hintergrund":  "#1A1D23",
    "panel":        "#22262E",
    "panel_hell":   "#2C3140",
    "akzent":       "#00D4AA",
    "akzent_dunkel":"#00A882",
    "text_hell":    "#F0F4FF",
    "text_mittel":  "#9BA3B8",
    "text_dunkel":  "#5A6275",
    "trennlinie":   "#333847",
    "warn_ok":      "#4CAF50",
    "warn_gelb":    "#FF9800",
    "warn_rot":     "#F44336",
    "btn_normal":   "#2C3140",
    "btn_hover":    "#3D4559",
}


# ──────────────────────────────────────────────────────────────
# Use-Case-Definitionen
# ──────────────────────────────────────────────────────────────
@dataclass
class Schritt:
    nummer: int
    titel: str
    beschreibung: str
    warnung: Optional[str] = None         # Orangene Warnung
    tipp: Optional[str] = None            # Grüner Tipp
    aktion_label: Optional[str] = None   # Label des Buttons im Hauptfenster
    aktion_key: Optional[str] = None     # Technischer Key für spätere Anbindung


@dataclass
class UseCase:
    key: str
    titel: str
    untertitel: str
    icon: str
    schwierigkeit: str    # "Einfach" / "Mittel" / "Fortgeschritten"
    dauer: str            # z.B. "5–10 Minuten"
    beschreibung: str
    voraussetzungen: list[str]
    schritte: list[Schritt]
    abschluss_hinweis: str
    farbe: str = "#00D4AA"


USE_CASES: list[UseCase] = [

    # ── 1. Externe Festplatte formatieren ─────────────────────
    UseCase(
        key="externe_platte",
        titel="Externe Festplatte formatieren",
        untertitel="Für Windows, Mac und Linux nutzbar machen",
        icon="💾",
        schwierigkeit="Einfach",
        dauer="3–5 Minuten",
        farbe="#4CAF50",
        beschreibung=(
            "Du hast eine neue externe Festplatte oder einen USB-Stick "
            "und willst ihn frisch einrichten – oder eine alte Platte "
            "vollständig löschen und neu starten."
        ),
        voraussetzungen=[
            "Externe Festplatte oder USB-Stick angeschlossen",
            "Alle wichtigen Daten davon gesichert (wird alles gelöscht!)",
        ],
        schritte=[
            Schritt(
                nummer=1,
                titel="Laufwerk identifizieren",
                beschreibung=(
                    "Schau in der Laufwerksliste links, welches dein externes "
                    "Laufwerk ist. Externe Platten heißen meist 'sdb', 'sdc' usw. "
                    "Tipp: Stecke die Platte aus und wieder ein – das Laufwerk, "
                    "das neu auftaucht, ist deins."
                ),
                tipp="Achte auf die Größenangabe – das hilft beim Identifizieren.",
            ),
            Schritt(
                nummer=2,
                titel="Vorhandene Partitionen löschen",
                beschreibung=(
                    "Klicke auf jede Partition des Laufwerks und lösche sie. "
                    "Danach hast du 'unzugeordneten Speicher' – das ist gewollt."
                ),
                warnung="Lösche NUR Partitionen auf deinem externen Laufwerk, nicht auf sda!",
                aktion_label="Partition löschen",
                aktion_key="delete_partition",
            ),
            Schritt(
                nummer=3,
                titel="Neue Partition erstellen",
                beschreibung=(
                    "Klicke auf den unzugeordneten Bereich und erstelle eine "
                    "neue Partition. Lass die Größe auf Maximum (gesamtes Laufwerk)."
                ),
                tipp="Für maximale Kompatibilität: Eine einzige große Partition.",
                aktion_label="Neue Partition erstellen",
                aktion_key="create_partition",
            ),
            Schritt(
                nummer=4,
                titel="Dateisystem wählen",
                beschreibung=(
                    "Wähle das Dateisystem je nach Verwendungszweck:\n\n"
                    "• exFAT → Für Windows + Mac + Linux (empfohlen)\n"
                    "• NTFS  → Nur für Windows-Nutzung\n"
                    "• ext4  → Nur für Linux-Nutzung"
                ),
                tipp="exFAT ist meistens die beste Wahl für externe Laufwerke.",
                aktion_label="Dateisystem wählen & formatieren",
                aktion_key="format_partition",
            ),
            Schritt(
                nummer=5,
                titel="Änderungen anwenden",
                beschreibung=(
                    "Alle Aktionen werden zunächst nur geplant, nicht sofort "
                    "ausgeführt. Klicke auf 'Anwenden', um alles auf einmal "
                    "zu schreiben."
                ),
                warnung="Danach werden alle Daten auf dem Laufwerk unwiderruflich gelöscht!",
                aktion_label="✓ Anwenden",
                aktion_key="apply_changes",
            ),
        ],
        abschluss_hinweis=(
            "Fertig! Dein Laufwerk ist jetzt formatiert. "
            "Du kannst es sicher auswerfen (rechtsklick → Auswerfen) "
            "und direkt auf anderen Computern nutzen."
        ),
    ),

    # ── 2. Dual Boot vorbereiten ───────────────────────────────
    UseCase(
        key="dual_boot",
        titel="Dual-Boot vorbereiten",
        untertitel="Windows und Linux auf einer Festplatte",
        icon="🖥️",
        schwierigkeit="Mittel",
        dauer="15–30 Minuten",
        farbe="#2196F3",
        beschreibung=(
            "Du willst Windows und Linux gleichzeitig installiert haben "
            "und beim Start wählen, welches System startet. "
            "Dafür musst du Platz auf der Windows-Partition freimachen."
        ),
        voraussetzungen=[
            "Windows ist bereits installiert",
            "Mindestens 30 GB freier Speicher auf der Windows-Partition",
            "Backup aller wichtigen Daten erstellt",
            "Linux-Installations-USB bereit",
        ],
        schritte=[
            Schritt(
                nummer=1,
                titel="EFI-Partition suchen & merken",
                beschreibung=(
                    "Schaue dir alle Partitionen an. Es gibt eine kleine Partition "
                    "(100–500 MB), die als 'EFI System Partition' markiert ist. "
                    "Merke dir den Namen (z.B. sda1). Diese Partition niemals löschen!"
                ),
                warnung="EFI-Partition = Startprogramm für alle Betriebssysteme. Nicht anfassen!",
            ),
            Schritt(
                nummer=2,
                titel="Windows-Partition identifizieren",
                beschreibung=(
                    "Die Windows-Partition ist meist die größte NTFS-Partition "
                    "(z.B. 'sda3' oder 'C:'). Klicke sie an und schau dir die "
                    "Details rechts an – sie sollte mehrere Dutzend GB groß sein."
                ),
                tipp="Windows ist NTFS. Linux-Partitionen wären ext4.",
            ),
            Schritt(
                nummer=3,
                titel="Windows-Partition verkleinern",
                beschreibung=(
                    "Verkleinere die Windows-Partition, um Platz für Linux zu schaffen. "
                    "Empfehlung:\n\n"
                    "• Für Windows: Aktuelle Größe minus 30–50 GB\n"
                    "• Für Linux: Mindestens 20 GB, besser 40+ GB\n\n"
                    "Beispiel: Partition hat 200 GB → verkleinere auf 150 GB → "
                    "50 GB für Linux."
                ),
                warnung=(
                    "Starte Windows danach einmal und lass chkdsk laufen, "
                    "bevor du mit Linux weitermachst."
                ),
                aktion_label="Partition verkleinern",
                aktion_key="resize_partition",
            ),
            Schritt(
                nummer=4,
                titel="Linux-Partition erstellen",
                beschreibung=(
                    "Im neu entstandenen freien Bereich: Erstelle eine neue "
                    "Partition mit ext4-Dateisystem. Das wird deine Linux-Partition.\n\n"
                    "Optional: Erstelle zusätzlich eine Swap-Partition "
                    "(2–4 GB, Typ: Linux Swap) für den Ruhezustand."
                ),
                tipp="Linux-Installer kann Partitionen auch selbst erstellen – das hier ist nur Vorbereitung.",
                aktion_label="Neue Partition erstellen",
                aktion_key="create_partition",
            ),
            Schritt(
                nummer=5,
                titel="Änderungen anwenden & Linux installieren",
                beschreibung=(
                    "Wende die Änderungen an, dann starte den Rechner neu mit "
                    "dem Linux-USB-Stick. Beim Linux-Installer wählst du "
                    "'Neben Windows installieren' oder 'Partition manuell auswählen' "
                    "und zeigst auf die gerade erstellte ext4-Partition."
                ),
                aktion_label="✓ Anwenden",
                aktion_key="apply_changes",
            ),
        ],
        abschluss_hinweis=(
            "Nach der Linux-Installation wird GRUB installiert – das ist das "
            "Startmenü, das dir beim Einschalten die Wahl zwischen Windows und "
            "Linux gibt. Beim ersten Neustart siehst du dieses Menü."
        ),
    ),

    # ── 3. Linux-Neuinstallation ───────────────────────────────
    UseCase(
        key="linux_neuinstall",
        titel="Linux frisch installieren",
        untertitel="Gesamte Festplatte für Linux vorbereiten",
        icon="🐧",
        schwierigkeit="Einfach",
        dauer="10–15 Minuten",
        farbe="#9C27B0",
        beschreibung=(
            "Du willst einen Computer komplett auf Linux umstellen "
            "und Windows nicht mehr behalten. Die gesamte Festplatte "
            "wird für Linux eingerichtet."
        ),
        voraussetzungen=[
            "Alle Daten gesichert (alles wird gelöscht!)",
            "Linux-Installations-USB bereit",
            "Computer bootet von USB (ggf. BIOS-Einstellung nötig)",
        ],
        schritte=[
            Schritt(
                nummer=1,
                titel="Alle Partitionen löschen",
                beschreibung=(
                    "Lösche alle vorhandenen Partitionen auf der Zielfestplatte. "
                    "Danach bleibt nur 'unzugeordneter Speicher' übrig. "
                    "Das ist korrekt so."
                ),
                warnung="Wähle die richtige Festplatte! Externe Laufwerke vorher abziehen.",
                aktion_label="Alle Partitionen löschen",
                aktion_key="delete_partition",
            ),
            Schritt(
                nummer=2,
                titel="EFI-Partition erstellen (für UEFI-Systeme)",
                beschreibung=(
                    "Erstelle zuerst eine kleine EFI-Partition:\n\n"
                    "• Größe: 512 MB\n"
                    "• Dateisystem: FAT32\n"
                    "• Typ: EFI System Partition\n\n"
                    "Diese braucht dein Computer zum Starten von Linux."
                ),
                tipp="Weißt du nicht ob dein PC UEFI hat? Schau im BIOS oder prüfe ob /sys/firmware/efi existiert.",
                aktion_label="Neue Partition erstellen",
                aktion_key="create_partition",
            ),
            Schritt(
                nummer=3,
                titel="Swap-Partition erstellen (optional)",
                beschreibung=(
                    "Erstelle eine Swap-Partition für den Ruhezustand:\n\n"
                    "• Weniger als 4 GB RAM: Swap = doppelter RAM\n"
                    "• 4–8 GB RAM: Swap = RAM-Größe\n"
                    "• Mehr als 8 GB RAM: 2–4 GB reichen\n\n"
                    "Kannst du überspringen – Linux nutzt dann eine Swap-Datei."
                ),
                tipp="Modernes Linux richtet Swap-Dateien automatisch ein. Swap-Partition ist optional.",
                aktion_label="Neue Partition erstellen",
                aktion_key="create_partition",
            ),
            Schritt(
                nummer=4,
                titel="Root-Partition erstellen",
                beschreibung=(
                    "Erstelle die Hauptpartition für Linux:\n\n"
                    "• Größe: Rest der Festplatte\n"
                    "• Dateisystem: ext4\n"
                    "• Einhängepunkt: /\n\n"
                    "Hier kommt dein Betriebssystem und alle Daten drauf."
                ),
                aktion_label="Neue Partition erstellen",
                aktion_key="create_partition",
            ),
            Schritt(
                nummer=5,
                titel="Anwenden & Linux installieren",
                beschreibung=(
                    "Wende die Änderungen an. Dann starte mit dem "
                    "Linux-USB-Stick und wähle beim Installer "
                    "'Partitionen manuell'. Zeige auf deine gerade "
                    "erstellten Partitionen."
                ),
                aktion_label="✓ Anwenden",
                aktion_key="apply_changes",
            ),
        ],
        abschluss_hinweis=(
            "Die Partitionen sind vorbereitet. Starte jetzt den Linux-Installer "
            "und wähle 'Partitionen manuell belegen'. Du erkennst deine Partitionen "
            "an den Größen und Dateisystemen."
        ),
    ),

    # ── 4. Speicherplatz freimachen ────────────────────────────
    UseCase(
        key="speicher_freimachen",
        titel="Speicherplatz freimachen",
        untertitel="Partition vergrößern wenn der Platz knapp wird",
        icon="📊",
        schwierigkeit="Mittel",
        dauer="10–20 Minuten",
        farbe="#FF9800",
        beschreibung=(
            "Deine Linux-Partition läuft voll? Du willst sie vergrößern, "
            "indem du den Platz von einer anderen Partition nimmst – "
            "zum Beispiel einer ungenutzten Windows-Partition."
        ),
        voraussetzungen=[
            "Eine andere Partition mit freiem Speicher vorhanden",
            "Backup der wichtigen Daten",
            "Du kannst von einem Live-USB-System starten (für Systempartitionen)",
        ],
        schritte=[
            Schritt(
                nummer=1,
                titel="Platzsituation analysieren",
                beschreibung=(
                    "Klicke jede Partition an und schau dir rechts die "
                    "Belegungsanzeige an. Suche eine Partition die:\n\n"
                    "• Viel freien Speicher hat (>50% frei)\n"
                    "• Direkt neben der vollen Partition liegt\n"
                    "• Nicht als SYSTEM markiert ist"
                ),
                tipp="Partitionen können nur vergrößert werden wenn direkt daneben freier Platz ist.",
            ),
            Schritt(
                nummer=2,
                titel="Nachbarpartition verkleinern",
                beschreibung=(
                    "Verkleinere die Nachbarpartition um den Betrag, "
                    "den du brauchst. Der freigewordene Bereich muss "
                    "direkt neben deiner vollen Partition liegen.\n\n"
                    "Beispiel: Sda3 ist voll, sda4 hat viel Platz → "
                    "Verkleinere sda4 → sda3 kann wachsen."
                ),
                warnung="Systempartitionen (/, /boot) nur von einem Live-USB-System aus ändern!",
                aktion_label="Partition verkleinern",
                aktion_key="resize_partition",
            ),
            Schritt(
                nummer=3,
                titel="Volle Partition vergrößern",
                beschreibung=(
                    "Jetzt hat die volle Partition freien Platz daneben. "
                    "Klicke sie an und wähle 'Vergrößern'. "
                    "Ziehe die Größe auf den gewünschten Wert."
                ),
                aktion_label="Partition vergrößern",
                aktion_key="resize_partition",
            ),
            Schritt(
                nummer=4,
                titel="Anwenden & prüfen",
                beschreibung=(
                    "Wende die Änderungen an. Nach dem Neustart prüfe "
                    "mit 'df -h' im Terminal ob die Partition größer ist."
                ),
                tipp="Nach dem Anwenden: Neustart empfohlen damit das System die neue Größe erkennt.",
                aktion_label="✓ Anwenden",
                aktion_key="apply_changes",
            ),
        ],
        abschluss_hinweis=(
            "Deine Partition sollte jetzt mehr Speicher haben. "
            "Prüfe im Terminal mit 'df -h' oder im Dateimanager, "
            "ob die neue Größe angezeigt wird."
        ),
    ),
]


# ──────────────────────────────────────────────────────────────
# Wizard-Fenster
# ──────────────────────────────────────────────────────────────
class WizardFenster(tk.Toplevel):
    """
    Das Use-Case-Wizard-Fenster.
    Öffnet sich über dem Hauptfenster.
    """

    def __init__(self, parent, on_use_case_gewaehlt: Optional[Callable] = None):
        super().__init__(parent)
        self.title("Partitionshelfer – Was möchtest du tun?")
        self.geometry("720x580")
        self.minsize(600, 480)
        self.configure(bg=F["hintergrund"])
        self.resizable(True, True)
        self.grab_set()  # Modal

        self.on_use_case_gewaehlt = on_use_case_gewaehlt
        self.aktueller_use_case: Optional[UseCase] = None
        self.aktueller_schritt: int = 0

        # Zentrieren über Parent
        self.update_idletasks()
        px = parent.winfo_x()
        py = parent.winfo_y()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        x = px + (pw - 720) // 2
        y = py + (ph - 580) // 2
        self.geometry(f"+{x}+{y}")

        self._zeige_auswahl()

    # ── Schritt 0: Use-Case-Auswahl ───────────────────────────
    def _zeige_auswahl(self):
        self._leere_fenster()
        self.title("Partitionshelfer – Was möchtest du tun?")

        # Header
        header = tk.Frame(self, bg=F["panel"], pady=0)
        header.pack(fill="x")
        tk.Label(
            header,
            text="Was möchtest du tun?",
            bg=F["panel"], fg=F["akzent"],
            font=("Helvetica", 16, "bold"),
            pady=16, padx=20,
        ).pack(side="left")
        tk.Label(
            header,
            text="Wähle dein Ziel – ich führe dich Schritt für Schritt.",
            bg=F["panel"], fg=F["text_mittel"],
            font=("Helvetica", 9),
            padx=20,
        ).pack(side="left")

        tk.Frame(self, bg=F["trennlinie"], height=1).pack(fill="x")

        # Use-Case-Karten
        scroll_container = tk.Frame(self, bg=F["hintergrund"])
        scroll_container.pack(fill="both", expand=True, padx=20, pady=16)

        for uc in USE_CASES:
            self._use_case_karte(scroll_container, uc)

        # Abbrechen
        tk.Frame(self, bg=F["trennlinie"], height=1).pack(fill="x")
        tk.Button(
            self,
            text="Abbrechen",
            bg=F["btn_normal"], fg=F["text_mittel"],
            font=("Helvetica", 9),
            relief="flat", padx=16, pady=8,
            cursor="hand2",
            command=self.destroy,
        ).pack(side="right", padx=16, pady=10)

    def _use_case_karte(self, parent, uc: UseCase):
        karte = tk.Frame(
            parent,
            bg=F["panel"],
            cursor="hand2",
        )
        karte.pack(fill="x", pady=(0, 8))

        # Hover-Effekt
        def hover_ein(e):
            karte.configure(bg=F["panel_hell"])
            for child in karte.winfo_children():
                self._farbe_rekursiv(child, F["panel_hell"])

        def hover_aus(e):
            karte.configure(bg=F["panel"])
            for child in karte.winfo_children():
                self._farbe_rekursiv(child, F["panel"])

        karte.bind("<Enter>", hover_ein)
        karte.bind("<Leave>", hover_aus)
        karte.bind("<Button-1>", lambda e, u=uc: self._zeige_wizard(u))

        # Farbstreifen links
        tk.Frame(karte, bg=uc.farbe, width=4).pack(side="left", fill="y")

        # Icon
        tk.Label(
            karte, text=uc.icon,
            bg=F["panel"], font=("Helvetica", 26),
            padx=12, pady=10,
        ).pack(side="left")

        # Text
        text_frame = tk.Frame(karte, bg=F["panel"])
        text_frame.pack(side="left", fill="both", expand=True, pady=10)

        tk.Label(
            text_frame, text=uc.titel,
            bg=F["panel"], fg=F["text_hell"],
            font=("Helvetica", 11, "bold"), anchor="w",
        ).pack(anchor="w")

        tk.Label(
            text_frame, text=uc.untertitel,
            bg=F["panel"], fg=F["text_mittel"],
            font=("Helvetica", 9), anchor="w",
        ).pack(anchor="w")

        badges = tk.Frame(text_frame, bg=F["panel"])
        badges.pack(anchor="w", pady=(4, 0))

        schwierigkeit_farben = {
            "Einfach": F["warn_ok"],
            "Mittel": F["warn_gelb"],
            "Fortgeschritten": F["warn_rot"],
        }
        s_farbe = schwierigkeit_farben.get(uc.schwierigkeit, F["text_mittel"])

        tk.Label(
            badges, text=f"● {uc.schwierigkeit}",
            bg=F["panel"], fg=s_farbe,
            font=("Helvetica", 8),
        ).pack(side="left", padx=(0, 12))

        tk.Label(
            badges, text=f"⏱ {uc.dauer}",
            bg=F["panel"], fg=F["text_dunkel"],
            font=("Helvetica", 8),
        ).pack(side="left")

        # Pfeil
        tk.Label(
            karte, text="›",
            bg=F["panel"], fg=uc.farbe,
            font=("Helvetica", 18),
            padx=12,
        ).pack(side="right")

        # Bind auf alle Child-Widgets
        for child in karte.winfo_children():
            child.bind("<Button-1>", lambda e, u=uc: self._zeige_wizard(u))
            child.bind("<Enter>", hover_ein)
            child.bind("<Leave>", hover_aus)

    # ── Schritt 1+: Wizard-Schritte ───────────────────────────
    def _zeige_wizard(self, uc: UseCase, schritt_nr: int = 0):
        self.aktueller_use_case = uc
        self.aktueller_schritt = schritt_nr
        self._leere_fenster()
        self.title(f"Partitionshelfer – {uc.titel}")

        schritt = uc.schritte[schritt_nr] if schritt_nr < len(uc.schritte) else None
        ist_intro = (schritt_nr == -1)

        # Header mit Fortschrittsanzeige
        header = tk.Frame(self, bg=F["panel"])
        header.pack(fill="x")

        header_oben = tk.Frame(header, bg=F["panel"])
        header_oben.pack(fill="x", padx=20, pady=(12, 4))

        tk.Label(
            header_oben, text=f"{uc.icon}  {uc.titel}",
            bg=F["panel"], fg=uc.farbe,
            font=("Helvetica", 13, "bold"),
        ).pack(side="left")

        if schritt:
            tk.Label(
                header_oben,
                text=f"Schritt {schritt.nummer} von {len(uc.schritte)}",
                bg=F["panel"], fg=F["text_dunkel"],
                font=("Helvetica", 9),
            ).pack(side="right")

        # Fortschrittsbalken
        fortschritt_canvas = tk.Canvas(header, bg=F["panel"],
                                        height=4, highlightthickness=0)
        fortschritt_canvas.pack(fill="x", padx=20, pady=(0, 10))

        def zeichne_fortschritt(event=None):
            w = fortschritt_canvas.winfo_width()
            if w < 2 or not schritt:
                return
            fortschritt_canvas.delete("all")
            fortschritt_canvas.create_rectangle(0, 0, w, 4,
                                                  fill=F["panel_hell"], outline="")
            anteil = schritt.nummer / len(uc.schritte)
            fortschritt_canvas.create_rectangle(0, 0, int(w * anteil), 4,
                                                  fill=uc.farbe, outline="")

        fortschritt_canvas.bind("<Configure>", lambda e: zeichne_fortschritt())
        self.after(50, zeichne_fortschritt)

        tk.Frame(self, bg=F["trennlinie"], height=1).pack(fill="x")

        # Inhalt
        inhalt = tk.Frame(self, bg=F["hintergrund"])
        inhalt.pack(fill="both", expand=True, padx=24, pady=16)

        if schritt:
            # Schritt-Titel
            tk.Label(
                inhalt, text=f"{schritt.nummer}. {schritt.titel}",
                bg=F["hintergrund"], fg=F["text_hell"],
                font=("Helvetica", 14, "bold"), anchor="w",
            ).pack(anchor="w", pady=(0, 8))

            # Beschreibung
            tk.Label(
                inhalt, text=schritt.beschreibung,
                bg=F["hintergrund"], fg=F["text_mittel"],
                font=("Helvetica", 10),
                wraplength=650, justify="left", anchor="nw",
            ).pack(anchor="w", pady=(0, 12))

            # Warnung (orange)
            if schritt.warnung:
                warn_frame = tk.Frame(inhalt, bg=F["warn_gelb"])
                warn_frame.pack(fill="x", pady=(0, 8))
                tk.Frame(warn_frame, bg=F["warn_gelb"], width=4).pack(side="left", fill="y")
                warn_inhalt = tk.Frame(warn_frame, bg="#2C2400")
                warn_inhalt.pack(side="left", fill="x", expand=True, padx=8, pady=8)
                tk.Label(
                    warn_inhalt, text=f"⚠️  {schritt.warnung}",
                    bg="#2C2400", fg="#FFD700",
                    font=("Helvetica", 9),
                    wraplength=580, justify="left",
                ).pack(anchor="w")

            # Tipp (grün)
            if schritt.tipp:
                tipp_frame = tk.Frame(inhalt, bg=F["warn_ok"])
                tipp_frame.pack(fill="x", pady=(0, 8))
                tk.Frame(tipp_frame, bg=F["warn_ok"], width=4).pack(side="left", fill="y")
                tipp_inhalt = tk.Frame(tipp_frame, bg="#1A2C1A")
                tipp_inhalt.pack(side="left", fill="x", expand=True, padx=8, pady=8)
                tk.Label(
                    tipp_inhalt, text=f"💡  {schritt.tipp}",
                    bg="#1A2C1A", fg="#A5D6A7",
                    font=("Helvetica", 9, "italic"),
                    wraplength=580, justify="left",
                ).pack(anchor="w")

        # Schritt-Navigation am Ende
        tk.Frame(self, bg=F["trennlinie"], height=1).pack(fill="x")
        nav = tk.Frame(self, bg=F["panel"])
        nav.pack(fill="x", padx=16, pady=10)

        # Zurück-Button
        if schritt_nr > 0:
            tk.Button(
                nav, text="← Zurück",
                bg=F["btn_normal"], fg=F["text_mittel"],
                font=("Helvetica", 9), relief="flat",
                padx=14, pady=7, cursor="hand2",
                command=lambda: self._zeige_wizard(uc, schritt_nr - 1),
            ).pack(side="left")
        else:
            tk.Button(
                nav, text="← Übersicht",
                bg=F["btn_normal"], fg=F["text_mittel"],
                font=("Helvetica", 9), relief="flat",
                padx=14, pady=7, cursor="hand2",
                command=self._zeige_auswahl,
            ).pack(side="left")

        # Weiter / Fertig
        ist_letzter = (schritt_nr >= len(uc.schritte) - 1)

        if ist_letzter:
            tk.Button(
                nav, text="✓ Fertig",
                bg=uc.farbe, fg=F["hintergrund"],
                font=("Helvetica", 10, "bold"), relief="flat",
                padx=18, pady=7, cursor="hand2",
                command=lambda: self._zeige_abschluss(uc),
            ).pack(side="right")
        else:
            tk.Button(
                nav, text="Weiter →",
                bg=uc.farbe, fg=F["hintergrund"],
                font=("Helvetica", 10, "bold"), relief="flat",
                padx=18, pady=7, cursor="hand2",
                command=lambda: self._zeige_wizard(uc, schritt_nr + 1),
            ).pack(side="right")

        # Schritt-Punkte (Minimap)
        punkte_frame = tk.Frame(nav, bg=F["panel"])
        punkte_frame.pack(side="right", padx=16)
        for i in range(len(uc.schritte)):
            farbe = uc.farbe if i == schritt_nr else (
                F["warn_ok"] if i < schritt_nr else F["panel_hell"]
            )
            tk.Label(
                punkte_frame, text="●",
                bg=F["panel"], fg=farbe,
                font=("Helvetica", 8),
            ).pack(side="left", padx=2)

    def _zeige_abschluss(self, uc: UseCase):
        self._leere_fenster()
        self.title(f"Partitionshelfer – {uc.titel} abgeschlossen")

        tk.Frame(self, bg=F["panel"], height=60).pack(fill="x")
        tk.Label(
            self, text="✓", bg=F["hintergrund"], fg=uc.farbe,
            font=("Helvetica", 48),
        ).pack(pady=(24, 8))
        tk.Label(
            self, text="Alle Schritte erledigt!",
            bg=F["hintergrund"], fg=F["text_hell"],
            font=("Helvetica", 16, "bold"),
        ).pack()
        tk.Label(
            self, text=uc.abschluss_hinweis,
            bg=F["hintergrund"], fg=F["text_mittel"],
            font=("Helvetica", 10),
            wraplength=560, justify="center",
            pady=12,
        ).pack(padx=40)

        tk.Frame(self, bg=F["trennlinie"], height=1).pack(fill="x", pady=(20, 0))
        nav = tk.Frame(self, bg=F["panel"])
        nav.pack(fill="x", padx=16, pady=10)

        tk.Button(
            nav, text="← Neue Aufgabe wählen",
            bg=F["btn_normal"], fg=F["text_mittel"],
            font=("Helvetica", 9), relief="flat",
            padx=14, pady=7, cursor="hand2",
            command=self._zeige_auswahl,
        ).pack(side="left")

        tk.Button(
            nav, text="Schließen",
            bg=uc.farbe, fg=F["hintergrund"],
            font=("Helvetica", 10, "bold"), relief="flat",
            padx=18, pady=7, cursor="hand2",
            command=self.destroy,
        ).pack(side="right")

    # ── Hilfsmethoden ─────────────────────────────────────────
    def _leere_fenster(self):
        for widget in self.winfo_children():
            widget.destroy()

    def _farbe_rekursiv(self, widget, farbe):
        try:
            widget.configure(bg=farbe)
        except Exception:
            pass
        for child in widget.winfo_children():
            self._farbe_rekursiv(child, farbe)


# ──────────────────────────────────────────────────────────────
# Quick-Test (standalone)
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Test")
    root.geometry("200x100")
    root.configure(bg="#1A1D23")

    tk.Button(
        root, text="Wizard öffnen",
        command=lambda: WizardFenster(root),
        bg="#00D4AA", fg="#1A1D23",
        font=("Helvetica", 11, "bold"),
        relief="flat", padx=16, pady=8,
    ).pack(expand=True)

    root.mainloop()
