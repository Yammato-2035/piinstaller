# Rescue Controlled ISO Build — Result

## Neuester Lauf (2026-06-09, RS-001 SquashFS-Update)

| Feld | Wert |
|------|------|
| Git HEAD | `6f3c783` |
| Version | `1.7.9.3` |
| `build_status` | **blocked** |
| Exit | 30 `blocked_requires_operator_sudo_policy` |
| ISO neu gebaut | **nein** (`no_build_executed: true`) |
| Vorhandenes ISO | `binary.hybrid.iso` (SHA256 unverändert) |
| SquashFS Repack-Fallback | `build/rescue/filesystem.squashfs.repacked-1.7.9.3` |
| Repack SHA256 | `ac95ebc3bdc4693da56d51cda1bb3f5fd36dc68d18b2ff1e8f76aad30a85f00a` |
| `contains_live_medium_fix` | **true** |
| `contains_setuphelfer_rescue_live_medium_check_py` | **true** |
| `no_fake_green` | **true** |
| USB Payload-Update | **nicht ausgeführt** (Agent ohne sudo-TTY) |

Evidence: `docs/evidence/runtime-results/rescue/controlled_iso_build_latest_summary.json`

Operator: Controlled Build im Terminal mit sudo, oder Repack-SquashFS für `update-fat32-esp-live-payload.sh`.

---

**Datum:** 2026-05-25 (STRICT MODE – Controlled Rescue ISO Build + USB Write Gate + First Boot Prep)
**Git HEAD:** `fe36af0`
**Gesamtstatus:** **ISO_BUILD_FAILED** → **Kein ISO erzeugt, USB-Write nicht freigegeben**

## Aktueller Fix-Stand (2026-05-26, Version 1.7.2)

- vorheriger Notification-Basisstand: Commit `3adfc13`
- der historische Build-Fehler `LB_EXIT=127` bleibt als letzter echter Build-Befund bestehen
- neuer Dashboard-/Executor-Stand blockiert den Build jetzt **vorher** mit `blocked_build_tools_missing`, wenn `rsvg` fuer den Bootloader-Splash fehlt
- neuer `next_operator_action.type`: `build_dependency_required`
- neuer Operator-Hinweis vor jedem erneuten Buildversuch:

```bash
sudo apt install librsvg2-bin
```

Wichtig:

- in diesem Fix-Lauf wurde **kein** neuer ISO-Build gestartet
- es wurde **kein** USB-Write gestartet
- der echte Buildstatus bleibt deshalb bis zu einem spaeteren erneuten Build **rot**
- produktiver 1.7.2-Runtime-Smoke:
  - `GET /api/dev-dashboard/rescue-iso/status` -> `status=red`
  - `rsvg_preflight.status=blocked`
  - `rsvg_preflight.error_code=blocked_build_tools_missing`
  - `next_operator_action.type=build_dependency_required`
  - `usb_write.allowed=false`
  - root-owned Altzustand bleibt sichtbar (`needs_sudo_clean=true`)

---

## Neuester Lauf (fe36af0)

### Vorbedingungen

| Feld | Wert |
|------|------|
| Workspace HEAD vor Build | `fe36af0` |
| Runtime-Gate | Exit **0** |
| `workspace_path` | `/home/volker/piinstaller` |
| `runtime_path` | `/opt/setuphelfer` |
| `build_tree_path` | `/home/volker/piinstaller/build/rescue/live-build/setuphelfer-rescue-live` |
| `detect_stale_state` | **ok** (`needs_sudo_clean = false`) |
| `prepare_bundle` | **ok** |
| `validate_bundle` | **ok** |
| `prepare_tree` | **ok** |
| `validate_tree` | **ok** |
| `dpkg_preflight` | **ok** / `pre_chroot_ok` |
| `usb_write.allowed` vor Build | **false** |

### Operator-Build-Befehl

```bash
cd "/home/volker/piinstaller/build/rescue/live-build/setuphelfer-rescue-live"
./auto/config
sudo lb build noauto
```

### Build-Ergebnis

| Feld | Wert |
|------|------|
| `LB_EXIT` | **127** |
| ISO gefunden | **nein** |
| ISO-Pfad | `null` |
| ISO-Groesse | `null` |
| ISO-SHA256 | `null` |
| USB-Write | **nicht ausgefuehrt** |
| USB-Verifikation | **nicht ausgefuehrt** |

