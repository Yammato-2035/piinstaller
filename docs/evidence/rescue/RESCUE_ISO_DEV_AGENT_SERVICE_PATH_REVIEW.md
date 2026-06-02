# Rescue ISO — setuphelfer-dev-agent.service Pfad-Review

**Datum:** 2026-06-02  
**HEAD:** `11453c5`

## Fundstellen

| Pfad | Typ | Kontext |
|------|-----|---------|
| `build/.../includes.chroot/etc/systemd/system/setuphelfer-dev-agent.service` | systemd Unit (Live-Image) | `Environment=PYTHONPATH=/opt/setuphelfer-rescue` Zeile 10 |
| `scripts/rescue-live/prepare-controlled-live-build-tree.sh` | Generator | schreibt Unit ins includes.chroot |
| `packaging/systemd/setuphelfer-dev-agent.service` | Host-Referenz | nutzt `/opt/setuphelfer` (nicht rescue) |

## Zeilenanalyse (Live-Image-Unit)

```
WorkingDirectory=/opt/setuphelfer-rescue/backend
Environment=PYTHONPATH=/opt/setuphelfer-rescue
Environment=SETUPHELFER_RESCUE_ROOT=/opt/setuphelfer-rescue
ExecStart=... backend.devserver_agent.cli ...
ReadWritePaths=/opt/setuphelfer-rescue/docs/evidence/... /tmp /run
```

| Prüfpunkt | Ergebnis |
|-----------|----------|
| systemd Unit im includes.chroot | ja |
| Environment-Zeile (PYTHONPATH) | ja, Zeile 10 |
| Host-Schreiboperation über Token | **nein** — nur Live-Image-Inhalt |
| Cleanup/Build/Deploy auf Host-`/opt` | **nein** |
| Live-Image-Runtimepfad | **ja** — `/opt/setuphelfer-rescue` ist der geplante Squashfs-Mount-Pfad |

## Pflichtbewertung

| Frage | Antwort |
|-------|---------|
| `/opt/setuphelfer-rescue` ist geplanter Live-Runtime-Pfad | **yes** |
| Token nur in systemd Environment/PYTHONPATH (Blocker-Zeile) | **yes** (weitere `/opt/setuphelfer-rescue`-Zeilen in derselben Unit sind ebenfalls Live-Kontext) |
| Token für Host-Schreiboperation | **no** |
| Token in Cleanup/Build/Deploy auf Host-`/opt` | **no** |
| Risiko | **`ok_intended_live_runtime_path`** |

Evidence: `rescue_iso_dangerous_path_occurrences_latest.log`
