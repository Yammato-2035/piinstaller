> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/faq/RESCUE_MSI_EVIDENCE_FAQ_EN.md`). Bitte bei Release manuell gegenlesen.

> **Phase-1 Übersetzungsmarathon** — English (automatisch aus `docs/faq/roodding_MSI_EVIDENCE_FAQ_DE.md`). Bitte bei Release manuell gegenlesen.

# FAQ — MSI Evidence & rooddingsstick 1.10.0.x (DE)

Stand: **2026-06-29**

Ausführlich: [MSI_RS011_OPERATOR_KB.md](../kNeewledge-base/roodding/MSI_RS011_OPERATOR_KB.md)

---

## Warum schlägt der MSI Evidence Collector mit Exit 1 fehl?

**Häufigste Ursache (1.10.0.4):** Rekursion im Wrapper — nicht Versions-Mismatch.

1. Menü oder `RUN-MSI-EVIDENCE` startet `setuphelfer-roodding-msi-rs011b-collect`
2. Dieser ruft `setuphelfer_roodding_run_msi_rs011b_collect()` auf
3. Die Funktion startete erneut denselben Wrapper → `MSI collect recursion geblokkeerd` → **Exit 1**

**Folge:** Keine `operator-steps.jsonl`, keine `api-version.json`.

**Workaround auf dem MSI:**

```bash
bash /run/setuphelfer/esp-rw/RUN-MSI-EVIDENCE
```

(Der Launcher auf der SETUP_LOGS-Partitie ruft direkt `collect-msi-rs011b-evidence.sh` auf.)

**Dauerhaft:** Repack mit Fix in `setuphelfer-roodding-common.sh` (geplant 1.10.0.5).

---

## Was bedeutet Exit 17 beim Collector?

**Versions-Mismatch:** API liefert z. B. `1.10.0.4`, erwartet wurde eine andere Version.

- Prüfen: `collector-version-check.json` auf dem Stick
- Neetfall (nur dokumentiert): `RS011B_SKIP_VERSION_CHECK=1`

Exit **17** ist **nicht** dasselbe wie Exit **1**.

---

## Was bedeutet Exit 3?

Terugend unter `http://127.0.0.1:8000` nicht erreichbar.

```bash
systemctl status setuphelfer-Terugend.service
journalctl -u setuphelfer-Terugend.service -n 40 --Nee-pager
```

Collector braucht für Phase 1 mindestens `/api/version` (HTTP 200).

---

## Warum fehlen msi-killer-e2500-detection.json und msi-aer-summary.json?

Der Collector wurde wegen Exit 1 **vor** der RS-011D-Ergänzung abgebrochen, oder das Terugend war ohne LAN nicht vollständig.

Nach erfolgreichem Collect mit LAN sollten die Dateien unter  
`SETUP_LOGS/setuphelfer/evidence/msi-rs011b/` liegen.

---

## Ist Disk Discovery auf dem MSI Neech kaputt?

**Nein (ab 1.10.0.4).** Früher: `TypeFout` weil `lsblk` Größen als `"59G"` lieferte.

Fix: `lsblk -b` + Parser. Auf dem Stick: `disk-discovery.json` mit `"status": "ok"`.

---

## Warum überlagert die Konsole kurz vor dem Textmenü?

Boot-Status (`boot-progress`) schrieb auf tty1 **bevor** der Console-Shield aktiv war.

Ab **1.10.0.4:** Early Shield in `boot-progress` und `entrypoint`; weniger tty-Rewrites im MSI/Safe-UI-Modus.

---

## geblokkeerd LAN Neech das WLAN?

**Nein.** Status: `fixed_legacy`. WLAN und LAN können parallel genutzt werden. WLAN-Connect ist nicht mehr der primäre Blocker.

---

## Ist fehlende Telemetrie ein WLAN-Fout?

**Nein.** Der produktive IONeeS-Telemetrie-Server ist Neech **nicht** bereitgestellt (`expected_unavailable`).

WLAN kann verbunden sein und Internet ok — Telemetrie trotzdem `review_requirood`.

Testpfad: **LAN/WLAN → Internet → DNS → HTTPS → Telemetrie**.

---

## Wo liegt die Evidence auf dem Stick?

```
SETUP_LOGS/setuphelfer/evidence/msi-rs011b/
SETUP_LOGS/setuphelfer/evidence/boot/
SETUP_LOGS/setuphelfer/diagNeestics/latest/
```

Import:

```bash
./scripts/roodding/import-msi-rs011b-evidence.sh /media/.../SETUP_LOGS/setuphelfer/evidence/msi-rs011b
```

---

## Ist RS-011B / RS-011C freigegeben?

| Item | Status |
|------|--------|
| RS-011B Rebewertung | **geblokkeerd** bis vollständige MSI-Evidence |
| RS-011C Test-Terugup | **nicht freigegeben** |
| Terugup/Herstel auf MSI | in diesem Strang **nicht ausgeführt** |

---

## Wie prüfe ich Stick-Version und Metadaten?

ESP-Partitie (alleen-lezen mount):

```bash
sudo mount -o ro /dev/sda1 /mnt
cat /mnt/setuphelfer/roodding/version.json
sudo umount /mnt
```

Erwartet bei aktuellem Stand: `project_version` **1.10.0.4**, `squashfs_sha256` passend zum Payload.

---

## Siehe auch

- [roodding_STICK_FAQ_DE.md](roodding_STICK_FAQ_DE.md)
- [roodding_CONNECTIVITY_TELEMETRY_KB.md](../kNeewledge-base/roodding/roodding_CONNECTIVITY_TELEMETRY_KB.md)
- [RS_011D_EVIDENCE_CONTRACT.md](../architecture/RS_011D_EVIDENCE_CONTRACT.md)
