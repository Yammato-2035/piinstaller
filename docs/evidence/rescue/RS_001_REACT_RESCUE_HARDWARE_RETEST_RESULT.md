# RS-001 React Rescue Hardware Retest — Ergebnis

**Datum:** 2026-06-10  
**Commit (Workspace):** `bc75f89`  
**Version:** `1.7.10.1`  
**SquashFS SHA256 (Stick):** `0b303d3ab563f4aeaa354813dcbf46e8fb934a3f23d4705251129f80f2ac51dc`  
**RS-001 Status:** **yellow**  
**Lauf-Status:** **Phase 0 bestanden — Operator-Hardware-Retest ausstehend**

---

## Phase 0 — Payload-Gate (bestanden)

| Prüfung | Wert |
|---------|------|
| `payload_update_status` | **success** |
| `verify_status` | **success** |
| `stick_squashfs_hash_ok` | **true** |
| `staging_artifacts_cleaned` | **true** |
| `expected_squashfs_sha256` | `0b303d3ab563f4aeaa354813dcbf46e8fb934a3f23d4705251129f80f2ac51dc` |
| `ready_for_operator_retest` | **true** |
| Read-only Verify (Agent, 2026-06-10) | **success** — Hash auf `/dev/sdb1` stimmt |

Evidence: `docs/evidence/runtime-results/rescue/fat32_esp_payload_update_20260609_214051`

---

## Phase 1 — Operator-Hardwaretest (1.7.10.1, **nicht ausgeführt**)

| Feld | Wert |
|------|------|
| Hardware | MSI / Referenzhardware (Operator) |
| UEFI USB visible | **pending** |
| GRUB visible | **pending** |
| Kernel starts | **pending** |
| Live system starts | **pending** |
| Old whiptail/OK dialog | **pending** |
| Only URL printed | **pending** |
| Usable menu visible | **pending** |
| Menu mode | **pending** (`kiosk` \| `browser` \| `fallback_tui`) |
| Live-Medium warning | **pending** |
| Network failed before menu | **pending** |
| Telemetry failed before menu | **pending** |
| wait-online failed before menu | **pending** |
| Repair/install/backup/restore started | **no** (Auftrag: nicht starten) |
| Evidence on USB | **no** (`setuphelfer/evidence/boot/` leer / nicht vorhanden) |
| Operator hardware test executed | **no** (1.7.10.1-Payload) |

**Operator-Schritte:** siehe `RS_001_LIVE_MEDIUM_RETEST_HANDOFF.md` Schritt 2.

---

## Vorheriger Retest (superseded — alter SquashFS `a54aae1d…`, 1.7.10.0)

| Feld | Wert |
|------|------|
| UEFI / GRUB / Live | **reached** |
| React Rescue Shell launcher | **yes** |
| Only URL printed | **yes** (`http://127.0.0.1:8765/rescue.html`) |
| Graphical React menu | **no** |
| Network / wait-online / telemetry failed | **yes** (vor Menü) |
| Photo | `IMG_31CF232F-F82B-4EF4-AAF7-4176D1539492.jpeg` |
| RS-001 damals | **yellow** |

Dieser Befund gilt **nicht** für Payload `0b303d3…` — neuer Retest erforderlich.

---

## Phase 5 — Klassifikation

```text
RS-001: yellow
Reason: Payload 1.7.10.1 verified on stick; operator hardware retest not yet executed
```

**Nicht grün** — kein nutzbares Menü auf Hardware mit 1.7.10.1 beobachtet.

---

## SquashFS-Inhalt (verifiziert vor Payload-Update)

| Merkmal | Wert |
|---------|------|
| React Rescue Shell | yes |
| Launcher Fix | yes |
| Fallback TUI | yes |
| Network-Onboarding vor Menü | no |
| Telemetry vor Menü | no |
| wait-online Bootblocker | no |

Quelle: `RS_001_REACT_SHELL_LAUNCHER_SQUASHFS_CONTENT_CHECK.md`

---

## Next

1. Operator: Phase-1-Hardwaretest auf MSI/Referenzhardware (kein Backup/Restore/Repair)
2. Erfolg = Kiosk/Browser-Menü **oder** bedienbare Fallback-TUI — **nicht** nur URL
3. Evidence auf Stick (`setuphelfer/evidence/boot/`) und Repo aktualisieren
4. RS-001 erst **green** setzen, wenn nutzbares Menü dokumentiert ist
