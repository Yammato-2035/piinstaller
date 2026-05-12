#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PI-Installer Bilderrahmen – Standalone PyQt6-App.
Zeigt Bilder aus dem Picture-Verzeichnis mit Datumsanzeige,
themenbezogenem Text und animierten Symbolen (Weihnachten, Ostern, etc.).
"""

import os
import sys
import random
from pathlib import Path
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QSpinBox,
    QCheckBox,
    QGroupBox,
    QMessageBox,
    QFrame,
    QScrollArea,
)
from PyQt6.QtCore import Qt, QTimer, QRectF, QPointF, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtGui import (
    QPixmap,
    QImage,
    QFont,
    QPainter,
    QColor,
    QPen,
    QBrush,
    QFontMetrics,
    QPainterPath,
    QShortcut,
    QKeySequence,
)

try:
    from PyQt6.QtSvg import QSvgRenderer
except ImportError:
    QSvgRenderer = None

# Themen
try:
    from . import themes
except ImportError:
    import themes

APP_VERSION = "1.0.0"
WINDOW_TITLE = "PI-Installer Bilderrahmen"
_APP_DIR = os.path.dirname(os.path.abspath(__file__))
APP_SYMBOLS_DIR = os.path.join(_APP_DIR, "symbols")
CONFIG_BASE = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
CONFIG_DIR = os.path.join(CONFIG_BASE, "pi-installer-picture-frame")
CONFIG_SYMBOLS_DIR = os.path.join(CONFIG_DIR, "symbols")
os.makedirs(CONFIG_DIR, exist_ok=True)
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

# Standard: Benutzer-Pictures + Unterordner für Muster
PICTURES_DEFAULT = os.path.join(os.path.expanduser("~"), "Pictures")
SAMPLES_SUBFOLDER = "PI-Installer-Samples"

# Unterstützte Bildformate
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}

# Portrait für DSI/Display: 480×800
FRAME_WIDTH = 480
FRAME_HEIGHT = 800
WHITE_FRAME_PX = 4  # weißer Rahmen um jedes Bild (oben, unten, links, rechts)


def load_config():
    import json
    out = {
        "picture_folder": os.path.join(PICTURES_DEFAULT, SAMPLES_SUBFOLDER),
        "theme": "valentinstag",
        "custom_text": "",
        "slide_interval_sec": 10,
        "random_order": True,
        "show_date": True,
        "show_clock": False,
        "symbol_size": 32,
        "symbol_speed": 1.0,
    }
    try:
        if os.path.isfile(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                out.update({k: v for k, v in data.items() if k in out})
    except Exception:
        pass
    # Fallback: Wenn Ordner nicht existiert, Pictures root anbieten
    if not os.path.isdir(out["picture_folder"]):
        out["picture_folder"] = PICTURES_DEFAULT
    return out


def save_config(cfg):
    import json
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def list_images(folder: str) -> list:
    if not folder or not os.path.isdir(folder):
        return []
    out = []
    for name in os.listdir(folder):
        p = os.path.join(folder, name)
        if os.path.isfile(p) and Path(p).suffix.lower() in IMAGE_EXTENSIONS:
            out.append(p)
    return sorted(out)


def _symbol_bases():
    """Alle möglichen Basis-Pfade für symbols/<thema>/ (Config + App, inkl. CWD-Fallback)."""
    bases = [CONFIG_SYMBOLS_DIR, APP_SYMBOLS_DIR]
    cwd_base = os.path.join(os.getcwd(), "apps", "picture_frame", "symbols")
    if cwd_base not in bases and os.path.isdir(cwd_base):
        bases.append(cwd_base)
    return bases


def _load_symbol_pixmaps(theme_id: str, size: int) -> list:
    """Lädt rechtefreie Symbol-Bilder (PNG bevorzugt, sonst SVG) aus symbols/<theme_id>/.
    Zuerst Config-Ordner, dann App-Bundle. Liefert Liste von QPixmap (skaliert auf size×size).
    PNG funktioniert ohne QtSvg; SVG nur mit PyQt6.QtSvg.
    """
    pixmaps = []
    for base in _symbol_bases():
        dir_path = os.path.join(base, theme_id)
        if not os.path.isdir(dir_path):
            continue
        # Pro Basisname nur eine Datei: PNG bevorzugen (läuft ohne QtSvg)
        by_base = {}
        for name in sorted(os.listdir(dir_path)):
            ext = Path(name).suffix.lower()
            if ext not in (".svg", ".png"):
                continue
            path = os.path.join(dir_path, name)
            base_name = Path(name).stem
            if base_name not in by_base or ext == ".png":
                by_base[base_name] = (path, ext)
        for path, ext in by_base.values():
            path_abs = os.path.abspath(path)
            if ext == ".png":
                pix = QPixmap(path_abs)
                if not pix.isNull():
                    scaled = pix.scaled(
                        size, size,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                    pixmaps.append(scaled)
            elif ext == ".svg" and QSvgRenderer is not None:
                renderer = QSvgRenderer(path_abs)
                if renderer.isValid():
                    img = QImage(size, size, QImage.Format.Format_ARGB32_Premultiplied)
                    img.fill(Qt.GlobalColor.transparent)
                    painter = QPainter(img)
                    renderer.render(painter)
                    painter.end()
                    pixmaps.append(QPixmap.fromImage(img))
    return pixmaps


# ---- Overlay-Widget: Datum, Text, animierte Symbole ----

class SymbolSprite:
    """Einzelnes Symbol mit Position und Animation (Emoji-Text oder Bild)."""
    def __init__(self, symbol: str, width: int, height: int, size: int, animation_type: str, pixmap: QPixmap = None):
        self.symbol = symbol  # Emoji/Text, falls kein pixmap
        self.pixmap = pixmap  # optional: rechtefreies Icon-Bild
        self.size = size
        self.animation_type = animation_type
        self.x = random.randint(0, max(0, width - size))
        self.y = -size if animation_type == "rain" else random.randint(0, max(0, height - size))
        self.dx = random.choice([-1, 1]) * (0.5 + random.random() * 1.5) if animation_type == "fly" else 0
        self.dy = 1.5 + random.random() * 2.0 if animation_type == "rain" else (random.random() - 0.5) * 0.8
        self.alpha = 180 + int(75 * random.random())

    def step(self, width: int, height: int):
        self.x += self.dx
        self.y += self.dy
        if self.animation_type == "rain":
            if self.y > height + self.size:
                self.y = -self.size
                self.x = random.randint(0, max(0, width - self.size))
        else:
            if self.x < -self.size or self.x > width:
                self.dx = -self.dx
                self.x = max(0, min(width - self.size, self.x))
            if self.y < -self.size or self.y > height:
                self.dy = -self.dy
                self.y = max(0, min(height - self.size, self.y))


class OverlayWidget(QWidget):
    """Zeichnet Datum, Thema-Text und animierte Symbole über dem Bild."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.date_text = ""
        self.theme_text = ""
        self.symbols: list[SymbolSprite] = []
        self.symbol_size = 32
        self.theme_animation = "none"
        self.black_symbols = False  # nur bei Halloween
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start(50)

    def set_date_text(self, text: str):
        self.date_text = text

    def set_theme_text(self, text: str):
        self.theme_text = text

    def set_symbols_from_theme(self, theme_id: str, theme_symbols: list, animation: str, size: int, black_symbols: bool = False):
        self.symbol_size = size
        self.theme_animation = animation
        self.black_symbols = black_symbols
        # Overlay kann beim ersten Aufruf noch 0×0 sein → Parent (image_label) nutzen
        w, h = self.width(), self.height()
        if (w <= 0 or h <= 0) and self.parent() is not None:
            p = self.parent()
            w = max(w, p.width())
            h = max(h, p.height())
        if w <= 0:
            w = FRAME_WIDTH
        if h <= 0:
            h = FRAME_HEIGHT
        anim = animation if animation in ("rain", "fly") else "rain"
        # Bevorzugt rechtefreie Icon-Bilder (SVG/PNG aus symbols/<theme_id>/)
        pixmaps = _load_symbol_pixmaps(theme_id, size) if theme_id and theme_id != "none" else []
        if pixmaps:
            self.symbols = [
                SymbolSprite("", w, h, size, anim, pixmap=random.choice(pixmaps))
                for _ in range(len(pixmaps) * 2)
            ]
        else:
            self.symbols = [
                SymbolSprite(s, w, h, size, anim)
                for s in (theme_symbols or []) for _ in range(2)
            ]
        # Startpositionen für Regen
        if animation == "rain":
            for s in self.symbols:
                s.y = random.randint(-h * 2, h)
                s.x = random.randint(0, max(0, w - size))

    def _on_tick(self):
        w, h = self.width(), self.height()
        if (w <= 0 or h <= 0) and self.parent() is not None:
            p = self.parent()
            w = max(w, p.width())
            h = max(h, p.height())
        w, h = max(w, 1), max(h, 1)
        for s in self.symbols:
            s.step(w, h)
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

        # Datum (oben rechts)
        if self.date_text:
            font = QFont()
            font.setPointSize(max(10, min(24, self.width() // 30)))
            p.setFont(font)
            fm = QFontMetrics(font)
            rect = fm.boundingRect(self.date_text)
            x = self.width() - rect.width() - 20
            y = 30
            path = QPainterPath()
            path.addText(0, 0, font, self.date_text)
            p.setPen(QPen(QColor(0, 0, 0), 3))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.translate(x, y)
            p.drawPath(path)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(255, 255, 255))
            p.drawPath(path)
            p.translate(-x, -y)

        # Themen-Text (unten Mitte)
        if self.theme_text:
            font = QFont()
            font.setPointSize(max(12, min(28, self.width() // 25)))
            p.setFont(font)
            fm = QFontMetrics(font)
            tw = fm.horizontalAdvance(self.theme_text)
            x = (self.width() - tw) // 2
            y = self.height() - 40
            path = QPainterPath()
            path.addText(0, 0, font, self.theme_text)
            p.setPen(QPen(QColor(0, 0, 0), 4))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.translate(x, y)
            p.drawPath(path)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(255, 255, 220))
            p.drawPath(path)
            p.translate(-x, -y)

        # Symbole: Bild-Icons (rechtefrei) oder Emoji (schwarz nur bei Halloween)
        for s in self.symbols:
            if s.pixmap and not s.pixmap.isNull():
                if self.black_symbols:
                    p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Multiply)
                    p.setOpacity(0.9)
                else:
                    p.setOpacity(s.alpha / 255.0)
                p.drawPixmap(int(s.x), int(s.y), s.size, s.size, s.pixmap)
                p.setOpacity(1.0)
                p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            else:
                font = QFont()
                font.setPointSize(s.size)
                p.setFont(font)
                if self.black_symbols:
                    p.setPen(Qt.PenStyle.NoPen)
                    p.setBrush(QColor(0, 0, 0))
                else:
                    p.setPen(QPen(QColor(0, 0, 0), 2))
                    p.setBrush(QColor(255, 255, 255, s.alpha))
                p.drawText(int(s.x), int(s.y) + s.size, s.symbol)


# ---- Kombinierter Anzeige-Widget (Bild + Overlay in einem paintEvent → Symbole garantiert sichtbar) ----

class PictureDisplayWidget(QWidget):
    """Zeichnet Bild (mit weißem Rahmen), Datum, Thema-Text und Symbole in einem paintEvent."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(FRAME_WIDTH, FRAME_HEIGHT)
        self.setStyleSheet("background: #000000;")
        self._pixmap = None
        self._no_images_msg = ""
        self.date_text = ""
        self.theme_text = ""
        self.symbols: list[SymbolSprite] = []
        self.symbol_size = 32
        self.black_symbols = False
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start(50)

    def set_pixmap(self, pix: QPixmap):
        self._pixmap = pix
        self._no_images_msg = ""
        self.update()

    def set_no_images_message(self, msg: str):
        self._no_images_msg = msg
        self._pixmap = None
        self.update()

    def set_date_text(self, text: str):
        self.date_text = text

    def set_theme_text(self, text: str):
        self.theme_text = text

    def set_symbols_from_theme(self, theme_id: str, theme_symbols: list, animation: str, size: int, black_symbols: bool = False):
        self.symbol_size = size
        self.black_symbols = black_symbols
        w, h = self.width(), self.height()
        w, h = max(w, FRAME_WIDTH), max(h, FRAME_HEIGHT)
        anim = animation if animation in ("rain", "fly") else "rain"
        # Immer Emoji als Basis nutzen (sichtbar); Icons nur wenn geladen
        emoji_list = list(theme_symbols or [])
        if theme_id and theme_id != "none" and not emoji_list:
            th = themes.get_theme(theme_id)
            emoji_list = list(th.get("symbols", []))
        pixmaps = _load_symbol_pixmaps(theme_id, size) if theme_id and theme_id != "none" else []
        if pixmaps:
            self.symbols = [
                SymbolSprite("", w, h, size, anim, pixmap=random.choice(pixmaps))
                for _ in range(len(pixmaps) * 2)
            ]
        else:
            self.symbols = [
                SymbolSprite(s, w, h, size, anim)
                for s in emoji_list for _ in range(2)
            ]
        if animation == "rain":
            for s in self.symbols:
                s.y = random.randint(-h * 2, h)
                s.x = random.randint(0, max(0, w - size))
        self.update()

    def _on_tick(self):
        w, h = max(self.width(), 1), max(self.height(), 1)
        for s in self.symbols:
            s.step(w, h)
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        # 1) Hintergrund + Bild
        p.fillRect(self.rect(), QColor(0, 0, 0))
        if self._pixmap and not self._pixmap.isNull():
            p.drawPixmap(0, 0, self._pixmap)
        elif self._no_images_msg:
            p.setPen(QColor(200, 200, 200))
            p.setFont(QFont("Sans", 12))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self._no_images_msg)
        # 2) Datum
        if self.date_text:
            font = QFont()
            font.setPointSize(max(10, min(24, self.width() // 30)))
            p.setFont(font)
            fm = QFontMetrics(font)
            x = self.width() - fm.horizontalAdvance(self.date_text) - 20
            y = 30
            path = QPainterPath()
            path.addText(0, 0, font, self.date_text)
            p.setPen(QPen(QColor(0, 0, 0), 3))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.translate(x, y)
            p.drawPath(path)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(255, 255, 255))
            p.drawPath(path)
            p.translate(-x, -y)
        # 3) Themen-Text
        if self.theme_text:
            font = QFont()
            font.setPointSize(max(12, min(28, self.width() // 25)))
            p.setFont(font)
            fm = QFontMetrics(font)
            tw = fm.horizontalAdvance(self.theme_text)
            x = (self.width() - tw) // 2
            y = self.height() - 40
            path = QPainterPath()
            path.addText(0, 0, font, self.theme_text)
            p.setPen(QPen(QColor(0, 0, 0), 4))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.translate(x, y)
            p.drawPath(path)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(255, 255, 220))
            p.drawPath(path)
            p.translate(-x, -y)
        # 4) Symbole (Icons oder Emoji) – dezent hinterlegt, dann Symbol gut sichtbar
        p.setOpacity(1.0)
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        for s in self.symbols:
            rx, ry = int(s.x), int(s.y)
            box = QRect(rx, ry, s.size * 2, s.size * 2)
            # Leichter Hintergrund, damit Symbol auf jedem Foto lesbar ist
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(255, 255, 255, 200))
            p.drawEllipse(rx + 2, ry + 2, s.size - 4, s.size - 4)
            # Immer sichtbares Symbol: roter Kreis in der Mitte (Herz-Ersatz)
            r = max(10, s.size // 3)
            cx = rx + s.size // 2
            cy = ry + s.size // 2
            p.setPen(QPen(QColor(180, 0, 50), 2))
            p.setBrush(QColor(220, 50, 80))
            p.drawEllipse(int(cx - r), int(cy - r), r * 2, r * 2)
            # Optional: Icon oder Emoji darüber (falls sichtbar)
            if s.pixmap and not s.pixmap.isNull():
                p.setOpacity(max(0.95, s.alpha / 255.0))
                if self.black_symbols:
                    p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Multiply)
                p.drawPixmap(rx, ry, s.size, s.size, s.pixmap)
                p.setOpacity(1.0)
                p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            else:
                pts = max(20, min(s.size, 40))
                font = QFont()
                font.setPointSize(pts)
                for name in ("Noto Color Emoji", "Apple Color Emoji", "Segoe UI Emoji", "Sans"):
                    font.setFamily(name)
                    if font.exactMatch() or name == "Sans":
                        break
                p.setFont(font)
                p.setPen(QColor(255, 255, 255))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawText(box, Qt.AlignmentFlag.AlignCenter, s.symbol)
        # 5) Fallback wenn keine Symbole (z. B. Thema „Kein Thema“)
        if not self.symbols:
            p.setBrush(QColor(220, 80, 80))
            for (px, py) in [(80, 120), (200, 350), (320, 580)]:
                p.drawEllipse(px, py, 50, 50)
            p.setBrush(QColor(255, 255, 255))
            font = QFont()
            font.setPointSize(36)
            p.setFont(font)
            p.drawText(70, 160, "❤")
            p.drawText(190, 390, "❤")
            p.drawText(310, 620, "❤")


# ---- Hauptfenster ----

class PictureFrameWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.config = load_config()
        self.image_list = []
        self.current_index = 0

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        # Bild + Overlay (Datum, Text, Symbole) in einem Widget
        self.display = PictureDisplayWidget(self)
        self.display.setMinimumSize(FRAME_WIDTH, FRAME_HEIGHT)
        layout.addWidget(self.display, 1)

        # Leiste: Ordner, Einstellungen (kompakt, Ordner bleibt sichtbar)
        bar = QFrame()
        bar.setStyleSheet("background: #2d2d2d; padding: 2px 4px;")
        bar.setMaximumHeight(36)
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(4, 2, 4, 2)
        bar_layout.setSpacing(6)
        lbl_bilder = QLabel("Bilder:")
        lbl_bilder.setStyleSheet("color: #999; font-size: 11px;")
        self.folder_label = QLabel(self.config.get("picture_folder", ""))
        self.folder_label.setStyleSheet("color: #bbb; font-size: 11px;")
        self.folder_label.setMinimumWidth(80)
        self.folder_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.folder_label.setWordWrap(False)
        # setElideMode erst ab Qt 6.2 bei QLabel – weglassen für Kompatibilität
        btn_folder = QPushButton("Ordner…")
        btn_folder.setMaximumHeight(26)
        btn_folder.setStyleSheet("font-size: 11px;")
        btn_folder.clicked.connect(self.choose_folder)
        btn_settings = QPushButton("Einstellungen…")
        btn_settings.setMaximumHeight(26)
        btn_settings.setStyleSheet("font-size: 11px;")
        btn_settings.clicked.connect(self.show_settings)
        bar_layout.addWidget(lbl_bilder)
        bar_layout.addWidget(self.folder_label, 1)
        bar_layout.addWidget(btn_folder)
        bar_layout.addWidget(btn_settings)
        layout.addWidget(bar)

        self.slideshow_timer = QTimer(self)
        self.slideshow_timer.timeout.connect(self.next_image)
        self.load_folder()
        self.apply_theme_and_text()
        self.start_slideshow()

        # Vollbild mit F11
        self._fullscreen = False
        QShortcut(QKeySequence(QKeySequence.StandardKey.FullScreen), self, self._toggle_fullscreen)
        QShortcut(QKeySequence("F11"), self, self._toggle_fullscreen)

    def _toggle_fullscreen(self):
        self._fullscreen = not self._fullscreen
        if self._fullscreen:
            self.showFullScreen()
        else:
            self.showNormal()

    def choose_folder(self):
        start = self.config.get("picture_folder") or PICTURES_DEFAULT
        if not os.path.isdir(start):
            start = PICTURES_DEFAULT
        folder = QFileDialog.getExistingDirectory(self, "Bilderordner wählen", start)
        if folder:
            self.config["picture_folder"] = folder
            save_config(self.config)
            self.folder_label.setText(folder)
            self.load_folder()
            self.apply_theme_and_text()

    def load_folder(self):
        folder = self.config.get("picture_folder") or PICTURES_DEFAULT
        self.image_list = list_images(folder)
        if self.config.get("random_order"):
            random.shuffle(self.image_list)
        self.current_index = 0
        self.show_current_image()

    def show_current_image(self):
        if not self.image_list:
            self.display.set_no_images_message(
                "Keine Bilder in diesem Ordner.\nOrdner wählen oder Musterbilder anlegen."
            )
            return
        path = self.image_list[self.current_index]
        pix = QPixmap(path)
        if pix.isNull():
            self.next_image()
            return
        # Weißer Rahmen 3–4 px; Bild in der Mitte
        w, h = FRAME_WIDTH, FRAME_HEIGHT
        inner_w = w - 2 * WHITE_FRAME_PX
        inner_h = h - 2 * WHITE_FRAME_PX
        scaled = pix.scaled(
            inner_w, inner_h,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        out = QPixmap(w, h)
        out.fill(QColor(255, 255, 255))
        dx = (inner_w - scaled.width()) // 2
        dy = (inner_h - scaled.height()) // 2
        painter = QPainter(out)
        painter.drawPixmap(WHITE_FRAME_PX + dx, WHITE_FRAME_PX + dy, scaled)
        painter.end()
        self.display.set_pixmap(out)

    def next_image(self):
        if not self.image_list:
            return
        self.current_index = (self.current_index + 1) % len(self.image_list)
        self.show_current_image()

    def apply_theme_and_text(self):
        theme_id = self.config.get("theme") or "none"
        th = themes.get_theme(theme_id)
        text = (self.config.get("custom_text") or "").strip() or th.get("default_text", "")
        self.display.set_theme_text(text)

        date_fmt = "%d.%m.%Y"
        if self.config.get("show_clock"):
            date_fmt += "  %H:%M"
        self.display.set_date_text(datetime.now().strftime(date_fmt) if self.config.get("show_date") else "")

        anim = th.get("animation", "none")
        size = self.config.get("symbol_size", 32)
        black_sym = th.get("black_symbols", False)
        self.display.set_symbols_from_theme(theme_id, th.get("symbols", []), anim, size, black_symbols=black_sym)

    def start_slideshow(self):
        sec = max(5, self.config.get("slide_interval_sec", 10))
        self.slideshow_timer.start(sec * 1000)

    def show_settings(self):
        d = SettingsDialog(self.config, self)
        if d.exec() == QDialog.DialogCode.Accepted:
            self.config = d.get_config()
            save_config(self.config)
            self.folder_label.setText(self.config.get("picture_folder", ""))
            self.load_folder()
            self.apply_theme_and_text()
            self.slideshow_timer.stop()
            self.start_slideshow()


# ---- Einstellungsdialog ----

class SettingsDialog(QDialog):
    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Einstellungen – Bilderrahmen")
        self.config = dict(config)
        # Größeres Fenster, damit Ordnerpfad gut les- und auswählbar ist
        self.setMinimumSize(580, 520)
        self.resize(620, 540)
        layout = QVBoxLayout(self)

        form = QFormLayout()
        # Ordner (breites Feld, gut lesbar)
        self.folder_edit = QLineEdit(self.config.get("picture_folder", ""))
        self.folder_edit.setPlaceholderText("z.B. " + PICTURES_DEFAULT)
        self.folder_edit.setMinimumWidth(400)
        self.folder_edit.setMinimumHeight(28)
        btn_browse = QPushButton("Durchsuchen…")
        btn_browse.clicked.connect(self._browse_folder)
        row = QHBoxLayout()
        row.addWidget(self.folder_edit, 1)
        row.addWidget(btn_browse)
        form.addRow("Bilderordner:", row)

        # Thema
        self.theme_combo = QComboBox()
        for tid in themes.theme_ids():
            self.theme_combo.addItem(themes.theme_display_name(tid), tid)
        idx = self.theme_combo.findData(self.config.get("theme", "none"))
        if idx >= 0:
            self.theme_combo.setCurrentIndex(idx)
        form.addRow("Thema:", self.theme_combo)

        # Kartentext / Eigener Text (überschreibt Beispieltext des Themas)
        self.text_edit = QLineEdit(self.config.get("custom_text", ""))
        self.text_edit.setPlaceholderText("Eigenen Text eingeben – überschreibt den Beispieltext (z. B. bei Valentinstag)")
        self.text_edit.setMinimumWidth(400)
        form.addRow("Kartentext / Text über den Bildern:", self.text_edit)

        # Intervall
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(5, 300)
        self.interval_spin.setSuffix(" s")
        self.interval_spin.setValue(self.config.get("slide_interval_sec", 10))
        form.addRow("Wechselintervall:", self.interval_spin)

        # Optionen
        self.random_check = QCheckBox("Zufällige Reihenfolge")
        self.random_check.setChecked(self.config.get("random_order", True))
        form.addRow("", self.random_check)

        self.show_date_check = QCheckBox("Datum anzeigen")
        self.show_date_check.setChecked(self.config.get("show_date", True))
        form.addRow("", self.show_date_check)

        self.show_clock_check = QCheckBox("Uhrzeit anzeigen")
        self.show_clock_check.setChecked(self.config.get("show_clock", False))
        form.addRow("", self.show_clock_check)

        self.symbol_size_spin = QSpinBox()
        self.symbol_size_spin.setRange(16, 72)
        self.symbol_size_spin.setValue(self.config.get("symbol_size", 32))
        form.addRow("Symbolgröße:", self.symbol_size_spin)

        layout.addLayout(form)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse_folder(self):
        start = self.folder_edit.text() or PICTURES_DEFAULT
        folder = QFileDialog.getExistingDirectory(self, "Bilderordner", start)
        if folder:
            self.folder_edit.setText(folder)

    def get_config(self) -> dict:
        self.config["picture_folder"] = self.folder_edit.text().strip() or PICTURES_DEFAULT
        self.config["theme"] = self.theme_combo.currentData() or "none"
        self.config["custom_text"] = self.text_edit.text().strip()
        self.config["slide_interval_sec"] = self.interval_spin.value()
        self.config["random_order"] = self.random_check.isChecked()
        self.config["show_date"] = self.show_date_check.isChecked()
        self.config["show_clock"] = self.show_clock_check.isChecked()
        self.config["symbol_size"] = self.symbol_size_spin.value()
        return self.config


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("pi-installer-picture-frame")
    win = PictureFrameWindow()
    win.setFixedSize(FRAME_WIDTH, FRAME_HEIGHT + 50)  # +50 für Leiste unten
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