### Primaere Fehlerursache

Der Operator-Lauf endete mit folgendem Fehler:

```text
/usr/bin/env: 'rsvg': No such file or directory
LB_EXIT=127
```

Damit wurde kein `.iso` erzeugt; die USB-Phase blieb deshalb gemaess Gate-Regel blockiert.

### Scan / Summary / Safety

- `scan_iso` → **review_required**
  - `iso_found = false`
  - `secret_hits` und `cdn_hits` wurden als heuristische Review-Hits gemeldet
  - kein echter Secret-Wert wurde fuer den USB-Entscheid ausgewertet
- `summarize` → **ok**
  - Dashboard-/Summary-Stand danach: **red**
  - `next_operator_action.type = sudo_clean_required`
- `stale_state.needs_sudo_clean = true` nach dem Root-Build
- keine `.iso`
- keine `.img`
- keine `.qcow2`

### Bewertung

Der kontrollierte Prebuild-Pfad blieb korrekt und reproduzierbar. Der echte Root-Build scheiterte jedoch mit `LB_EXIT=127`, erzeugte keine ISO und hinterliess root-owned Buildreste. Deshalb blieb:

- Controlled ISO Build: **red**
- Rescue ISO Artifact: **red**
- USB Write: **blocked / not attempted**
- Live Boot: **pending**

### Notification-Follow-up

Der Failure wurde zusaetzlich in den neuen Notification-Contract uebernommen:

- Eventtyp: `rescue_iso_build_failed`
- Titel: `Rescue ISO Build fehlgeschlagen`
- technische Kerndaten:
  - `LB_EXIT=127`
  - `primary_error=/usr/bin/env: 'rsvg': No such file or directory`
  - `iso_found=false`
  - `usb_write_started=false`
  - `next_required_action=fix_missing_rsvg_or_remove_rsvg_dependency`

Wichtig:

- lokal wurde die Event-Persistenz erfolgreich verifiziert
- die produktive Runtime ist inzwischen ebenfalls verifiziert:
  - `GET /api/dev-dashboard/notifications/status` -> `200`
  - `GET /api/dev-dashboard/notifications/events` -> `200`
  - Rescue-Failure-Event wurde unter `/var/lib/setuphelfer/notifications/notification_events.jsonl` persistiert
- der Dashboard-Pfad fuer dieses Failure-Event ist damit produktiv **green**
- der produktive E-Mail-Versand fuer dieses konkrete Failure-Event ist aktuell **failed**, klassifiziert als `notification.email.provider_limit_exceeded`
- sichtbarer, redigierter Fehlertext: `554 5.7.0 outgoing message limit exceeded`
- `next_action = check_smtp_provider_limit_or_wait`
- kein Fake-`sent`, kein automatischer Retry

---

## Echter ISO-Build via Dashboard-Pfad (2026-05-25)

### Vorbedingungen

| Feld | Wert |
|------|------|
| Workspace HEAD vor Build | `887ace6` |
| Runtime-Gate | Exit **0** |
| `workspace_path` | `/home/volker/piinstaller` |
| `runtime_path` | `/opt/setuphelfer` |
| `build_tree_path` | `/home/volker/piinstaller/build/rescue/live-build/setuphelfer-rescue-live` |
| `usb_write.allowed` | **false** |
| `detect_stale_state` | **ok** (`needs_sudo_clean = false`) |
| `prebuild_check` | **ok** (`green`) |
| `prepare_bundle` | **ok** |
| `validate_bundle` | **ok** |
| `prepare_tree` | **ok** |
| `validate_tree` | **ok** |

### Operator-Build-Befehl

```bash
cd "/home/volker/piinstaller/build/rescue/live-build/setuphelfer-rescue-live"
./auto/config
sudo lb build noauto
```

### Build-Ergebnis

| Feld | Wert |
|------|------|
| `LB_EXIT` | **100** |
| ISO gefunden | **nein** |
| ISO-Pfad | `null` |
| ISO-Groesse | `null` |
| ISO-SHA256 | `null` |
| `binary/live/filesystem.squashfs` | vorhanden, **429252608 Bytes** |
| `binary/live/initrd.img` | vorhanden, **35634950 Bytes** |
| Dashboard-Status nach Build | **red** |
| `iso_build.status` | **not_started** |
| `next_operator_action.type` | **sudo_clean_required** |

### Fehlerursache aus dem Build-Log

