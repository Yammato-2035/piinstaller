# RS-001 React Rescue Hardware Retest — Ergebnis

**Datum:** 2026-06-09  
**HEAD (Stick-Payload):** `27b0829` / SquashFS `a54aae1d…`  
**HEAD (Fix):** `17ac7f7` → `1.7.10.1`  
**Version auf Stick:** `1.7.10.0`  
**RS-001 Status:** **yellow**  
**Lauf-Status:** **Hardware-Retest durchgeführt — grafisches Menü fehlt**

---

## Phase 0 — Payload-Gate (bestanden)

| Prüfung | Wert |
|---------|------|
| `payload_update_status` | **success** |
| `verify_status` | **success** |
| `stick_squashfs_hash_ok` | **true** |
| `expected_squashfs_sha256` | `a54aae1d902523cf08b37105b1f6001e048d610b57210520ea2e1a649b3fe820` |

---

## Phase 1 — Operator-Hardwaretest (durchgeführt)

| Feld | Wert |
|------|------|
| UEFI | **reached** |
| GRUB | **reached** |
| Live system | **reached** |
| React Rescue Shell launcher visible | **yes** |
| React UI URL visible | `http://127.0.0.1:8765/rescue.html` |
| Graphical React menu visible | **no** |
| Old whiptail blocker | **no** |
| Live-Medium warning | not visible in photo |
| Network onboarding failed | **yes** |
| systemd-networkd-wait-online failed | **yes** |
| telemetry-push failed | **yes** |
| Photo | `IMG_31CF232F-F82B-4EF4-AAF7-4176D1539492.jpeg` |

Konsolen-Auszug (Operator):

```text
Setuphelfer - React Rescue Shell
UI: http://127.0.0.1:8765/rescue.html
```

---

## Phase 2 — Klassifikation

```text
RS-001: yellow
Reason: React shell reached but no browser/kiosk menu; optional network/telemetry services still fail during boot
```

**Nicht grün** — nutzbares grafisches Hauptmenü nicht sichtbar.

---

## Phase 3 — Workspace-Fix (1.7.10.1, nicht auf Stick)

| Änderung | Ziel |
|----------|------|
| Launcher Browser-Erkennung + Fallback-TUI | Kein Fake-Success bei URL-only |
| `rescue-ui-status.json` Evidence | `review_required` bei fehlendem Kiosk |
| Network onboarding Boot-Skip | Nur nach Nutzerwahl „Netzwerk verbinden“ |
| Telemetry default skipped | Kein Hard-Fail ohne Opt-in |
| `systemd-networkd-wait-online` Drop-in | Nicht im kritischen Bootpfad |

**Retest ready:** nein (SquashFS-Rebuild + Payload-Update erforderlich)

---

## Next

1. Controlled build / repack SquashFS mit `1.7.10.1`
2. Payload-Update + Verify Hash
3. Hardware-Retest: **nutzbares Setuphelfer-Menü** (Kiosk oder Fallback-TUI), keine rohen systemd-Failed-Units
