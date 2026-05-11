# Recovery Minimal Execute Phase 2b (DE)

## Ziel
Erste echte, strikt begrenzte Einzelaktionen innerhalb `target_path` für Recovery-Minimal.

## Kernregeln
- Session single-use
- Token verpflichtend
- keine Aktionen außerhalb `target_path`
- kein SSH enable, kein useradd, keine Netzwerkänderung
- keine verbotenen Systemcalls

## Umgesetzte Aktionen
- Recovery-Notiz schreiben
- Setuphelfer-Agent vorbereiten (nur lokale Quelle)
- Backend-Unit vorbereiten (ohne systemctl)
- SSH/User/Netzwerk/Firewall/Backup nur als Plan-Marker
