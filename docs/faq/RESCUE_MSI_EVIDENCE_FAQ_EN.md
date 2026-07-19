> **Phase-1 Übersetzungsmarathon** — English (automatisch aus `docs/faq/RESCUE_MSI_EVIDENCE_FAQ_DE.md`). Bitte bei Release manuell gegenlesen.

# FAQ — MSI Evidence & Rescue stick 1.10.0.x (DE)

Stand: **2026-07-13**

Ausführlich: [MSI_RS011_OPERATOR_KB.md](../knowledge-base/rescue/MSI_RS011_OPERATOR_KB.md)

---

## Warum schlägt der MSI Evidence Collector mit Exit 1 fehl?

**Häufigste Ursache (1.10.0.4):** Rekursion im Wrapper — nicht Versions-Mismatch.

1. Menü oder `RUN-MSI-EVIDENCE` startet `setuphelfer-rescue-msi-rs011b-collect`
2. Dieser ruft `setuphelfer_rescue_run_msi_rs011b_collect()` auf
3. Die Funktion startete erneut denselben Wrapper → `MSI collect recursion blocked` → **Exit 1**

**Folge:** Keine `operator-steps.jsonl`, keine `api-version.json`.

**Workaround auf dem MSI:**

```bash
bash /run/setuphelfer/esp-rw/RUN-MSI-EVIDENCE
```

(Der Launcher auf der SETUP_LOGS-Partition ruft direkt `collect-msi-rs011b-evidence.sh` auf.)

**Dauerhaft:** Repack mit Fix in `setuphelfer-rescue-common.sh` (geplant 1.10.0.5).

---

## Was bedeutet Exit 17 beim Collector?

**Versions-Mismatch:** API liefert z. B. `1.10.0.4`, erwartet wurde eine andere Version.

- Prüfen: `collector-version-check.json` auf dem Stick
- Notfall (nur dokumentiert): `RS011B_SKIP_VERSION_CHECK=1`

Exit **17** ist **nicht** dasselbe wie Exit **1**.

---

## Was bedeutet Exit 3?

Backend unter `http://127.0.0.1:8000` nicht erreichbar.

```bash
systemctl status setuphelfer-backend.service
journalctl -u setuphelfer-backend.service -n 40 --no-pager
```

Collector braucht für Phase 1 mindestens `/api/version` (HTTP 200).

---

## Warum fehlen msi-killer-e2500-detection.json und msi-aer-summary.json?

Der Collector wurde wegen Exit 1 **vor** der RS-011D-Ergänzung abgebrochen, oder das Backend war ohne LAN nicht vollständig.

Nach erfolgreichem Collect mit LAN sollten die Dateien unter  
`SETUP_LOGS/setuphelfer/evidence/msi-rs011b/` liegen.

---

## Ist Disk Discovery auf dem MSI noch kaputt?

**Nein (ab 1.10.0.4).** Früher: `TypeError` weil `lsblk` Größen als `"59G"` lieferte.

Fix: `lsblk -b` + Parser. Auf dem Stick: `disk-discovery.json` mit `"status": "ok"`.

---

## Why does the console briefly overlay the text menu?

Boot status (`boot-progress`) wrote to tty1 **before** the console shield was active.

From **1.10.0.4:** early shield in `boot-progress` and entrypoint; fewer tty rewrites in MSI/safe-UI mode.

**From 1.10.0.16 (PI-RS-MSI-GUI-003):** under MSI compat no `x11_starting` phase; `tui_mode_selected` instead. Console ownership blocks boot-progress writes after TUI handoff. **Physical retest pending** — see [PI_RS_MSI_GUI_003_FAQ.en.md](PI_RS_MSI_GUI_003_FAQ.en.md).

---

## Why does boot-timeline.jsonl still show “Starting graphical interface”?

That was the **confirmed failure** in PI-RS-MSI-RETEST-002 (payload 1.10.0.15): boot progress was not coupled to GUI block.

From payload **1.10.0.16** (software fix, USB update still pending): under `setuphelfer_msi_compat=1` **no** `x11_starting`; message “MSI compatibility mode: using text interface.”

---

## Why are gui-start.log entries from yesterday still visible?

Without session binding, old GUI logs were mirrored as current evidence (session `20260712_015909` in a new boot).

From **1.10.0.16:** each boot gets `session_id`/`boot_id`; stale files are no longer mirrored as current proof.

---

## blocked LAN noch das WLAN?

**Nein.** Status: `fixed_legacy`. WLAN und LAN können parallel genutzt werden. WLAN-Connect ist nicht mehr der primäre Blocker.

---

## Ist fehlende Telemetrie ein WLAN-Error?

**Nein.** Der produktive IONOS-Telemetrie-Server ist noch **nicht** bereitgestellt (`expected_unavailable`).

WLAN kann verbunden sein und internalet ok — Telemetrie trotzdem `review_required`.

Testpfad: **LAN/WLAN → internalet → DNS → HTTPS → Telemetrie**.

---

## Wo liegt die Evidence auf dem Stick?

```
SETUP_LOGS/setuphelfer/evidence/msi-rs011b/
SETUP_LOGS/setuphelfer/evidence/boot/
SETUP_LOGS/setuphelfer/diagnostics/latest/
```

Import:

```bash
./scripts/rescue/import-msi-rs011b-evidence.sh /media/.../SETUP_LOGS/setuphelfer/evidence/msi-rs011b
```

---

## Ist RS-011B / RS-011C freigegeben?

| Item | Status |
|------|--------|
| RS-011B Rebewertung | **blocked** bis vollständige MSI-Evidence |
| RS-011C Test-Backup | **nicht freigegeben** |
| Backup/Restore auf MSI | in diesem Strang **nicht ausgeführt** |

---

## Wie prüfe ich Stick-Version und Metadaten?

ESP-Partition (read-only mount):

```bash
sudo mount -o ro /dev/sda1 /mnt
cat /mnt/setuphelfer/rescue/version.json
sudo umount /mnt
```

Expected on current lab stick: payload **1.10.0.20**. Unattended lab boot: [PI_RS_MSI_AUTO_EVIDENCE_001_FAQ.en.md](PI_RS_MSI_AUTO_EVIDENCE_001_FAQ.en.md).

---

## See also

- [PI_RS_MSI_AUTO_EVIDENCE_001_FAQ.en.md](PI_RS_MSI_AUTO_EVIDENCE_001_FAQ.en.md)

- [PI_RS_MSI_GUI_003_FAQ.en.md](PI_RS_MSI_GUI_003_FAQ.en.md)
- [MSI_TUI_CONSOLE_ISOLATION_KB_EN.md](../knowledge-base/rescue/MSI_TUI_CONSOLE_ISOLATION_KB_EN.md)
- [RESCUE_STICK_FAQ_DE.md](RESCUE_STICK_FAQ_DE.md)
- [RESCUE_CONNECTIVITY_TELEMETRY_KB.md](../knowledge-base/rescue/RESCUE_CONNECTIVITY_TELEMETRY_KB.md)
- [RS_011D_EVIDENCE_CONTRACT.md](../architecture/RS_011D_EVIDENCE_CONTRACT.md)
