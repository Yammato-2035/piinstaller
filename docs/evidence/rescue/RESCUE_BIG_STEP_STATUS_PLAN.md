# Rescue Big Step — Status Plan

**Datum:** 2026-05-24  
**Git HEAD:** `0d211fc` (Controlled Live Build Tree Prep)
**real_iso_build_allowed:** `false`
**usb_write_allowed:** `false`

| Bereich | Ziel | Aktueller Status | Blocker | Entscheidung |
|---------|------|------------------|---------|--------------|
| Temp Runtime Bundle | bereitstellen | **green** | — | Validator Exit 0 |
| Live-build Tree | vorbereiten | **green** | — | `prepare-controlled-live-build-tree.sh` + Validator Exit 0 |
| Controlled ISO Build Prep | ready | **ISO_BUILD_PREP_REVIEW_REQUIRED** | `lb`, xorriso fehlen | Kein ISO in diesem Auftrag |
| Live-Medium Network Validation | grün | **review_required** | Kein Live-Boot | Operator |
| Real ISO Build | blockiert | **blocked** | Operator-Freigabe | Runbook |
| USB Write | blockiert | **blocked** | Separates Gate | Runbook |

## Entscheidung

1. **Controlled Live Build Tree** erstellt unter `build/rescue/live-build/setuphelfer-rescue-live/`.
2. **auto/build** blockiert (Exit 20); kein `lb build` ausgeführt.
3. **Tools:** `lb` + `xorriso` fehlen → ISO-Build erst nach Operator-Install.
4. **Nächster Schritt:** Toolcheck grün → Operator-Freigabe → manueller `lb build`.
