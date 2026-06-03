# Devserver Agent Fix — Rebuild QEMU Result

**Datum:** 2026-06-03  
**HEAD:** `886a098`  
**Gesamtstatus:** **blocked** (Phase 1 Deploy)

## Zusammenfassung

Der Fix aus `886a098` ist im **Workspace** und im **developer-qemu-Profil** vorhanden, aber **nicht live unter `/opt`**. Deploy scheiterte an fehlendem `sudo` in der Agent-Session. Ohne Backend-Deploy würde QEMU erneut am **Invalid Host header** scheitern — daher wurden ISO-Build und QEMU **nicht** ausgeführt.

Port-/Profilfehler wurden **nicht** erneut als Ursache gewertet.

## Phasen

| Phase | Status | Exit / Hinweis |
|-------|--------|----------------|
| 0 Baseline | ok | HEAD `886a098`, release green |
| 1 Deploy `/opt` | **blocked** | `deploy_exit=1` (sudo) |
| 2 Clean | **skipped** | Deploy-Voraussetzung |
| 3 Prepare | **skipped** | — |
| 4 Validate tree | **skipped** | — |
| 5 ISO build | **skipped** | — |
| 6 ISO validate | **skipped** | Alter ISO SHA `614cc86e…` (pre-fix) |
| 7 QEMU smoke | **skipped** | — |

## Operator-Fortsetzung (Reihenfolge)

1. `sudo ./scripts/deploy-to-opt.sh /home/volker/piinstaller`
2. `sudo ./scripts/rescue-live/clean-controlled-live-build-tree.sh --operator-confirm-clean`
3. `SETUPHELFER_RESCUE_BUILD_PROFILE=developer-qemu ./scripts/rescue-live/prepare-controlled-live-build-tree.sh`
4. `./scripts/rescue-live/validate-controlled-live-build-tree.sh build/rescue/live-build/setuphelfer-rescue-live`
5. `scripts/rescue-live/run-controlled-iso-build-with-logging.sh --operator-confirm-build --profile developer-qemu`
6. `./scripts/rescue-live/validate-rescue-iso-squashfs.sh build/.../binary.hybrid.iso` → Exit **0**
7. `./scripts/rescue-live/qemu-guest-agent-smoke-operator.sh`

USB bleibt gesperrt, solange Guest-Report nicht grün.

## Evidence

| Datei |
|-------|
| `DEVSERVER_AGENT_FIX_REBUILD_QEMU_PHASE0.md` |
| `DEVSERVER_AGENT_FIX_DEPLOY_RESULT.md` |
| `devserver_agent_fix_rebuild_qemu_latest.json` |
