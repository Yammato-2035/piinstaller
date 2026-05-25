# Rescue Big Step — Status Plan

**Datum:** 2026-05-25
**Git HEAD:** `751e2cf` (Workspace-Path-Fix + Runtime-Abnahme)
**real_iso_build_allowed:** `false`
**usb_write_allowed:** `false`

| Bereich | Ziel | Status | Blocker |
|---------|------|--------|---------|
| Runtime-Gate | `/opt` konsistent | **green** | — |
| Workspace/Runtime Path Split | `/opt` Runtime, Workspace Build | **green** | — |
| Temp-Bundle | Exit 0 | **green** | — |
| Build-Tree | Exit 0 | **green** | — |
| Controlled ISO Build | ISO | **operator_required** | `sudo lb build noauto` nur im Operator-Terminal |
| Rescue ISO artifact | SHA256 | **blocked** | — |
| USB Write | blockiert | **blocked** | — |

## Entscheidung

1. Die Runtime bleibt unter `/opt/setuphelfer`; Bundle und Live-Build-Tree werden kontrolliert im Workspace `/home/volker/piinstaller` erzeugt.
2. Die vier Dashboard-/Executor-Prebuild-Schritte (`prepare_bundle`, `validate_bundle`, `prepare_tree`, `validate_tree`) sind auf `751e2cf` runtime-seitig **grün**.
3. Nächster Schritt bleibt bewusst manuell: Operator `sudo lb build noauto` im Workspace-Terminal, erst danach ISO-Scan und weitere Evidence.
