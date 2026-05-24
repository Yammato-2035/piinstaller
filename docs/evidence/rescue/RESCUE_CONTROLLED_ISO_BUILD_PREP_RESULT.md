# Rescue Controlled ISO Build Prep — Result

**Datum:** 2026-05-24
**Git HEAD:** `0d211fc`
**Session:** Controlled Live Build Tree Preparation

## Gesamtstatus

**ISO_BUILD_PREP_REVIEW_REQUIRED**

| Flag | Wert |
|------|------|
| **real_iso_build_allowed** | **false** |
| **usb_write_allowed** | **false** |
| **next_gate** | Operator: `live-build`/`xorriso` installieren → Toolcheck → ISO-Build-Freigabe |

**Kein fake green:** Build-Tree und Validatoren grün; ISO-Build-Tools auf Host fehlen; Live-OS-Test weiterhin offen.

---

## Toolcheck

| Tool | Status |
|------|--------|
| lb | **fehlt** |
| xorriso | **fehlt** |
| grub-mkrescue | vorhanden |
| mksquashfs | vorhanden |
| sha256sum, tar, rsync | vorhanden |

Details: `RESCUE_CONTROLLED_LIVE_BUILD_TOOL_CHECK.md`
**blocked_build_tools_missing** für `lb build` — Prep trotzdem abgeschlossen.

---

## Temp-Bundle-Validator

| Feld | Wert |
|------|------|
| Pfad | `build/rescue/temp-runtime/setuphelfer-rescue-runtime/` |
| **files_count** | 2775 |
| **source_head** | `0d211fc` |
| **MANIFEST sha256** | `957191d080eed85e9dc082e673a6632837a6cca5305fafd20cf66f3424e5d257` |
| **Validator Exit** | **0** |
| CDN | pass |
| Secrets / .env / forbidden | pass |

---

## Build-Tree-Validator

| Feld | Wert |
|------|------|
| Pfad | `build/rescue/live-build/setuphelfer-rescue-live/` |
| **Validator Exit** | **0** |
| auto/build | blockiert (Exit 20) |
| ISO/IMG/squashfs/initrd | keine |
| Forbidden tokens (Tree-Scripts) | pass |
| Runtime im includes.chroot | `/opt/setuphelfer-rescue` |

---

## Paketliste

- Minimal konservativ — siehe `RESCUE_LIVE_PACKAGE_LIST_DECISION.md`
- **parted**, **network-manager**, **nginx** bewusst ausgeschlossen

---

## systemd-networkd

- `20-wired.network` — `en*`, DHCP
- `25-ethernet-alt.network` — `eth*`, DHCP
- WLAN: optional_later, nicht konfiguriert

---

## local-only Services

- `setuphelfer-backend.service` — `SETUPHELFER_DISABLE_WRITES=1`, local-only backend script
- `setuphelfer.service` — local-only UI script
- Hook `010-enable-setuphelfer-services.hook.chroot` — enable networkd + services only

---

## Hook-Sicherheit

- Kein apt, mount, dd, mkfs, parted, restore, externe curl
- Nur `systemctl enable` für networkd + Setuphelfer

---

## Build-Artefakte

| Artefakt | Vorhanden |
|----------|-----------|
| `.iso` | **nein** |
| `.img` / `.qcow2` | **nein** |
| squashfs / initrd / vmlinuz | **nein** |

`find` über `build/rescue/live-build` + `build/rescue/temp-runtime`: **keine Treffer**

---

## Runbooks

| Dokument | Status |
|----------|--------|
| `RESCUE_CONTROLLED_ISO_BUILD_RUNBOOK.md` | erstellt |
| `RESCUE_USB_WRITE_GATE_RUNBOOK.md` | erstellt |

---

## Skripte (versioniert)

| Script | Zweck |
|--------|-------|
| `prepare-controlled-live-build-tree.sh` | Tree + Bundle-Integration |
| `validate-controlled-live-build-tree.sh` | Read-only Validierung |

---

## Status-Matrix-Entscheidung

| Bereich | Status |
|-------|--------|
| Controlled ISO Build Prep | **ISO_BUILD_PREP_REVIEW_REQUIRED** |
| Real ISO Build | **blocked** |
| USB Write | **blocked** |
| Live-OS Network Validation | **review_required** (unverändert) |

---

## Nächster Schritt (Operator)

1. `live-build` + `xorriso` auf Build-Host installieren
2. Toolcheck wiederholen → bei grün: **ISO_BUILD_PREP_READY** möglich
3. Schriftliche Freigabe + `RESCUE_CONTROLLED_ISO_BUILD_RUNBOOK.md`
4. `lb config` + `lb build` (manuell, nicht `auto/build`)
5. USB nur via `RESCUE_USB_WRITE_GATE_RUNBOOK.md`
