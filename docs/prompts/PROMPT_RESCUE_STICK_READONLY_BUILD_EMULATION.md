# PROMPT – STRICT MODE: RESCUE STICK READONLY BUILD EMULATION

Kopiere diesen Prompt für den nächsten Agenten-Lauf.

---

**STRICT MODE – RESCUE STICK READONLY BUILD EMULATION**

**ZIEL:** Den Rettungsstick-Build **nur vorbereiten und emulieren** (Snapshots, Previews, Handoffs, Evidence). **Kein** echter ISO-Build.

**VORAUSSETZUNG:**

- Runtime-Gate Exit 0
- Partitions-Finalisierung abgenommen (`PARTITIONS_FINAL_BROWSER_UI_SMOKE.md` green)
- `docs/architecture/RESCUE_STICK_READONLY_BUILD_GATE.md` gelesen

**ERLAUBT:**

- Build-Workspace-Snapshot unter `build/rescue/emulation/`
- Erwartete Debian-Live-Dateistruktur dokumentieren
- Paketlisten-Preview (aus Handoffs / Plan)
- Runtime-Bundle-Preview (`runner_rescue_runtime_bundle_manifest`)
- Frontend-Bundle-Preview (Hashes, Pfade, keine Kopie auf USB)
- systemd-Service-Preview für Live-Backend
- Network/Web-UI-Preview (Ports, keine Aktivierung am Host)
- Evidence-Manifest (`rescue_build_emulation_*.json`)
- Deploy-Runner **read-only** aufrufen: `build_environment_emulation`, `build_readiness_gate`, `debian_live_build_inputs`, `dry_build_orchestration`
- Tests für Handoff-Generierung (bestehende `test_deploy_runner_rescue_*`)

**VERBOTEN:**

- `lb build`
- debootstrap
- chroot
- `apt install` / `apt upgrade`
- mount / umount (Stick, Live-Root)
- ISO-Erzeugung (xorriso, grub-mkrescue)
- `dd`
- qemu / echter Boot-Test
- Partition-Write, Restore-Execute, Backup-Start
- Allowlist erweitern, Safety-Gates schwächen
- `git add -A`

**PHASEN:**

0. Phase-0 Runtime-Gate + `git log -1`
1. `runner_rescue_build_environment_emulation` – Snapshot schreiben/validieren
2. Debian-Live-Struktur-Preview (Verzeichnisbaum als Doku, kein Build)
3. Paketlisten-Preview aus `rescue_debian_live_build_plan.json`
4. Runtime-Bundle-Preview + Seal-Check
5. Frontend-Bundle-Preview (dist-Hash vs. `/opt`)
6. systemd-Unit-Preview für Live
7. Partitions-Handoff einbinden (`storage_safety`, `handoff_sources`)
8. Final-Gate-Dokument: `docs/evidence/rescue/RESCUE_STICK_READONLY_BUILD_EMULATION_RESULT.md`
9. `git diff --check`; nur Evidence/Doku committen

**ABNAHME green nur wenn:**

- Emulation-Handoffs geschrieben oder validiert (ohne Overwrite ohne Flag)
- Kein verbotenes Kommando ausgeführt
- Build-Gate 15-Punkte-Checkliste in Evidence referenziert
- Runtime-Gate bleibt Exit 0

---

**Ende Prompt**
