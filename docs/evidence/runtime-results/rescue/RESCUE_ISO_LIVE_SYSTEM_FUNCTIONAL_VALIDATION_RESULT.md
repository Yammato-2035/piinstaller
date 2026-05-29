# Rescue ISO — Live-System Funktionsprüfung (Operator)

**Ergebnis:** **Kein nutzbarer Setuphelfer** (Operator-Meldung)  
**Klassifikation:** `setuphelfer_not_functional`

## Operator

- VM bootet bis `debian login:` (visuell).
- Login als **root** → fehlgeschlagen.
- **Kein** sichtbarer Setuphelfer (UI, Dienste, Hinweis).

## Offline-Analyse der aktuellen `binary.hybrid.iso`

| Prüfung | Ergebnis |
|---------|----------|
| `/opt/setuphelfer-rescue` in Squashfs | **ja** (Backend, venv, frontend/dist) |
| `setuphelfer-backend.service` vorhanden | **ja** |
| Units in `multi-user.target.wants` | **nein** → Dienste starten nicht automatisch |
| `validate-rescue-iso-squashfs.sh` | Exit **11** `INTEGRATION_GAP` |

**Fazit:** Das Bundle ist **im Image**, aber die Integration für den Live-Boot war unvollständig (keine enabled Units, generischer Debian-Login statt dokumentiertem `user`/`live`).

## Build-Fix (Workspace, noch kein Rebuild)

`prepare-controlled-live-build-tree.sh`:

- systemd-Enable-Symlinks unter `multi-user.target.wants`
- `--mode debian` + `hostname=setuphelfer-rescue username=user` in `--bootappend-live`
- MOTD mit Pfad `/opt/setuphelfer-rescue`

**Nächster Operator-Schritt:** Tree neu vorbereiten, **ISO neu bauen**, dann in VM:

```text
Login: user
Passwort: live
ls /opt/setuphelfer-rescue
systemctl status setuphelfer-backend.service
curl -sS http://127.0.0.1:8000/api/version
```

JSON: `rescue_iso_live_system_functional_validation_latest.json`