Der Build lief bis in die Binary-Stufe und scheiterte dann waehrend eines Paket-Upgrades im chroot:

```text
dpkg: warning: 'start-stop-daemon' not found in PATH or not executable
dpkg: error: 1 expected program not found in PATH or not executable
E: Sub-process /usr/bin/dpkg returned an error code (2)
LB_EXIT=100
```

Der abschliessende `find`-Befehl im Operator-Terminal lieferte zusaetzlich:

```text
find: './chroot/root': Keine Berechtigung
```

Das ist ein Nachlauf-Effekt der root-owned chroot-Reste und **nicht** die primaere Build-Ursache.

### Scan / Summary / Safety

- `scan_iso` → **review_required**
  - `iso_found = false`
  - keine ISO-Artefakte gefunden
  - heuristische Review-Hits aus dem Runtime-Bundle wurden gemeldet
- `summarize` → **ok**
  - `controlled_iso_build_latest_summary.json` aktualisiert
- manueller Safety-Scan:
  - **keine** CDN-Treffer in lesbaren Dateien
  - **keine** Secret-Treffer in lesbaren Dateien
  - der Scan war wegen root-owned Verzeichnissen unter `config/includes.chroot/opt/setuphelfer-rescue/` **nicht vollstaendig lesbar**
  - unerwartete Build-Artefakte nach Fehlerlauf:
    - `binary/live/filesystem.squashfs`
    - `binary/live/initrd.img`

### Bewertung

Der kontrollierte Dashboard-Pfad bis zum echten Operator-Build war korrekt und reproduzierbar gruen. Der erste echte ISO-Build selbst ist jedoch **fehlgeschlagen** und darf deshalb nicht gruen gemeldet werden. USB-Write bleibt weiter blockiert.

## Dashboard-/Executor-Runtime-Abnahme (2026-05-25)

### Phase 0 / Gate

| Feld | Wert |
|------|------|
| Workspace HEAD | `f2b13f5` |
| Branch | `main` |
| Runtime-Gate | Exit **0** |
| Services | `setuphelfer-backend=active`, `setuphelfer=active` |
| Runtime Path | `/opt/setuphelfer` |
| Workspace Path | `/home/volker/piinstaller` |
| Helper-Deploy | manuell gestartet, Runtime danach weiter **green** |

### Dashboard-Status vor Build

| Feld | Wert |
|------|------|
| `status` | **green** |
| `path_status` | **ok** |
| `path_mode` | `workspace_build_runtime_opt` |
| `build_tree.validator_status` | **ok** |
| `temp_runtime_bundle.status` | **ok** |
| `build_tree.source_head` | `f2b13f5` |
| `temp_runtime_bundle.source_head` | `f2b13f5` |
| `iso_build.status` | **not_started** |
| `stale_state.needs_sudo_clean` | **false** |
| `next_operator_action.type` | **operator_sudo_required** |
| `usb_write.allowed` | **false** |

### Executor-Schritte

| Step | Ergebnis |
|------|----------|
| `prepare_bundle` | **ok** |
| `validate_bundle` | **ok** |
| `prepare_tree` | **ok** |
| `validate_tree` | **ok** |
| `build_iso_operator_required` | **operator_required** — Kommandos wurden angezeigt, aber **nicht** ausgefuehrt |

### Operator-Befehl aus dem Dashboard

```bash
cd "/home/volker/piinstaller/build/rescue/live-build/setuphelfer-rescue-live"
./auto/config
sudo lb build noauto
```

### Ergebnis der Runtime-Abnahme

| Feld | Wert |
|------|------|
| `LB_EXIT` | **nicht gesetzt** |
| ISO gefunden | **nein** |
| ISO-Pfad | `null` |
| ISO-Groesse | `null` |
| ISO-SHA256 | `null` |
| Dashboard-Status nach PHASE 4 | **green** |
| `next_operator_action.type` nach PHASE 4 | **operator_sudo_required** |
| USB-Write | **blocked** |
| `source_head` Bundle/Tree | `f2b13f5` / `f2b13f5` |

### Aufgeloeste Blocker

