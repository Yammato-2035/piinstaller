# Rescue ISO isohybrid — Fix Decision

**Entscheidung:** **A — Binary-Package-List** (`setuphelfer.list.binary` → `syslinux-utils`)

## Begründung

- Fehler in **`chroot/binary.sh`**, nicht auf dem Host.
- `apt-cache`/`dpkg` auf dem Host zeigen `isohybrid` ∈ **`syslinux-utils`** (installiert).
- Live-build-Log zeigt im Binary-Stage nur **`syslinux`**, nicht **`syslinux-utils`**.

## Nicht gewählt

| Option | Warum nicht |
|--------|-------------|
| Host-Wrapper | PATH des Hosts erreicht Chroot-`binary.sh` nicht |
| isohybrid deaktivieren | `iso-hybrid` Zielbild für Rescue-Stick |
| `apt install` im Agent-Lauf | Verboten |

## Operator nach Merge/Prepare

Kein automatisches apt — nur Build-Tree aktualisieren und Retry (siehe `rescue_iso_isohybrid_fix_decision_latest.json`).

JSON: `rescue_iso_isohybrid_fix_decision_latest.json`
