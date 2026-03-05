# -*- coding: utf-8 -*-
"""
Themen für den PI-Installer Bilderrahmen.
Jedes Thema: Anzeigename, Symbole (Unicode/Emoji), Standard-Text.
Freie Symbol-Bilder (z. B. von Pixabay) können in ~/.config/pi-installer-picture-frame/symbols/<thema>/ abgelegt werden.
Schwarze Symbole nur bei Halloween.
"""

THEMES = {
    "none": {
        "name": "Kein Thema",
        "symbols": [],
        "default_text": "",
        "animation": "none",
        "black_symbols": False,
    },
    "weihnachten": {
        "name": "Weihnachten",
        "symbols": ["🎄", "❄️", "⭐", "🎅", "🔔", "🎁", "🕯️", "🌟"],
        "default_text": "Frohe Weihnachten",
        "animation": "rain",
        "black_symbols": False,
    },
    "ostern": {
        "name": "Ostern",
        "symbols": ["🐣", "🐰", "🌸", "🥚", "🌷", "🪺", "🌿", "💐"],
        "default_text": "Frohe Ostern",
        "animation": "fly",
        "black_symbols": False,
    },
    "geburtstag": {
        "name": "Geburtstag",
        "symbols": ["🎂", "🎈", "🎁", "🎉", "🥳", "🎊", "✨", "🕯️"],
        "default_text": "Alles Gute zum Geburtstag!",
        "animation": "rain",
        "black_symbols": False,
    },
    "valentinstag": {
        "name": "Valentinstag",
        "symbols": ["❤️", "🌹", "💕", "❤️", "🌹", "💗", "💖", "🌹", "❤️", "💕"],
        "default_text": "Alles Liebe zum Valentinstag",
        "animation": "fly",
        "black_symbols": False,
    },
    "hochzeitstag": {
        "name": "Hochzeitstag",
        "symbols": ["💍", "💒", "💐", "🥂", "❤️", "💑", "✨", "🌹"],
        "default_text": "Happy Anniversary",
        "animation": "rain",
        "black_symbols": False,
    },
    "halloween": {
        "name": "Halloween",
        "symbols": ["🎃", "🦇", "🕷️", "💀", "👻", "🐈‍⬛", "🕸️", "🎃"],
        "default_text": "Frohes Halloween",
        "animation": "rain",
        "black_symbols": True,
    },
}

def get_theme(key: str) -> dict:
    return THEMES.get(key, THEMES["none"]).copy()

def theme_ids() -> list:
    return list(THEMES.keys())

def theme_display_name(key: str) -> str:
    return get_theme(key).get("name", key)