- Die produktive Runtime bleibt unter `/opt/setuphelfer`, waehrend Bundle und Build-Tree kontrolliert im Workspace `/home/volker/piinstaller` erzeugt werden.
- `prepare_bundle`, `validate_bundle`, `prepare_tree` und `validate_tree` laufen jetzt ueber die Runtime-API mit Exit **0**.
- `build-tree-manifest.json` und `MANIFEST.json` referenzieren jetzt den aktuellen Workspace-Stand `f2b13f5`.
- Der Dashboard-Operator-Befehl zeigt keinen `/opt`-Build-Pfad mehr, sondern den korrekten Workspace-Build-Root.
- USB-Schreiben, `dd`, `mkfs`, `parted write`, Backup und Restore blieben weiterhin blockiert bzw. ungenutzt.

### Historischer Erstlauf (vor Workspace-Path-Fix)

- Der erste produktive Executor-Lauf war noch auf `/opt`-nahe Build-Artefakte ausgerichtet und blieb deshalb in PHASE 4 blockiert.
- `prepare_bundle` loggte dort `rsync`-Permission-Fehler, danach fehlte `MANIFEST.json`, wodurch `validate_bundle` und `prepare_tree` folgerichtig blockierten.
- Dieser Altbefund ist fuer die Ursachenanalyse relevant, gilt aber nach der erfolgreichen Runtime-Abnahme auf `751e2cf` nicht mehr als aktueller Status.

### Safety

| Feld | Wert |
|------|------|
| USB-Write | **nicht ausgefuehrt** |
| `dd` | **nicht ausgefuehrt** |
| `mkfs` | **nicht ausgefuehrt** |
| `parted write` | **nicht ausgefuehrt** |
| Backup | **nicht ausgefuehrt** |
| Restore | **nicht ausgefuehrt** |
| Verify Deep | **nicht ausgefuehrt** |

---

## Retry-Session — Ursache tar/adduser

### Reproduktion (Operator-Terminal, vor Fix)

```
I: Extracting adduser...
E: Tried to extract package, but tar failed. Exit...
LB_EXIT=1
```

### Root Cause (debootstrap.log)

**Kein Dateisystem-Problem.** Build-Verzeichnis liegt auf **ext4** (`/dev/nvme0n1p2`), ~1,3 TB frei.

**Ursache:** **Verunreinigter chroot** aus vorherigem **fakeroot**-Teilbuild + **lb bootstrap cache restore**:

```
tar: ./usr/sbin/adduser: Cannot open: File exists
tar: ./usr/sbin/addgroup: Cannot create symlink to 'adduser': File exists
tar: Exiting with failure status due to previous errors
```

debootstrap versuchte `adduser` erneut zu extrahieren, obwohl Dateien/Symlinks aus partiellem Bootstrap bereits in `chroot/` lagen (Owner `gabriel:workspace`, nicht root).

### Fix (durchgeführt)

| Maßnahme | Status |
|----------|--------|
| `auto/config` → `lb config noauto` | **fixed** (keine Rekursion mehr) |
| `prepare-controlled-live-build-tree.sh` → `noauto` | **fixed** |
| Harte Reinigung: `rm -rf .build chroot cache binary local` | **done** (User-Owner, ohne sudo) |
| `sudo lb clean --purge` | **nicht aus Agent** (sudo Passwort) |
| Bundle + Tree neu validiert | **Exit 0** |

---

## Pre-Build (Retry)

| Feld | Wert |
|------|------|
| Runtime-Gate | Exit **0** |
| auto/config noauto | **pass** — `./auto/config` Exit 0 |
| auto/build blockiert | **pass** — Exit 20 |
| Temp-Bundle Validator | Exit **0** |
| Temp-Bundle files_count | 2775 |
| Temp-Bundle source_head | `83ec644` |
| Build-Tree Validator | Exit **0** |
| Clean-Build State | **ja** — chroot/cache/binary/local/.build entfernt |
| usb_write_allowed | **false** |
| dd_executed | **false** |

---

## Dateisystem / Rechte (Phase 3)

| Feld | Wert |
|------|------|
| Pfad | `/home/volker/piinstaller/build/rescue/live-build/setuphelfer-rescue-live` |
| Typ | **ext4** (geeignet) |
| Freier Platz | ~1,3 TB (26 % belegt) |
| Mount | `rw,relatime` |
| Build-Dir | `gabriel:workspace`, `drwxrwsr-x` |
| umask | 0002 |

**Nicht** auf exFAT/VFAT/NTFS.

---

## Build-Versuch (Retry, Agent)

| Befehl | Ergebnis |
|--------|----------|
| `./auto/config` | **pass** (Exit 0) |
| `sudo lb build noauto` | **nicht ausgeführt** — Agent ohne sudo-Passwort |

