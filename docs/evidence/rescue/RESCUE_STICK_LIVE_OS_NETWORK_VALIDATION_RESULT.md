# Rescue Stick — Live-OS Network Validation Result

**Version:** 1.1 (Live-Medium Execution Attempt)
**Testdatum:** 2026-05-24 (Session 3, ca. 23:00 CEST)
**Git HEAD (Dev-Repo):** `dd0aa59`
**Runtime-Gate vor Test:** Exit 0

## Zusammenfassung

| Feld | Wert |
|------|------|
| **Gesamtstatus** | **review_required** |
| **live_boot_detected** | **false** |
| **live_os_network_test** | **not passed** |
| **real_iso_build_allowed** | **false** |
| **Controlled ISO Prep** | **ISO_PREP_REVIEW_REQUIRED** |

**Kein fake green.** Phasen 3–5 (Live-Boot, Temp-Runtime auf Live-OS, Offline-Test) wurden in der Agent-Session **nicht** ausgeführt — persistenter Ubuntu-Host, kein `/lib/live/mount/medium`.

---

## Phase 1 — Temp-Runtime-Bundle (Dev-Repo)

| Feld | Wert |
|------|------|
| Bundle-Pfad (lokal) | `build/rescue/temp-runtime/setuphelfer-rescue-runtime/` |
| **files_count** | 2777 |
| **MANIFEST sha256** | `f5b02d78825bea9a02cc17b6129f4e3933022205cf9ebdbd64f06887f48f0e04` |
| **Validator Exit** | **0** |
| CDN-Check | keine Google-Fonts in `frontend/dist` |
| Forbidden files | keine ISO/IMG/QCOW2 |
| Secret-Pattern | ok (backend/config scan) |
| **source_head** | `dd0aa59` |

---

## Phase 2 — Copy auf Medium (Operator-Versuch)

| Feld | Wert |
|------|------|
| Zielmedium | USB **INTENSO** (`/media/gabriel/INTENSO`) |
| Zielpfad | `/media/gabriel/INTENSO/setuphelfer-rescue-runtime` |
| Kopiermethode | `cp -a` auf bereits eingebundenes Medium |
| **Ergebnis** | **review_required / teilweise fehlgeschlagen** |
| Ursache | VFAT/exFAT: symbolische Links in `backend/venv/` nicht anlegbar (`Operation not permitted`) |
| MANIFEST vor Kopie | `f5b02d78825bea9a02cc17b6129f4e3933022205cf9ebdbd64f06887f48f0e04` |
| MANIFEST nach Kopie | **nicht verifiziert** (Kopie unvollständig) |
| **copied_to_medium_by_operator** | **false** (vollständig) |

**Operator-Nächster Schritt:** Bundle als `tar` auf ext4-Partition kopieren, oder USB mit ext4, oder Live-System mit Repo-Zugriff — **ohne** dd/mount-Befehle in Repo-Skripten.

---

## Phase 3 — Live-Boot (nicht durchgeführt)

| Feld | Wert |
|------|------|
| **live_boot_detected** | **false** |
| Erkannte Umgebung | `volker-ROG-Strix`, rootfs **ext4** auf NVMe |
| `/lib/live/mount/medium` | **nicht vorhanden** |
| `/proc/cmdline` | `root=UUID=… ro` (persistente Installation) |
| Bootmedium gebootet | **Nein** in dieser Session |

---

## Phase 4 — Temp-Runtime auf Live-OS (nicht durchgeführt)

| Prüfung | Status |
|---------|--------|
| `SETUPHELFER_RESCUE_ROOT` auf Live-Medium | **not_tested** |
| `start-backend-localonly.sh` auf Live | **not_tested** |
| `start-ui-localonly.sh` auf Live | **not_tested** |
| `check-localonly.sh` auf Live | **not_tested** |
| Backend localhost (Live) | **not_tested** |
| UI localhost (Live) | **not_tested** |

**Host-Referenz (kein Live-Nachweis):** Auf Dev-Host laufen `/opt/setuphelfer`-Services weiterhin auf `127.0.0.1:8000/3001` — zählt **nicht** als Live-Medium-Validation.

---

## Phase 5 — Offline / CDN (Live)

| Prüfung | Status |
|---------|--------|
| Offline ohne WAN auf Live | **not_tested** |
| CDN-frei im Bundle | **pass** (Validator) |
| UI ohne Internet (Live) | **not_tested** |

---

## Pass/Fail-Matrix

| Prüffeld | Ergebnis | Evidence | Bewertung |
|----------|----------|----------|-----------|
| Bundle validiert | pass | Validator Exit 0 | ok |
| Copy auf Medium vollständig | fail | venv symlinks auf INTENSO | review_required |
| Echtes Live gebootet | fail | kein live medium path | **Blocker für green** |
| systemd-networkd (Live) | not_tested | — | — |
| DHCP (Live) | not_tested | — | — |
| Backend localhost (Live) | not_tested | — | — |
| UI localhost (Live) | not_tested | — | — |
| LAN-Bind (Live) | not_tested | — | — |
| Offline/CDN (Live) | not_tested | Bundle CDN pass | review_required |
| Auto-Write/Restore/Partition | not_tested | — | — |
| Evidence vollständig | review_required | Dieses Dokument | Session 3 |

---

## Prüfpunkte 1–10 (Live-Kontext)

| # | Punkt | Status |
|---|-------|--------|
| 1 | systemd-networkd aktiv | not_tested |
| 2 | NetworkManager nicht erforderlich | not_tested |
| 3 | DHCP | not_tested |
| 4 | Loopback aktiv | not_tested (Live) |
| 5 | DNS optional | not_tested |
| 6 | Betrieb ohne Internet | not_tested |
| 7 | Backend localhost | not_tested (Live) |
| 8 | UI localhost | not_tested (Live) |
| 9 | Keine CDN-Pflicht | pass (Bundle) |
| 10 | Keine Telemetrie/Cloud | not_tested |

---

## Gesamtstatus: **review_required**

**Begründung:** Bundle erzeugt und validiert; USB-Kopie auf INTENSO wegen venv-Symlinks auf VFAT unvollständig; **kein Live-Boot**, daher keine Live-Network-/localhost-Validation.

## Verbotene Aktionen

Kein ISO-Build, lb build, apt, mount/umount (Repo), dd, mkfs, restore, backup, partition write in dieser Session.

## Nächster Schritt (Operator)

1. Bundle auf **ext4**-fähiges Medium kopieren (tar stream oder ext4-USB) — Runbook `RESCUE_TEMP_RUNTIME_COPY_TO_LIVE_MEDIUM.md`.
2. Debian/Ubuntu-Live von freigegebenem Medium **booten**.
3. Temp-Runtime starten + `check-localonly.sh` + Result-Template-Felder ergänzen.
4. Bei **green**: Controlled ISO Prep → `ISO_PREP_READY` (Real ISO weiterhin separater Prompt).
