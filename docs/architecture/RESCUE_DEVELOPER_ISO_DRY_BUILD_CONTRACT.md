# Rescue Developer ISO Dry-Build Contract

## 1. Zweck

- Dry-Build prüft, ob das **Rescue Developer Profile** mit integriertem **Development Agent** in einer zukünftigen ISO korrekt materialisiert würde.
- **Kein echtes ISO.**
- **Kein chroot.**
- **Kein debootstrap.**
- **Keine USB-/Hardwareaktion.**

## 2. Input

| Input | Pfad |
|-------|------|
| Clean HEAD Runtime | `/opt/setuphelfer` @ committed HEAD |
| Developer manifest | `build/rescue/profiles/developer/manifest.json` |
| Developer env | `build/rescue/profiles/developer/environment/setuphelfer-dev-agent.env` |
| Developer systemd | `build/rescue/profiles/developer/systemd/setuphelfer-dev-agent.service` |
| Public profile | `build/rescue/profiles/public/` |
| Packaging systemd | `packaging/systemd/setuphelfer-dev-agent.service` |
| Guard script | `scripts/check-dev-agent-rescue-profile-guard.sh` |

## 3. Output

| Output | Pfad |
|--------|------|
| Dry-Build Manifest | `docs/evidence/runtime-results/rescue/rescue_developer_iso_dry_build_manifest.json` |
| Agent Profile Placement Plan | im Manifest unter `placement_plan` |
| Public Guard Result | im Manifest unter `public_profile_guard` |
| Simulated systemd enablement | im Manifest unter `systemd` |
| Evidence | `docs/evidence/rescue/RESCUE_DEVELOPER_ISO_DRY_BUILD_RESULT.md` |

## 4. Statusregeln

| Status | Bedingung |
|--------|-----------|
| **green** (`ok`) | Alle Profile validiert, Public Upload blockiert, Agent nur Developer, keine verbotenen Aktionen, keine neuen Build-Artefakte |
| **yellow** (`review_required`) | Optionale Warnungen (z. B. prior ISO artifacts in tree) |
| **red** (`blocked`) | Public Auto-Upload, öffentliche URL, Token/Secret, SSH, write action, neue Build-Artefakte, echtes ISO |

## 5. CLI

```bash
PYTHONPATH=backend:. python3 -m backend.devserver_agent.cli \
  --rescue-iso-dry-build \
  --developer-profile-root build/rescue/profiles/developer \
  --public-profile-root build/rescue/profiles/public \
  --output docs/evidence/runtime-results/rescue/rescue_developer_iso_dry_build_manifest.json \
  --json
```

Exit codes: `0` = ok, `10` = review_required, `20` = blocked.

## 6. Nächste Stufe

Erst nach Dry-Build **ok** oder begründetem **review_required** (nur prior artifacts, keine Guard-Fehler):

**RESCUE DEVELOPER ISO CONTROLLED BUILD WITH DEV AGENT PROFILE**

Operator-controlled; requires explicit prompt. No automatic ISO build.
