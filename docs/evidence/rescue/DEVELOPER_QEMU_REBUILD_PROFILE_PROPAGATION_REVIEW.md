# Developer QEMU Rebuild — Profile Propagation Review

**Datum:** 2026-06-02

## Ursache Profil-Mismatch

Der Wrapper `run-controlled-iso-build-with-logging.sh` setzt:

```bash
RESCUE_BUILD_PROFILE="${SETUPHELFER_RESCUE_BUILD_PROFILE:-standard}"
```

Ohne `--profile` und ohne gesetzte Umgebungsvariable startet jeder Build mit **`profile=standard`** — wie im Log `START … profile=standard run_id=rescue_developer_iso_20260602_212524`.

Der fehlgeschlagene Versuch führte **kein** `SETUPHELFER_RESCUE_BUILD_PROFILE=developer-qemu` und **kein** `--profile developer-qemu` aus.

## Checkliste

| Frage | Antwort |
|-------|---------|
| Unterstützt `prepare-controlled-live-build-tree.sh` developer-qemu? | **yes** (`SETUPHELFER_RESCUE_BUILD_PROFILE=developer-qemu`) |
| Unterstützt `run-controlled-iso-build-with-logging.sh` developer-qemu? | **yes** (Env oder `--profile developer-qemu`; Code-Zweig Zeile 281+) |
| Variable beim Build-Wrapper erneut setzen? | **Empfohlen:** ja — `--profile developer-qemu` **oder** Env vor Aufruf |
| Verlust durch sudo? | **Nein** für Profil-Log-Zeile — wird vor `sudo lb build` in der Shell des Operators gelesen; `export SETUPHELFER_RESCUE_BUILD_PROFILE` im Wrapper |
| Prepare vor Build mit gleichem Profil? | **Pflicht** — sonst Exit 33 (dev-agent.env / Tree-Marker) |

## Empfohlener korrekter Ablauf

```bash
cd /home/volker/piinstaller
SETUPHELFER_RESCUE_BUILD_PROFILE=developer-qemu \
  ./scripts/rescue-live/prepare-controlled-live-build-tree.sh

sudo ./scripts/rescue-live/clean-controlled-live-build-tree.sh --operator-confirm-clean

sudo -v
scripts/rescue-live/run-controlled-iso-build-with-logging.sh \
  --operator-confirm-build \
  --profile developer-qemu
```

Alternative (gleichwertig):

```bash
SETUPHELFER_RESCUE_BUILD_PROFILE=developer-qemu \
  scripts/rescue-live/run-controlled-iso-build-with-logging.sh --operator-confirm-build
```

## Status

**needs_wrapper_doc_fix** (behoben: Usage nennt jetzt `developer-qemu` und Abort-Regel bei `profile=standard`)

Kein Code-Fix für Profil-Propagation nötig — nur Operator-Disziplin + Doku.
