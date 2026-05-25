# Rescue ISO Build Tree Review

**Datum:** 2026-05-25
**HEAD bei Review:** `fd057ce`
**Runtime-Gate:** `./scripts/check-runtime-deploy-gate.sh` -> Exit `0`

## Ergebnis

Der verbliebene Rescue-ISO-/Build-Tree-Scope wurde gezielt fachlich geprüft.
Es wurde **kein** ISO-Build gestartet und **kein** `lb build` ausgeführt.

Verifiziert:

- Temp-Runtime-Bundle erzeugbar
- Temp-Bundle-Validator am Ende **Exit 0**
- Controlled Build-Tree erzeugbar
- Build-Tree-Validator am Ende **Exit 0**
- keine `.iso`-, `.img`-, `.qcow2`-, `filesystem.squashfs`-, `initrd*`-, `vmlinuz*`- oder `SHA256SUMS`-Artefakte im Build-Tree oder Temp-Bundle

## Review-Tabelle

| Datei | Änderung | Zweck | Risiko | Entscheidung |
|---|---|---|---|---|
| `build/rescue/live-build/setuphelfer-rescue-live/config/package-lists/setuphelfer.list.chroot` | entfernt `lsblk`, Rest bleibt minimal (`systemd`, `curl`, `jq`, `util-linux`, `python3*`) | Paketliste lokal, minimal und ohne Write-/Repair-/LAN-Daemons halten | niedrig | `include` |
| `build/rescue/live-build/setuphelfer-rescue-live/auto/config` | `lb config noauto` bleibt erhalten; zusätzliche Flags `--security false`, `--firmware-chroot false`, `--firmware-binary false` | kaputte Default-Fetches im Live-Build deterministisch abschalten, ohne Build auszuführen | niedrig | `include` |
| `build/rescue/live-build/setuphelfer-rescue-live/auto/clean` | rekursives `lb clean` entfernt; nur `rm -rf .build chroot cache binary local` | sichere, nicht rekursive Tree-Reinigung nur innerhalb der Stage-Verzeichnisse | niedrig | `include` |
| `scripts/rescue-live/prepare-controlled-live-build-tree.sh` | erzeugt Paketliste, `config/archives`, `auto/config`, `auto/clean` und kopiert Bundle; kein Build | reproduzierbare, kontrollierte Build-Tree-Vorbereitung | mittel, weil Tree-Dateien generiert werden | `include` |
| `scripts/rescue-live/validate-controlled-live-build-tree.sh` | prüft `noauto`, blockiertes `auto/build`, sicheren `auto/clean`, zusätzliche Archive-Listen und vermeidet Secret-False-Positive | falsche grüne Zustände vermeiden; Validator bleibt read-only | niedrig | `include` |
| `scripts/rescue-live/validate-temp-runtime-bundle.sh` | False-Positive-Fix fuer Secret-Scan auf eigenen Regex-Checker im Python-Quellcode | Temp-Bundle-Validator muss reproduzierbar grün werden, ohne echte Secret-Funde zu maskieren | niedrig | `include` |

## Paketlistenentscheidung

Aktuelle Paketliste:

- `systemd`
- `systemd-sysv`
- `ca-certificates`
- `curl`
- `jq`
- `iproute2`
- `iputils-ping`
- `net-tools`
- `util-linux`
- `smartmontools`
- `python3`
- `python3-venv`
- `python3-pip`

Bewertung:

- **minimal und lokal sinnvoll**
- **keine** zu frühen Partitionierungs-/Repair-Tools
- **keine** LAN-Dienste
- **kein** `openssh-server`
- `lsblk` ist als eigenes Paket nicht nötig, weil die benoetigte Read-only-Storage-Basis bereits ueber `util-linux` abgedeckt ist
- `squashfs-tools` ist fuer den kontrollierten Host-/Build-Kontext relevant, nicht fuer das lokale Runtime-Paketset im Rescue-System

## auto/config

Verifiziert:

- enthaelt `lb config noauto`
- fuehrt keinen Build aus
- Distribution bleibt `bookworm`
- ISO-Volume/Application bleiben `SETUPHELFER_RESCUE` / `Setuphelfer Rescue Live`
- keine USB-/`dd`-/`mkfs`-/`parted`-Befehle

Zusatzbewertung:

- `--security false`
- `--firmware-chroot false`
- `--firmware-binary false`

Diese Flags sind im aktuellen Stand eine gezielte Stabilisierung gegen die bereits dokumentierten kaputten Default-Repositories/Firmware-Fetches und kein Sicherheits-Gate-Bypass.

## auto/clean

Verifiziert:

- kein rekursives `lb clean`
- nur `.build`, `chroot`, `cache`, `binary`, `local`
- kein Pfad ausserhalb des Build-Trees
- keine unsicheren Wildcards

## Prepare-/Validator-Skripte

`prepare-controlled-live-build-tree.sh`:

- erzeugt Package-List reproduzierbar
- erzeugt `auto/config` mit `noauto`
- erzeugt sicheren `auto/clean`
- kopiert Temp-Runtime-Bundle
- fuehrt **keinen** Build aus
- kein `apt install`, kein `apt upgrade`, kein `mount`, kein `umount`, kein `dd`, kein `mkfs`, kein `parted`

`validate-controlled-live-build-tree.sh`:

- bleibt read-only
- erkennt `noauto`
- erkennt blockiertes `auto/build`
- erkennt sicheren `auto/clean`
- erkennt verbotene Artefakte
- erkennt CDN/Secrets
- erkennt verbotene Tokens
- fuehrt **keine** gefaehrlichen Runtime-Aktionen aus

## Validierung

Erfolgreich ausgefuehrt:

- `scripts/rescue-live/create-temp-runtime-bundle.sh`
- `scripts/rescue-live/validate-temp-runtime-bundle.sh build/rescue/temp-runtime/setuphelfer-rescue-runtime`
- `scripts/rescue-live/prepare-controlled-live-build-tree.sh`
- `scripts/rescue-live/validate-controlled-live-build-tree.sh build/rescue/live-build/setuphelfer-rescue-live`
- `PYTHONPATH=backend backend/venv/bin/python3 -m unittest backend.tests.test_deploy_runner_rescue_stick_readonly_build_emulation_v1 backend.tests.test_rescue_iso_build_dashboard_state_v1 backend.tests.test_rescue_iso_build_executor_v1 -v`
- `./scripts/check-runtime-deploy-gate.sh`

## Fazit

Der Rescue-ISO-Build-Tree ist im aktuellen Scope **grün vorbereitet**.
Das bedeutet:

- Tree/Bundle/Validatoren sind grün
- keine Artefakte wurden erzeugt
- kein Build wurde gestartet
- USB-Write bleibt blockiert

Der eigentliche ISO-Build bleibt weiterhin **review_required / operator_sudo_required** und ist **nicht** Teil dieses Commits.
