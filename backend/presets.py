"""
Generische Preset-Unterstützung für den PI-Installer.

Presets liegen als JSON-Dateien im Unterordner ``backend/presets`` und können
von der API sowie dem Frontend verwendet werden, um Konfigurationen
vorzubelegen (z. B. NAS, Home-Assistant, High-Security).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Any


PRESETS_DIR = Path(__file__).parent / "presets"


def _ensure_presets_dir() -> Path:
  """
  Stellt sicher, dass das Preset-Verzeichnis existiert.
  """
  PRESETS_DIR.mkdir(parents=True, exist_ok=True)
  return PRESETS_DIR


def list_presets() -> List[Dict[str, Any]]:
  """
  Gibt eine Liste verfügbarer Presets zurück.

  Die Preset-ID entspricht dem Dateinamen ohne Endung.
  Optional können in der JSON-Datei zusätzliche Metadaten wie
  "label", "description" oder "category" hinterlegt werden.
  """
  _ensure_presets_dir()
  items: List[Dict[str, Any]] = []
  for f in sorted(PRESETS_DIR.glob("*.json")):
    preset_id = f.stem
    try:
      data = json.loads(f.read_text(encoding="utf-8") or "{}")
    except Exception:
      # Ungültige Presets werden übersprungen, statt die gesamte Liste zu brechen
      continue
    if not isinstance(data, dict):
      data = {}
    item = {
      "id": data.get("id") or preset_id,
      "name": data.get("name") or data.get("label") or preset_id,
      "description": data.get("description") or "",
      "category": data.get("category") or "general",
    }
    items.append(item)
  return items


def load_preset(preset_name: str) -> Dict[str, Any]:
  """
  Lädt eine Preset-JSON und gibt sie als Dict zurück.
  """
  _ensure_presets_dir()
  preset_file = PRESETS_DIR / f"{preset_name}.json"
  if not preset_file.exists():
    raise ValueError(f"Preset '{preset_name}' nicht gefunden.")
  with preset_file.open("r", encoding="utf-8") as f:
    data = json.load(f)
  if not isinstance(data, dict):
    raise ValueError(f"Preset '{preset_name}' ist ungültig (kein JSON-Objekt).")
  return data


def merge_preset(config: Dict[str, Any], preset: Dict[str, Any]) -> Dict[str, Any]:
  """
  Wendet das Preset auf die aktuelle Config an (rekursives Merge).

  - Schlüsselnamen in ``preset`` überschreiben bestehende Werte in ``config``.
  - Verschachtelte Dicts werden rekursiv gemerged.
  """

  for key, value in (preset or {}).items():
    if isinstance(value, dict) and isinstance(config.get(key), dict):
      config[key] = merge_preset(config[key], value)
    else:
      config[key] = value
  return config


__all__ = [
  "PRESETS_DIR",
  "list_presets",
  "load_preset",
  "merge_preset",
]

