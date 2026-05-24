# Rescue Big Step — Status Plan

**Datum:** 2026-05-24  
**Git HEAD:** `dd0aa59` (Session 3)
**real_iso_build_allowed:** `false`

| Bereich | Ziel | Aktueller Status | Blocker | Entscheidung |
|---------|------|------------------------|---------|--------------|
| Temp Runtime Bundle | bereitstellen | **green** — Script + Validator Exit 0 | — | `create-temp-runtime-bundle.sh` ausführen; nicht versionieren |
| Live-Medium Network Validation | grün bekommen | **review_required** | Kein Live-Boot; USB-Copy VFAT/venv-Symlinks | Operator: ext4/tar + Live-Boot |
| Rescue Runtime Bundle | ISO-vorbereitend | **review_required** | Volles `backend/app.py` Monolith | Emulation ready; Controlled ISO Prep Gate |
| Debian-Live Config | vorbereiten | **review_required** | Kein `lb build` in diesem Auftrag | Emulation tree preview vorhanden |
| Monolith/Boundary | Buildfähigkeit prüfen | **review_required** | `app.py` ~17k Zeilen, Host-Pfade in Code | ISO-Prep möglich; kein Big-Bang-Refactor |
| Controlled ISO Build | noch blockiert | **ISO_PREP_REVIEW_REQUIRED** | Live-OS green + Operator-Freigabe fehlt | Kein ISO in diesem Auftrag |

## Entscheidung

1. **Live-Medium Session 3:** Bundle validiert; Copy auf INTENSO (VFAT) an venv-Symlinks gescheitert; **kein Live-Boot**.
2. **Monolith:** **review_required**, nicht **blocked** — gezielte Entkopplung (Phase 3) **nicht** ausgeführt.
3. **Nächster Operator-Schritt:** Bundle kopieren → Live booten → Result-Template ausfüllen.
