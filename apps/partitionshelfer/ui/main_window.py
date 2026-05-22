#!/usr/bin/env python3
"""
main_window.py – Setuphelfer Partitionierungstool
Grafische Oberfläche (Phase 1: Anzeige & Analyse)

Starten mit: python3 ui/main_window.py
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, font

# Pfad damit core-Module gefunden werden
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.disk_scanner import scan_all_disks, Disk, Partition, get_fs_info
from core.safety_checks import pruefe_loeschen, hat_blockierende_warnung, WarnStufe
from ui.use_case_wizard import WizardFenster


# ──────────────────────────────────────────────────────────────
# Design-Konstanten (Setuphelfer Farbschema)
# ──────────────────────────────────────────────────────────────
FARBEN = {
    "hintergrund":    "#1A1D23",   # Dunkelblau-Grau
    "panel":          "#22262E",   # Etwas heller
    "panel_hell":     "#2C3140",   # Hover/Auswahl
    "akzent":         "#00D4AA",   # Türkis-Grün (Setuphelfer)
    "akzent_dunkel":  "#00A882",
    "text_hell":      "#F0F4FF",
    "text_mittel":    "#9BA3B8",
    "text_dunkel":    "#5A6275",
    "trennlinie":     "#333847",
    "warnung_info":   "#4CAF50",
    "warnung_warn":   "#FF9800",
    "warnung_gefahr": "#FF5722",
    "warnung_krit":   "#F44336",
    "partition_bar_bg": "#13161C",
}

FS_FARBEN = {
    "ext4":  "#4CAF50",
    "ext3":  "#8BC34A",
    "ntfs":  "#2196F3",
    "vfat":  "#FF9800",
    "exfat": "#FF5722",
    "btrfs": "#9C27B0",
    "xfs":   "#00BCD4",
    "swap":  "#F44336",
    None:    "#555E72",
}


def get_fs_farbe(fstype):
    return FS_FARBEN.get(fstype, "#607D8B")


# ──────────────────────────────────────────────────────────────
# Hilfsfunktionen
# ──────────────────────────────────────────────────────────────
def bytes_to_human(b: int) -> str:
    if b == 0:
        return "0 B"
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} PB"


# ──────────────────────────────────────────────────────────────
# Partition-Balken-Widget
# ──────────────────────────────────────────────────────────────
class PartitionBalken(tk.Canvas):
    """
    Grafischer Balken wie in GParted.
    Zeigt alle Partitionen einer Festplatte proportional.
    """

    def __init__(self, parent, disk: Disk, on_select, **kwargs):
        super().__init__(
            parent,
            bg=FARBEN["partition_bar_bg"],
            height=72,
            highlightthickness=1,
            highlightbackground=FARBEN["trennlinie"],
            cursor="hand2",
            **kwargs
        )
        self.disk = disk
        self.on_select = on_select
        self.ausgewaehlte_part = None
        self.rects = []  # [(x1,y1,x2,y2, partition)]

        self.bind("<Configure>", self._zeichnen)
        self.bind("<Button-1>", self._klick)
        self.bind("<Motion>", self._hover)

    def _zeichnen(self, event=None):
        self.delete("all")
        self.rects.clear()

        w = self.winfo_width()
        h = self.winfo_height()
        if w < 10:
            return

        rand = 8
        balken_h = h - 2 * rand
        gesamt = self.disk.size_bytes or 1
        x = rand

        parts = self.disk.partitions
        if not parts:
            return

        for i, part in enumerate(parts):
            anteil = part.size_bytes / gesamt
            breite = max(int((w - 2 * rand) * anteil), 4)

            # Letzter bekommt den Rest (Rundungsfehler vermeiden)
            if i == len(parts) - 1:
                breite = w - rand - x

            farbe = get_fs_farbe(part.fstype)
            ausgewaehlt = (part == self.ausgewaehlte_part)

            # Hintergrund-Rechteck
            rect_id = self.create_rectangle(
                x, rand, x + breite - 2, rand + balken_h,
                fill=farbe,
                outline="#1A1D23" if not ausgewaehlt else FARBEN["akzent"],
                width=2 if ausgewaehlt else 1,
            )

            # Belegungsstreifen (dunkler Streifen = belegter Teil)
            if part.is_mounted and part.used_bytes > 0 and part.size_bytes > 0:
                belegt_anteil = part.used_bytes / part.size_bytes
                belegt_breite = int((breite - 2) * belegt_anteil)
                if belegt_breite > 0:
                    self.create_rectangle(
                        x + 1, rand + balken_h - 6,
                        x + belegt_breite, rand + balken_h - 1,
                        fill="#000000", outline="", stipple="gray50"
                    )

            # Label (Name + Größe) wenn genug Platz
            if breite > 50:
                self.create_text(
                    x + breite // 2, rand + balken_h // 2 - 8,
                    text=part.name,
                    fill="white",
                    font=("Helvetica", 9, "bold"),
                    anchor="center",
                )
                self.create_text(
                    x + breite // 2, rand + balken_h // 2 + 8,
                    text=part.size_human,
                    fill="#CCCCCC",
                    font=("Helvetica", 8),
                    anchor="center",
                )

            # System-Warnung
            if part.is_system_critical and breite > 30:
                self.create_text(
                    x + breite - 12, rand + 8,
                    text="⚠",
                    fill="#FFD700",
                    font=("Helvetica", 10),
                    anchor="center",
                )

            self.rects.append((x, rand, x + breite - 2, rand + balken_h, part))
            x += breite

    def _klick(self, event):
        part = self._part_bei(event.x, event.y)
        if part:
            self.ausgewaehlte_part = part
            self._zeichnen()
            self.on_select(part)

    def _hover(self, event):
        part = self._part_bei(event.x, event.y)
        self.configure(cursor="hand2" if part else "arrow")

    def _part_bei(self, x, y):
        for x1, y1, x2, y2, part in self.rects:
            if x1 <= x <= x2 and y1 <= y <= y2:
                return part
        return None

    def markiere(self, partition):
        self.ausgewaehlte_part = partition
        self._zeichnen()


# ──────────────────────────────────────────────────────────────
# Info-Panel (rechte Seite)
# ──────────────────────────────────────────────────────────────
class InfoPanel(tk.Frame):
    """Zeigt Details zur ausgewählten Partition an."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=FARBEN["panel"], **kwargs)
        self._aufbauen()

    def _aufbauen(self):
        # Titel
        tk.Label(
            self, text="Partition-Details",
            bg=FARBEN["panel"], fg=FARBEN["akzent"],
            font=("Helvetica", 13, "bold"),
            pady=12,
        ).pack(anchor="w", padx=16)

        tk.Frame(self, bg=FARBEN["trennlinie"], height=1).pack(fill="x", padx=16)

        # Scrollbarer Bereich
        self.canvas = tk.Canvas(self, bg=FARBEN["panel"], highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.innen = tk.Frame(self.canvas, bg=FARBEN["panel"])
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.innen, anchor="nw"
        )

        self.innen.bind("<Configure>", self._scroll_update)
        self.canvas.bind("<Configure>", self._canvas_resize)

        # Platzhalter
        self._platzhalter()

    def _scroll_update(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _canvas_resize(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _platzhalter(self):
        tk.Label(
            self.innen,
            text="← Klicke auf eine\n   Partition",
            bg=FARBEN["panel"],
            fg=FARBEN["text_dunkel"],
            font=("Helvetica", 11),
            pady=40,
        ).pack()

    def zeige_partition(self, partition: Partition):
        """Aktualisiert die Anzeige mit einer Partition."""
        for widget in self.innen.winfo_children():
            widget.destroy()

        self._zeile("Name", partition.name)
        self._zeile("Pfad", f"/dev/{partition.name}")
        self._zeile("Größe", partition.size_human)

        if partition.is_mounted:
            self._zeile("Eingehängt unter", partition.mountpoint)
            if partition.used_bytes > 0:
                self._zeile("Belegt", f"{partition.used_human} ({partition.used_percent:.0f}%)")
                self._zeile("Frei", partition.free_human)
                self._belegungsbalken(partition.used_percent)

        fs_info = partition.fs_info
        self._zeile("Dateisystem", fs_info["name"])

        if partition.label:
            self._zeile("Label", partition.label)
        if partition.uuid:
            uuid_kurz = partition.uuid[:18] + "..." if len(partition.uuid) > 18 else partition.uuid
            self._zeile("UUID", uuid_kurz)

        # Dateisystem-Erklärung
        self._abschnitt("Was ist das?")
        self._text(fs_info["beschreibung"])
        self._text(f"💡 {fs_info['empfehlung']}", italic=True)

        # System-Status
        if partition.is_system_critical:
            self._abschnitt("⚠️ Systempartition")
            self._text(
                "Diese Partition wird vom laufenden System benutzt. "
                "Änderungen können dein System beschädigen.",
                farbe=FARBEN["warnung_gefahr"]
            )

        # Sicherheitsanalyse
        self._abschnitt("🛡️ Sicherheitsanalyse")
        warnungen = pruefe_loeschen(partition)
        for w in warnungen:
            self._warnung_widget(w)

        self._scroll_update()

    def _zeile(self, label: str, wert: str):
        frame = tk.Frame(self.innen, bg=FARBEN["panel"])
        frame.pack(fill="x", padx=16, pady=3)
        tk.Label(
            frame, text=f"{label}:",
            bg=FARBEN["panel"], fg=FARBEN["text_mittel"],
            font=("Helvetica", 9), width=18, anchor="w",
        ).pack(side="left")
        tk.Label(
            frame, text=wert,
            bg=FARBEN["panel"], fg=FARBEN["text_hell"],
            font=("Helvetica", 9, "bold"), anchor="w",
        ).pack(side="left", fill="x", expand=True)

    def _abschnitt(self, titel: str):
        tk.Frame(self.innen, bg=FARBEN["trennlinie"], height=1).pack(
            fill="x", padx=16, pady=(10, 0)
        )
        tk.Label(
            self.innen, text=titel,
            bg=FARBEN["panel"], fg=FARBEN["akzent"],
            font=("Helvetica", 10, "bold"),
            pady=4,
        ).pack(anchor="w", padx=16)

    def _text(self, text: str, italic=False, farbe=None):
        stil = ("Helvetica", 9, "italic") if italic else ("Helvetica", 9)
        tk.Label(
            self.innen, text=text,
            bg=FARBEN["panel"],
            fg=farbe or FARBEN["text_mittel"],
            font=stil,
            wraplength=230,
            justify="left",
            pady=2,
        ).pack(anchor="w", padx=16)

    def _belegungsbalken(self, prozent: float):
        frame = tk.Frame(self.innen, bg=FARBEN["panel"])
        frame.pack(fill="x", padx=16, pady=4)

        canvas = tk.Canvas(frame, bg=FARBEN["partition_bar_bg"],
                           height=12, highlightthickness=0)
        canvas.pack(fill="x")
        canvas.update_idletasks()

        def zeichne(event=None):
            w = canvas.winfo_width()
            if w < 2:
                return
            canvas.delete("all")
            # Hintergrund
            canvas.create_rectangle(0, 0, w, 12, fill=FARBEN["partition_bar_bg"], outline="")
            # Belegung
            farbe = "#4CAF50" if prozent < 70 else "#FF9800" if prozent < 90 else "#F44336"
            canvas.create_rectangle(0, 0, int(w * prozent / 100), 12,
                                    fill=farbe, outline="")

        canvas.bind("<Configure>", lambda e: zeichne())
        self.after(50, zeichne)

    def _warnung_widget(self, warnung):
        stufe_farben = {
            WarnStufe.INFO:     FARBEN["warnung_info"],
            WarnStufe.WARNUNG:  FARBEN["warnung_warn"],
            WarnStufe.GEFAHR:   FARBEN["warnung_gefahr"],
            WarnStufe.KRITISCH: FARBEN["warnung_krit"],
        }
        farbe = stufe_farben[warnung.stufe]

        frame = tk.Frame(
            self.innen,
            bg=FARBEN["panel_hell"],
            bd=0,
        )
        frame.pack(fill="x", padx=16, pady=3)

        # Farbiger Streifen links
        tk.Frame(frame, bg=farbe, width=3).pack(side="left", fill="y")

        inhalt = tk.Frame(frame, bg=FARBEN["panel_hell"])
        inhalt.pack(side="left", fill="x", expand=True, padx=8, pady=6)

        tk.Label(
            inhalt,
            text=f"{warnung.icon} {warnung.titel}",
            bg=FARBEN["panel_hell"],
            fg=farbe,
            font=("Helvetica", 9, "bold"),
            anchor="w",
        ).pack(anchor="w")

        tk.Label(
            inhalt,
            text=warnung.erklaerung,
            bg=FARBEN["panel_hell"],
            fg=FARBEN["text_mittel"],
            font=("Helvetica", 8),
            wraplength=210,
            justify="left",
        ).pack(anchor="w", pady=(2, 0))

        tk.Label(
            inhalt,
            text=f"→ {warnung.empfehlung}",
            bg=FARBEN["panel_hell"],
            fg=FARBEN["text_hell"],
            font=("Helvetica", 8, "italic"),
            wraplength=210,
            justify="left",
        ).pack(anchor="w", pady=(2, 0))


# ──────────────────────────────────────────────────────────────
# Disk-Listenbereich (linke/mittlere Seite)
# ──────────────────────────────────────────────────────────────
class DiskListe(tk.Frame):
    """Zeigt alle Festplatten mit grafischen Balken."""

    def __init__(self, parent, on_partition_select, **kwargs):
        super().__init__(parent, bg=FARBEN["hintergrund"], **kwargs)
        self.on_partition_select = on_partition_select
        self.disks = []
        self.balken_widgets = []
        self._aufbauen()

    def _aufbauen(self):
        # Kopfzeile
        kopf = tk.Frame(self, bg=FARBEN["panel"], pady=0)
        kopf.pack(fill="x")

        tk.Label(
            kopf,
            text="⬡  Setuphelfer Partitionshelfer",
            bg=FARBEN["panel"],
            fg=FARBEN["akzent"],
            font=("Helvetica", 14, "bold"),
            pady=12,
            padx=16,
        ).pack(side="left")

        self.btn_aktualisieren = tk.Button(
            kopf,
            text="↺ Aktualisieren",
            bg=FARBEN["panel_hell"],
            fg=FARBEN["text_hell"],
            font=("Helvetica", 9),
            relief="flat",
            padx=12, pady=6,
            cursor="hand2",
            command=self.laden,
        )
        self.btn_aktualisieren.pack(side="right", padx=(4, 12))

        self.btn_wizard = tk.Button(
            kopf,
            text="🧭 Geführte Hilfe",
            bg=FARBEN["akzent"],
            fg=FARBEN["hintergrund"],
            font=("Helvetica", 9, "bold"),
            relief="flat",
            padx=14, pady=6,
            cursor="hand2",
            command=self._wizard_oeffnen,
        )
        self.btn_wizard.pack(side="right", padx=(0, 4))

        tk.Frame(self, bg=FARBEN["trennlinie"], height=1).pack(fill="x")

        # Scrollbarer Disk-Bereich
        self.scroll_frame = tk.Frame(self, bg=FARBEN["hintergrund"])
        self.scroll_frame.pack(fill="both", expand=True)

        # Statuszeile unten
        self.status = tk.Label(
            self,
            text="Laden...",
            bg=FARBEN["panel"],
            fg=FARBEN["text_dunkel"],
            font=("Helvetica", 8),
            pady=4,
        )
        self.status.pack(fill="x", side="bottom")

    def _wizard_oeffnen(self):
        WizardFenster(self.winfo_toplevel())

    def laden(self):
        """Liest Festplatten und baut die Anzeige auf."""
        self.status.config(text="Scanne Festplatten...")
        self.update()

        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.balken_widgets.clear()

        try:
            self.disks = scan_all_disks()
        except Exception as e:
            tk.Label(
                self.scroll_frame,
                text=f"Fehler beim Lesen:\n{e}",
                bg=FARBEN["hintergrund"],
                fg=FARBEN["warnung_krit"],
                font=("Helvetica", 10),
            ).pack(pady=20)
            return

        for disk in self.disks:
            self._disk_widget(disk)

        gesamt = sum(d.size_bytes for d in self.disks)
        count = sum(len(d.partitions) for d in self.disks)
        self.status.config(
            text=f"  {len(self.disks)} Laufwerk(e)  •  {count} Partition(en)  •  "
                 f"Gesamt: {bytes_to_human(gesamt)}"
        )

    def _disk_widget(self, disk: Disk):
        """Erstellt das Widget für eine Festplatte."""
        container = tk.Frame(
            self.scroll_frame,
            bg=FARBEN["panel"],
            padx=16, pady=12,
        )
        container.pack(fill="x", pady=(0, 1))

        # Disk-Kopfzeile
        kopf = tk.Frame(container, bg=FARBEN["panel"])
        kopf.pack(fill="x", pady=(0, 8))

        # Disk-Icon + Name
        tk.Label(
            kopf,
            text="💿",
            bg=FARBEN["panel"],
            font=("Helvetica", 14),
        ).pack(side="left", padx=(0, 6))

        info_frame = tk.Frame(kopf, bg=FARBEN["panel"])
        info_frame.pack(side="left")

        tk.Label(
            info_frame,
            text=disk.display_name,
            bg=FARBEN["panel"],
            fg=FARBEN["text_hell"],
            font=("Helvetica", 11, "bold"),
            anchor="w",
        ).pack(anchor="w")

        tk.Label(
            info_frame,
            text=f"Gesamt: {disk.size_human}  •  {len(disk.partitions)} Partition(en)",
            bg=FARBEN["panel"],
            fg=FARBEN["text_mittel"],
            font=("Helvetica", 8),
            anchor="w",
        ).pack(anchor="w")

        # Grafischer Balken
        balken = PartitionBalken(
            container, disk,
            on_select=self.on_partition_select,
        )
        balken.pack(fill="x", pady=(0, 8))
        self.balken_widgets.append(balken)

        # Nach dem Zeichnen des Balkens
        self.after(100, balken._zeichnen)

        # Partitionsliste (Tabelle)
        self._partitions_tabelle(container, disk)

    def _partitions_tabelle(self, parent, disk: Disk):
        """Kompakte Tabelle unter dem Balken."""
        tabelle = tk.Frame(parent, bg=FARBEN["panel"])
        tabelle.pack(fill="x")

        # Header
        header_farben = [
            ("Name", 100), ("Größe", 80), ("Dateisystem", 100),
            ("Eingehängt", 150), ("Status", 80)
        ]
        for text, breite in header_farben:
            tk.Label(
                tabelle,
                text=text,
                bg=FARBEN["panel"],
                fg=FARBEN["text_dunkel"],
                font=("Helvetica", 8),
                width=breite // 8,
                anchor="w",
            ).grid(row=0, column=header_farben.index((text, breite)),
                   sticky="w", padx=4, pady=(0, 4))

        tk.Frame(parent, bg=FARBEN["trennlinie"], height=1).pack(fill="x", pady=(0, 4))

        for i, part in enumerate(disk.partitions):
            bg = FARBEN["panel_hell"] if i % 2 == 0 else FARBEN["panel"]
            zeile = tk.Frame(parent, bg=bg, cursor="hand2")
            zeile.pack(fill="x")
            zeile.bind("<Button-1>", lambda e, p=part: self.on_partition_select(p))

            # Farbpunkt + Name
            punkt_farbe = get_fs_farbe(part.fstype)
            tk.Label(
                zeile,
                text="●",
                bg=bg, fg=punkt_farbe,
                font=("Helvetica", 8),
            ).pack(side="left", padx=(4, 0))

            felder = [
                (part.name, 10, "text_hell"),
                (part.size_human, 9, "text_mittel"),
                (part.fs_info["name"], 12, "text_mittel"),
                (part.mountpoint or "–", 18, "text_mittel"),
            ]

            for text, width, farb_key in felder:
                lbl = tk.Label(
                    zeile, text=text,
                    bg=bg, fg=FARBEN[farb_key],
                    font=("Helvetica", 9 if farb_key == "text_hell" else 8),
                    width=width, anchor="w",
                )
                lbl.pack(side="left", padx=4, pady=3)
                lbl.bind("<Button-1>", lambda e, p=part: self.on_partition_select(p))

            # Status-Badge
            if part.is_system_critical:
                badge_text, badge_farbe = "SYSTEM", FARBEN["warnung_gefahr"]
            elif part.is_mounted:
                badge_text, badge_farbe = "Aktiv", FARBEN["warnung_info"]
            else:
                badge_text, badge_farbe = "Inaktiv", FARBEN["text_dunkel"]

            tk.Label(
                zeile, text=badge_text,
                bg=bg, fg=badge_farbe,
                font=("Helvetica", 7, "bold"),
            ).pack(side="left", padx=4)


# ──────────────────────────────────────────────────────────────
# Hauptfenster
# ──────────────────────────────────────────────────────────────
class SetuphelferApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Setuphelfer Partitionshelfer")
        self.root.geometry("1050x680")
        self.root.minsize(800, 500)
        self.root.configure(bg=FARBEN["hintergrund"])

        # Fenster zentrieren
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 1050) // 2
        y = (self.root.winfo_screenheight() - 680) // 2
        self.root.geometry(f"+{x}+{y}")

        self._aufbauen()
        self.disk_liste.laden()

    def _aufbauen(self):
        # Haupt-Layout: Links (Disks) + Rechts (Info)
        haupt = tk.PanedWindow(
            self.root,
            orient=tk.HORIZONTAL,
            sashwidth=4,
            sashrelief="flat",
            bg=FARBEN["trennlinie"],
        )
        haupt.pack(fill="both", expand=True)

        # Linker Bereich
        self.disk_liste = DiskListe(
            haupt,
            on_partition_select=self._partition_ausgewaehlt,
        )
        haupt.add(self.disk_liste, minsize=550, stretch="always")

        # Rechter Bereich
        self.info_panel = InfoPanel(haupt)
        haupt.add(self.info_panel, minsize=280, stretch="never")

        # Anfangsgröße
        self.root.update_idletasks()
        haupt.sash_place(0, 680, 0)

    def _partition_ausgewaehlt(self, partition: Partition):
        self.info_panel.zeige_partition(partition)

    def starten(self):
        self.root.mainloop()


# ──────────────────────────────────────────────────────────────
# Einstiegspunkt
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = SetuphelferApp()
    app.starten()
