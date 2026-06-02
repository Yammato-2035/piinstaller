# Developer QEMU ISO Rebuild — Operator Handoff

**Datum:** 2026-06-02  
**HEAD:** `488e1ad` (+ Ingest-Lauf)

## Was schiefging

1. Buildversuch `rescue_developer_iso_20260602_212524` startete mit **`profile=standard`** (nicht developer-qemu).
2. Preflight blockierte sauber mit **LB_EXIT=34** (root-owned Top-Level-Artefakte).
3. **Kein lb build** ausgeführt (`build_started=false`).

## Abort-Regel

**Wenn im Build-Log `profile=standard` erscheint, obwohl developer-qemu ISO gewünscht ist:**

→ **sofort STOP**, Build nicht fortsetzen, kein QEMU-Folgeschritt.

## Pflichtsequenz (Operator-Terminal)

```bash
cd /home/volker/piinstaller

# 1) Profil im Tree
SETUPHELFER_RESCUE_BUILD_PROFILE=developer-qemu \
  ./scripts/rescue-live/prepare-controlled-live-build-tree.sh

# 2) Root-owned Reste entfernen (Pflicht vor Build)
sudo ./scripts/rescue-live/clean-controlled-live-build-tree.sh --operator-confirm-clean
# Erwartung: clean_exit=0, 7× REMOVED

# 3) Optional: Validate
./scripts/rescue-live/validate-controlled-live-build-tree.sh \
  build/rescue/live-build/setuphelfer-rescue-live

# 4) Build — Profil explizit
sudo -v
scripts/rescue-live/run-controlled-iso-build-with-logging.sh \
  --operator-confirm-build \
  --profile developer-qemu
```

**Prüfpunkt nach Start:** erste Log-Zeile muss enthalten:

```
profile=developer-qemu
```

## Alternativen (gleichwertig)

```bash
SETUPHELFER_RESCUE_BUILD_PROFILE=developer-qemu \
  scripts/rescue-live/run-controlled-iso-build-with-logging.sh --operator-confirm-build
```

Env geht **nicht** verloren, solange sie **vor** dem Skriptaufruf in derselben Shell gesetzt wird (Wrapper exportiert vor lb).

## Nach erfolgreichem Build

1. `validate-rescue-iso-squashfs.sh` auf `binary.hybrid.iso`
2. QEMU Guest Agent Smoke (`qemu-guest-agent-smoke-operator.sh`)
