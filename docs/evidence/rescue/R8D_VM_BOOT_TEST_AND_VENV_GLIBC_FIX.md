# R8D — VM-Bootverfahren + venv/glibc Boot-Hang Root Cause & Fix

**Datum:** 2026-06-14
**Version:** 1.7.18.1 → **1.7.18.2** (Bugfix)
**Symptom (MSI, nach R8C-Fix):** GRUB textuell, erster Eintrag startet automatisch, kurze rote Meldung, dann blinkender Cursor; auch „mit Netzwerk" identisch. Kein Menü.

## 1. VM-Testverfahren (neu)

`scripts/rescue-live/run-rescue-standard-iso-vm-test.sh` bootet die **Standard-ISO** headless unter QEMU/KVM und zeichnet ein vollständiges Serial-Log auf — reproduziert den MSI-Hang lokal, ohne Hardware.

- `--mode direct` (Standard): QEMU Direct-Kernel-Boot (`-kernel`/`-initrd`), überschreibbarer Cmdline, ISO als Medium für die squashfs. Schnell, kein Rebuild nötig, voller Log.
- `--mode uefi`: voller OVMF/UEFI-Boot der ISO (Firmware-Pfad wie MSI).
- `--variant default|network|msi-compat|diagnose`
- Voraussetzungen vorhanden: QEMU 8.2.2, KVM, OVMF.
- Evidence: `docs/evidence/runtime-results/rescue/vm_standard_boot_<stamp>/` (+ `_latest`), mit `serial.log`, `summary.json`, `kernel_cmdline.txt`.

Beispiel:
```bash
bash scripts/rescue-live/run-rescue-standard-iso-vm-test.sh --mode direct --variant default --timeout 150
# voller Journal-Inhalt auf Serial:
bash scripts/rescue-live/run-rescue-standard-iso-vm-test.sh --append "systemd.journald.forward_to_console=1"
```

## 2. Root Cause (im VM-Log eindeutig belegt)

Boot-Basis ist gesund (Kernel → initramfs → Live-Medium → systemd → multi-user/graphical, Login-Prompt auf Serial). **Drei Services scheitern**, alle mit derselben Ursache:

