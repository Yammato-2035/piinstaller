# RS-001 Stick SquashFS Acceptance

**Datum:** 2026-06-10  
**SquashFS SHA256:** `0b303d3ab563f4aeaa354813dcbf46e8fb934a3f23d4705251129f80f2ac51dc`  
**Version im SquashFS:** `1.7.10.1`

---

## Level 2 — Ergebnis

| Prüfung | Stick |
|---------|-------|
| `squashfs_content_ok` | **yes** |
| React Rescue Shell | **yes** |
| `rescue.html` | **yes** |
| Launcher Fix (1.7.10.1 baseline) | **yes** |
| Fallback TUI vorhanden | **yes** |
| Network boot-skip | **yes** |
| Telemetry default skipped | **yes** |
| wait-online neutralized | **yes** |
| Network/telemetry Boot-Autostart | **no** |

---

## Level 3 — Contract Delta (Stick vs. Workspace)

| Contract | Stick 1.7.10.1 | Workspace 1.7.11.0 |
|----------|----------------|---------------------|
| crash-safe network wrapper | **no** | **yes** |
| Status-Kurzfassung | **no** | **yes** |
| sicherer Notmodus-Text | **no** | **yes** |
| `return_to_menu` in network JSON | **no** | **yes** |

**Level 2:** ok · **Level 3 auf Stick:** review_required (Rebuild erforderlich)