**ISO:** keine — Build muss im Operator-Terminal fortgesetzt werden.

---

## Historische Versuche (Session 1)

| # | Problem |
|---|---------|
| 1 | `auto/config` ohne `noauto` → Rekursion |
| 2 | `lb build` → blockiertes `auto/build` |
| 3–4 | root/sudo ohne TTY |
| 5 | fakeroot → partielle chroot → **tar File exists** bei sudo-Retry |

---

## Safety-Scan (Bundle im Tree)

| Prüfung | Ergebnis |
|---------|----------|
| CDN | **pass** |
| Secrets | **pass** |
| ISO | **nicht vorhanden** |

---

## USB-Write

| Feld | Wert |
|------|------|
| usb_write_allowed | **false** |
| dd_executed | **false** |
| mkfs_executed | **false** |
| parted_write_executed | **false** |
| usb_target_device | **null** |

---

## Operator — Nächster Build (nach Clean-State)

```bash
cd /home/volker/piinstaller/build/rescue/live-build/setuphelfer-rescue-live
./auto/config
sudo lb build noauto 2>&1 | tee /tmp/setuphelfer-lb-build-clean.log
echo "LB_EXIT=${PIPESTATUS[0]}"
find . -maxdepth 3 -name '*.iso' -print
```

Bei erneutem tar-Fehler **zuerst** erneut `sudo lb clean --purge` und `sudo rm -rf .build chroot cache binary local`.

---

## Status

| Bereich | Status |
|---------|--------|
| Controlled ISO Build | **review_required** (Clean + noauto fix; ISO ausstehend) |
| Rescue ISO artifact | **blocked** |
| USB Write | **blocked** |
| Live Boot | **pending** |
| real_usb_write_allowed | **false** |

---

## Dashboard Executor Integration (2026-05-25)

| Bereich | Status |
|---------|--------|
| Development Dashboard Rescue ISO Executor | **implemented** |
| Stale-State-Erkennung | **implemented** |
| Operator-Sudo-Clean-Kommandos | **implemented** |
| Operator-Build-Kommandoanzeige | **implemented** |
| USB-Schreiben | **blocked** |

### Erkannte aktuelle Blocker

- stale root-owned live-build state kann `sudo clean` erforderlich machen
- vorherige Altartefakte `initrd`, `vmlinuz`, `filesystem.squashfs` sind aus dem Build-Tree bereinigt
- `auto/clean` war rekursiv kaputt (`lb clean` -> `auto/clean` -> `lb clean`) und ist jetzt auf direkten Stage-Directory-Clean korrigiert
- `.build/chroot_package-lists.install` kann stale sein
- `skipping chroot_package-lists.install, already done` bleibt ein harter Review-Hinweis
- `tar failed` bei `adduser` / `File exists` aus `debootstrap.log` bleibt sichtbar
- Runtime-Gate ist fuer die aktuelle produktive Runtime inzwischen **grün** (`check-runtime-deploy-gate.sh` Exit `0`)
- Temp-Runtime-Bundle-Validator und Controlled-Build-Tree-Validator laufen auf dem aktuellen Stand **grün**
- der eigentliche ISO-Build blieb im ersten produktiven Runtime-Lauf weiter **nicht ausgefuehrt**, weil PHASE 4 im `/opt`-Executor blockierte

### Nächster Schritt

Der nächste Operator-Schritt läuft jetzt über das Development Dashboard:

1. produktive `/opt`-Runtime auf den aktuellen Rescue-Executor-/Bundle-Stand bringen
2. `Stale-State prüfen`
3. `Prebuild-Check`
4. `prepare_bundle`, `validate_bundle`, `prepare_tree`, `validate_tree` muessen alle gruen sein
5. **erst danach** manueller Operator-Build ausserhalb des Agents

**Kein USB-Write.**

### Build-Tree-Review (2026-05-25)

Zusätzlich verifiziert:

- `setuphelfer.list.chroot` bleibt minimal und lokal-only
- `auto/config` verwendet `lb config noauto`
- `auto/clean` ist nicht rekursiv
- `prepare-controlled-live-build-tree.sh` erzeugt den Tree reproduzierbar ohne Build-Ausführung
- `validate-controlled-live-build-tree.sh` ist read-only und gibt Exit `0`
- keine ISO-/Image-/Kernel-Artefakte im Tree oder Temp-Bundle
