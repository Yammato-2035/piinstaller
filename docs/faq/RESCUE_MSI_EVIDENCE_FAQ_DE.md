# FAQ — MSI Evidence & Rettungsstick 1.10.0.x (DE)

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

## Warum überlagert die Konsole kurz vor dem Textmenü?

Boot-Status (`boot-progress`) schrieb auf tty1 **bevor** der Console-Shield aktiv war.

Ab **1.10.0.4:** Early Shield in `boot-progress` und `entrypoint`; weniger tty-Rewrites im MSI/Safe-UI-Modus.

**Update 1.10.0.16 (PI-RS-MSI-GUI-003):** Unter MSI-Compat keine Phase `x11_starting` mehr; stattdessen `tui_mode_selected`. Console-Ownership verhindert Boot-Progress-Writes nach TUI-Übergabe. **Physischer Retest ausstehend** — siehe [PI_RS_MSI_GUI_003_FAQ.de.md](PI_RS_MSI_GUI_003_FAQ.de.md).

---

## Warum zeigt boot-timeline.jsonl noch „Grafische Oberfläche wird gestartet“?

Das war der **bestätigte Fehler** in PI-RS-MSI-RETEST-002 (Payload 1.10.0.15): Boot-Progress und GUI-Sperre waren nicht gekoppelt.

Ab Payload **1.10.0.16** (Software-Fix, Stick-Update noch offen): unter `setuphelfer_msi_compat=1` **kein** `x11_starting`, Meldung „MSI-Kompatibilitätsmodus: Textoberfläche wird verwendet.“

**Update 2026-07-13:** Physisch bestätigt mit Payload **1.10.0.20** und PI-RS-MSI-AUTO-EVIDENCE-001 — siehe [PI_RS_MSI_AUTO_EVIDENCE_001_FAQ.de.md](PI_RS_MSI_AUTO_EVIDENCE_001_FAQ.de.md).

---

## Warum sind gui-start.log-Einträge von gestern noch sichtbar?

Ohne Session-Bindung wurden alte GUI-Logs beim Evidence-Mirror als aktuell behandelt (Session `20260712_015909` in neuer Boot-Evidence).

Ab **1.10.0.16:** jede Boot-Session erhält `session_id`/`boot_id`; stale Dateien werden nicht mehr als aktueller Nachweis gespiegelt.

---

## Blockiert LAN noch das WLAN?

**Nein.** Status: `fixed_legacy`. WLAN und LAN können parallel genutzt werden. WLAN-Connect ist nicht mehr der primäre Blocker.

---

## Ist fehlende Telemetrie ein WLAN-Fehler?

**Nein.** Der produktive IONOS-Telemetrie-Server ist noch **nicht** bereitgestellt (`expected_unavailable`).

WLAN kann verbunden sein und Internet ok — Telemetrie trotzdem `review_required`.

Testpfad: **LAN/WLAN → Internet → DNS → HTTPS → Telemetrie**.

---

## Wo liegt die Evidence auf dem Stick?

```
SETUP_LOGS/setuphelfer/evidence/msi-rs011b/
SETUP_LOGS/setuphelfer/evidence/boot/
SETUP_LOGS/setuphelfer/diagnostics/latest/
```

Import:

```bash
./scripts/rescue/import-msi-rs011b-evidence.sh /media/$USER/SETUP_LOGS
```

(Direkter `msi-rs011b`-Pfad ebenfalls möglich.)

---

## Ist RS-011B / RS-011C freigegeben?

| Item | Status |
|------|--------|
| RS-011B Rebewertung | **blockiert** bis vollständige MSI-Evidence |
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

Erwartet auf aktuellem Lab-Stick: Payload **1.10.0.20**.

---

## Gibt es vollautomatischen MSI-Lab-Boot?

**Ja (ab 1.10.0.20, passed).** GRUB-Lab-Modus → Late-Evidence → Collect → Auto-Shutdown (~2,5 min). Details: [PI_RS_MSI_AUTO_EVIDENCE_001_FAQ.de.md](PI_RS_MSI_AUTO_EVIDENCE_001_FAQ.de.md).

---

## Siehe auch

- [PI_RS_MSI_AUTO_EVIDENCE_001_FAQ.de.md](PI_RS_MSI_AUTO_EVIDENCE_001_FAQ.de.md)
- [MSI_TUI_CONSOLE_ISOLATION_KB_DE.md](../knowledge-base/rescue/MSI_TUI_CONSOLE_ISOLATION_KB_DE.md)
- [RESCUE_STICK_FAQ_DE.md](RESCUE_STICK_FAQ_DE.md)
- [RESCUE_CONNECTIVITY_TELEMETRY_KB.md](../knowledge-base/rescue/RESCUE_CONNECTIVITY_TELEMETRY_KB.md)
- [RS_011D_EVIDENCE_CONTRACT.md](../architecture/RS_011D_EVIDENCE_CONTRACT.md)
