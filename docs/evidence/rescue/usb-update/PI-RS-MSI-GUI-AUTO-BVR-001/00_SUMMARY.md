# PI-RS-MSI-GUI-AUTO-BVR-001 – USB Update Summary

Erfasst: `2026-07-21T21:18:37Z`

## Ergebnis
- Payload: **1.10.1.0**
- Build-Quellcommit: `9b3c4dee`
- Build-Modus: `payload_repack` (inject-gui-bvr)
- Stick: `/dev/sda` Intenso Ultra Line
- SquashFS SHA256: `bdb8a5476e2afe97e92f405cf5d73f003040141d43f205993b2c167b20a9252f`
- GRUB Default: `Setuphelfer Lab-Auto (GUI, Physical E2E)` (`msi_e2e_auto=1`, `mode=gui`)
- Run-Control: armed (SABRENT / GE63 / one-shot / auto_shutdown)
- Workspace HEAD at evidence write: `9b3c4dee6753839a5e209552e5cedad280ac399d`

## Operator
1. SABRENT (~1 TB USB) an MSI anschließen
2. Stick stecken, Power-On — **keine Tasten**
3. GUI zeigt Auto-BVR-Fortschritt; Lauf wipe→backup→verify→restore
4. Auto-Shutdown abwarten
5. Stick zurück: `STICK ZURÜCK – IMPORT STARTEN`