```
/opt/setuphelfer-rescue/backend/venv/bin/python3: /lib/x86_64-linux-gnu/libc.so.6:
version `GLIBC_2.38' not found (required by .../venv/bin/python3)
```

| Service | Folge |
|---|---|
| `setuphelfer-rescue-media-check` | exit 16 |
| `setuphelfer-rescue-start-assistant` | exit 1 → `tty1` leer (Conflicts=getty@tty1) → **blinkender Cursor auf MSI** |
| `setuphelfer-backend` | Restart-Endlosschleife |

**Mechanismus:**
- Build-Host = Ubuntu 24.04 (**python3.12 / glibc 2.39**); Live-Basis = Debian Bookworm (**python3.11 / glibc 2.36**).
- `backend/venv/bin/python3` ist Symlink → `/usr/bin/python3.12`.
- `create-temp-runtime-bundle.sh` schloss nur `.venv/` aus, **nicht `venv/`**.
- `prepare`-rsync nutzte **`-rltL`**: `-L` dereferenziert den Symlink und backt die **Host-python3.12-Binary** + 24 `cpython-312`-Extensions in die squashfs.
- Auf Bookworm (glibc 2.36) nicht lauffähig → alle venv-Services scheitern.

Der „rote Flacker" = genau diese FAILED-Zeilen. Kein Treiberproblem.

## 3. Fix (Option A — venv im chroot bauen)

1. **Host-venv nicht mehr ausliefern:** `venv/` aus `create-temp-runtime-bundle.sh` und aus dem `prepare`-rsync ausgeschlossen.
2. **venv im chroot bauen:** Hook `012-build-rescue-backend-venv.chroot` erstellt während `lb build` `python3 -m venv` + `pip install --prefer-binary -r backend/requirements.txt` (manylinux-Wheels, python3.11/glibc2.36-kompatibel) und prüft Imports (fastapi/uvicorn/pydantic/cryptography/PIL/yaml/psutil) → Build bricht früh ab statt am Boot zu hängen.
3. **Regressionssperre** in `validate-rescue-iso-squashfs.sh`: venv-Python-Version muss zur Live-Basis passen (kein `python3.12`-Host-Leak), fastapi-site-package muss vorhanden sein.

### 3b. Zweite Ursache (R8D-2): Hook lief gar nicht — falsche Hook-Konvention

Nach dem R8D-Rebuild fehlte der venv **komplett** im squashfs (Validator: `INTEGRATION_GAP: bundled backend venv missing`, exit 11). Im Build-Log keinerlei `pip`-Aktivität.

**Ursache:** `prepare` schrieb den venv-Hook nach `config/hooks/normal/013-…hook.chroot`. Diese Basis nutzt aber **live-build 3.0~a57**, das **ausschließlich** `config/hooks/*.chroot` ausführt — **nicht** `config/hooks/normal/*.hook.chroot` (so wie es erst neuere live-build-Versionen tun). Der Hook unter `normal/` wurde nie ausgeführt; nur die flachen Hooks `005-setuphelfer-live-user.chroot` und `010-enable-setuphelfer-services.chroot` liefen (deren `OK:`-Echos im Log). Die Services selbst sind unabhängig davon via `includes.chroot/.../multi-user.target.wants`-Symlinks enabled — nur der **venv-Build** (eine Aktion, kein Symlink) braucht zwingend einen *ausgeführten* Hook.

**Fix:** venv-Hook auf flachen Pfad `config/hooks/012-build-rescue-backend-venv.chroot` umgestellt (in `prepare` und im Build-Tree); toter `normal/013` entfernt. Tree-Validator erzwingt jetzt den flachen Hook und **verbietet** einen venv-Hook unter `normal/`.

### 3c. Dritte Ursache (R8E): f-string-Backslash → SyntaxError auf Python 3.11

Nach dem venv-Fix bootete das System bis `graphical.target`/Login, aber der **VM-Test mit
`systemd.journald.forward_to_console=1`** zeigte: `setuphelfer-backend.service` crasht im
Restart-Loop mit
`SyntaxError: f-string expression part cannot include a backslash` in `backend/app.py:10566`.

**Ursache:** Ein f-string mit Backslash im Ausdrucksteil (`f"{shlex.quote('… > \"$tmp\" …')}"`)
ist erst ab **Python 3.12** erlaubt (PEP 701). Der Dev-Host (3.12) akzeptiert ihn, die Live-Basis
(**3.11**) lehnt ihn beim Import ab. media-check/start-assistant importieren denselben Code.

**Fix:** Ausdruck aus dem f-string herausgezogen (kein Backslash mehr nötig). Verifiziert mit dem
**chroot-`python3.11`** (`python3.11 -m compileall backend/` → rc 0, keine weiteren Stellen).

> Lehre: Backend-Syntax IMMER gegen die Live-Python-Version prüfen, nicht nur gegen den Dev-Host.
> Schnellcheck ohne Rebuild: `build/.../chroot/usr/bin/python3.11 -m compileall -q backend/`.

Verbleibende VM-Fehlschläge sind **headless-Artefakte**, keine Boot-Blocker: `start-assistant`
(exit 1) scheitert an `whiptail` ohne interaktives tty1; `media-check` (exit 16,
`live_media_runtime_stable=False`) prüft im direct-kernel-boot eine ISO statt eines FAT32-ESP-USB.
Beide sind nicht-fatal — `graphical.target` und Login werden erreicht.

## 4. Headless-Logging auf den Stick (neu)

Damit ein Boot, der die UI nicht erreicht, trotzdem diagnostizierbar bleibt:
- Script `setuphelfer-rescue-boot-logs` (System-`python3`, **nicht** venv → robust) + Unit `setuphelfer-rescue-boot-logs.service` (oneshot, `After/WantedBy=multi-user.target`).
- Schreibt `journalctl -b`, `dmesg`, `systemctl --failed`, `systemd-analyze blame/critical-chain` und `systemctl status` der Kern-Services nach `setuphelfer/logs/boot/<stamp>/` auf den Stick (FAT32 ESP) via `resolve_spool_base()`, mit `/run`-Fallback und Secret-Redaction. Stabiler Schnellzugriff: `setuphelfer/logs/boot/latest-failed.txt`.

## 5. Verifikation (ohne sudo)

- `bash -n` aller geänderten Scripts: OK.
- VM-Test reproduziert Hang und liefert exakte Fehlerzeile (GLIBC_2.38).
- Dumper-Python lokal simuliert: schreibt + redigiert Secrets (`password=… → [REDACTED]`).
- Version-Konsistenz: `scope=workspace ok=True` (1.7.18.4 / semver 1.7.18).

## 6. Operator-Anweisung (Phase 0 / sudo)

**WICHTIG:** `run-controlled-iso-build-with-logging.sh` ruft **kein** prepare auf, und `clean`
entfernt `config/includes.chroot` **nicht**. Der `prepare`-Schritt (kein sudo) ist daher Pflicht —
er schreibt den flachen `012`-venv-Hook und entfernt einen evtl. stale Host-venv. Der flache Hook
(`config/hooks/012-build-rescue-backend-venv.chroot`) ist bereits im Build-Tree; der Lauf unten ist
trotzdem die saubere, reproduzierbare Sequenz.

```bash
cd /home/volker/piinstaller
# 1) Bundle ohne Host-venv (kein sudo)
scripts/rescue-live/create-temp-runtime-bundle.sh
# 2) PREPARE — schreibt flachen 012-venv-Hook, entfernt venv aus includes.chroot (kein sudo) — NICHT VERGESSEN
SETUPHELFER_RESCUE_BUILD_PROFILE=standard scripts/rescue-live/prepare-controlled-live-build-tree.sh
# 3) Clean + Build (sudo)
sudo scripts/rescue-live/clean-controlled-live-build-tree.sh --operator-confirm-clean
sudo SETUPHELFER_RESCUE_BUILD_PROFILE=standard \
  scripts/rescue-live/run-controlled-iso-build-with-logging.sh --operator-confirm-build
# 4) Validieren
bash scripts/rescue-live/validate-rescue-iso-squashfs.sh \
  build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso
```

Der Build-Tree-Validator (läuft automatisch im Build) erzwingt jetzt: flacher `012`-venv-Hook vorhanden,
**kein** venv-Hook unter `normal/` (würde nicht ausgeführt), **und** kein venv im `includes.chroot` —
ein vergessener prepare-Schritt oder eine falsche Hook-Platzierung bricht den Build sofort ab.

**Vor dem USB-Write zuerst im VM bestätigen** (kein sudo, keine Hardware nötig):
```bash
bash scripts/rescue-live/run-rescue-standard-iso-vm-test.sh --mode direct --variant default --timeout 150
# Erwartung: keine GLIBC_2.38-Fehler, media-check/backend OK, kein FAILED start-assistant.
```
Erst danach USB schreiben (R8B-Ablauf) und MSI-Boot. Headless-Logs danach unter `SETUPHELFER:/setuphelfer/logs/boot/`.
