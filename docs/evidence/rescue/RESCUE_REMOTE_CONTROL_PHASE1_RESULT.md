# Rescue Remote Control — Phase 1 Result

**HEAD:** `2e0216f` (vor Implementierung)
**Repository:** PUBLIC — Push blocked

## Implementiert

| Komponente | Status |
|------------|--------|
| Security model docs | **yes** |
| Transport / network / agent / job contracts | **yes** |
| Backend `rescue_remote/` API stubs | **yes** |
| Agent stub script | **yes** |
| Network menu stub | **yes** |
| Backend unit tests | **yes** (security 6/6; API mit FastAPI/venv) |
| Shell tests | **yes** |
| Dev-Control UI | **Doku only** (kein Frontend-Code Phase 1) |

## Persistenz

Runtime JSONL unter `build/runtime/rescue-remote/` (nicht `docs/evidence/` — vermeidet NDA-Leaks in Git).

## Sicherheit

| Check | Status |
|-------|--------|
| Remote shell disabled | **yes** |
| Arbitrary command blocked | **yes** |
| Write runbooks disabled | **yes** |
| Allowlisted read-only runbooks | **yes** |
| Redaction | **yes** |

## Nicht in Phase 1

- ISO-Integration / systemd units im Image
- QEMU-Smoke
- WireGuard
- Frontend Tab

## Nächste Schritte

1. ISO-Rebuild (Bootloader-Serial-Fix)
2. QEMU-Serial-Smoke
3. Remote-Agent in `developer-qemu`-Profil integrieren
