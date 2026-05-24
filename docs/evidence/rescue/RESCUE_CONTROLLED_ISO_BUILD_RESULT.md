# Rescue Controlled ISO Build — Result

**Datum:** 2026-05-24
**Git HEAD:** `e7e2e07`
**Gesamtstatus:** **ISO_BUILD_FAILED**

---

## Pre-Build (Phase 4)

| Feld | Wert |
|------|------|
| Runtime-Gate | Exit **0** |
| Toolcheck | **ok** |
| Temp-Bundle Validator | Exit **0** |
| Temp-Bundle files_count | 2775 |
| Temp-Bundle source_head | `e7e2e07` |
| Temp-Bundle MANIFEST sha256 | `b4b72807a5ccafe544094641748ef877fd23f028103ea787473032193f6c59f0` |
| Build-Tree Validator | Exit **0** |
| Operator-Freigabe ISO-Build | **true** |
| usb_write_allowed | **false** |
| dd_allowed | **false** |
| real_iso_build_allowed_for_this_task | **true** |
| real_usb_write_allowed | **false** |

---

## Build-Versuche (Phase 5)

| # | Befehl | Exit | Ergebnis |
|---|--------|------|----------|
| 1 | `./auto/config` dann `lb build` | 126 | **Fehler:** `auto/config` ruft `lb config` ohne `noauto` → rekursive Ausführung → `Argument list too long` |
| 2 | `lb config noauto …` dann `lb build` | 0* | **Kein ISO:** `lb build` führt blockiertes `auto/build` aus (Exit 20 Gate-Message) |
| 3 | `lb build noauto` | — | **Fehler:** `E: need root privileges` |
| 4 | `sudo lb build noauto` | — | **Fehler:** sudo Passwort erforderlich (Agent ohne TTY) |
| 5 | `fakeroot lb build noauto` | — | **Fehler:** debootstrap extrahiert Pakete, dann `chroot … Operation not permitted` |

\*Pipeline-Exit 0 trotz Gate — kein echter Build-Lauf.

### Letzte Logzeilen (Versuch 5, fakeroot)

```
W: Failure trying to run: chroot ".../chroot" /bin/true
chroot: cannot change root directory to '.../chroot': Operation not permitted
```

Debootstrap-Log: Paket-Download/-Extraktion bis Base-System, dann chroot-Block.

**Build-Dauer (Versuch 5):** ~19 s (Abbruch bei chroot)

---

## ISO-Artefakt (Phase 6)

| Feld | Wert |
|------|------|
| ISO-Build ausgeführt | **ja** (mehrere Versuche) |
| ISO-Dateiname | **—** (keine ISO erzeugt) |
| ISO-Größe | **—** |
| ISO-SHA256 | **—** |
| **Build-Status** | **ISO_BUILD_FAILED** |

```bash
find build/rescue/live-build/setuphelfer-rescue-live -maxdepth 3 -name "*.iso"
# (keine Treffer)
```

---

## Safety-Scan (Phase 7, Bundle im Tree)

| Prüfung | Ergebnis |
|---------|----------|
| Google-Fonts-CDN | **pass** — keine Treffer |
| Secret-Pattern | **pass** — nur Code-String in `activation_execute.py` (Key-Erkennung, kein Secret) |
| Unerwartete IMG/QCOW2 | **pass** — keine |
| ISO vorhanden | **fail** — Build nicht abgeschlossen |

---

## USB-Write (Phase 8)

| Feld | Wert |
|------|------|
| usb_write_allowed | **false** |
| dd_executed | **false** |
| mkfs_executed | **false** |
| parted_write_executed | **false** |
| usb_target_device | **null** |

---

## Ursachen / Blocker

1. **`auto/config`:** fehlendes `noauto` → Rekursion bei `./auto/config`
2. **`auto/build`:** absichtlich blockiert; `lb build` ohne `noauto` ruft es auf
3. **Root:** `lb build noauto` benötigt root/sudo für debootstrap/chroot — Agent ohne sudo-Passwort
4. **fakeroot:** reicht nicht für chroot in dieser Umgebung

## Operator-Nächster Schritt

Im interaktiven Terminal (mit sudo):

```bash
cd /home/volker/piinstaller/build/rescue/live-build/setuphelfer-rescue-live
lb config noauto \
  --distribution bookworm \
  --archive-areas "main" \
  --binary-images iso-hybrid \
  --debian-installer false \
  --bootappend-live "boot=live components quiet splash setuphelfer_rescue=1" \
  --iso-volume "SETUPHELFER_RESCUE" \
  --iso-application "Setuphelfer Rescue Live"
sudo lb build noauto
sha256sum live-image-amd64.hybrid.iso
```

Optional vorher: `auto/config` um `noauto` ergänzen (Follow-up-Commit).

---

## Status nach Session

| Bereich | Status |
|---------|--------|
| Controlled ISO Build | **review_required** (Build fehlgeschlagen) |
| Rescue ISO artifact | **blocked** (keine ISO) |
| USB Write | **blocked** |
| Live-Boot-Test | **pending** |
| real_usb_write_allowed | **false** |
