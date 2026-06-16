# Umgebungsprüfung vor Aktionen

## Ziel
Verhindern, dass Cursor falsche Annahmen über das System trifft.

---

## PFLICHT VOR JEDEM SYSTEMEINGRIFF

Cursor muss prüfen:

1. Betriebssystem
2. Gerätetyp (Raspberry Pi / Laptop / Server)
3. Rechte (root / user)
4. Kontext (Dev / Produktiv)

---

## VERBOTEN

- automatische Installation von:
  - pytest
  - pip Paketen
  - apt Paketen

OHNE:
- vorherige Prüfung
- oder explizite Freigabe

---

## WENN UNKLAR

- STOP
- keine Annahmen treffen
- sichere Variante wählen

---

## AUSGABE

Cursor muss immer melden:

- erkannte Umgebung
- mögliche Risiken

