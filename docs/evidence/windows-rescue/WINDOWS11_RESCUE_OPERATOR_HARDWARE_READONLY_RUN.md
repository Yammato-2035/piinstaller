# Windows 11 Rescue — Operator Hardware Read-only Run

**Track:** `windows-laptop-rescue-inspect`  
**Ziel-Laptop:** Windows 11 Pro Insider/Beta, 2×2 TB NVMe, AMD Ryzen, NVIDIA GPU  
**Dualboot-Ziel (später):** Windows 11 Pro stable + Linux Mint (~1 TB)  
**Modus:** read-only — Telemetrie-ACK Pflicht für Grün

## Vor dem Start

- Rettungsstick am Laptop booten (UEFI)
- **Keine** Datenträger beschreiben, **kein** Windows reparieren
- Netzwerk nur für Telemetrie prüfen (TLS)
- Keine Passwörter, Tokens oder Dateiinhalte in Evidence speichern

## Schritt 1 — Plan erzeugen (read-only)

```bash
cd /path/to/setuphelfer   # oder Rescue-Stick-Pfad
bash scripts/windows-rescue/plan-windows-readonly-inspect.sh \
  docs/evidence/windows-rescue/operator_windows_readonly_plan_latest.json
```

Prüfen: `bitlocker.status`, `blocked_reasons`, `readonly_mount_plan`, `forbidden`

## Schritt 2 — BitLocker zuerst

| Status | Aktion |
|--------|--------|
| `unknown` | **Stop** — kein Dateizugriff, kein Mount |
| `locked` | **Stop** — Recovery-Key-Handoff, kein Unlock aus Rescue |
| `not_detected` / `unlocked` | Weiter mit read-only Prüfungen |

## Schritt 3 — Nur bei BitLocker-OK: Windows read-only prüfen

Erlaubt (Operator, read-only Mount-Kontext — **nicht** in diesem Workspace-Lauf):

- EFI-Partition read-only mounten
- Windows-NTFS read-only mounten (`-o ro`)
- Offline-Registry-Hives lesen (kein Schreiben)
- Winlogon `Shell` prüfen: `HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon`
- Explorer-Pfad-Hinweis: `Windows\explorer.exe` exists/readable?
- Benutzerprofil-Kandidaten: `Users\` (nur Metadaten, keine Inhalte in Telemetrie)

Verboten: `ntfsfix`, `chkdsk`, `bcdedit`, `bootrec`, Reparatur, Cloud-Upload

## Schritt 4 — Report + Telemetrie-Envelope

```bash
bash scripts/windows-rescue/ingest-operator-hardware-run.sh
```

Outputs:

- `docs/evidence/windows-rescue/windows_inspect_report_latest.json`
- `docs/evidence/windows-rescue/windows_rescue_telemetry_envelope_latest.json`
- `docs/evidence/windows-rescue/operator_hardware_run_status_latest.json`

## Schritt 5 — Telemetrie senden

```http
POST /api/rescue/windows-inspect
X-Setuphelfer-Run-Id: <run_id>
X-Setuphelfer-Payload-Hash: <sha256>
```

Antwort muss enthalten: `ack_id`, `payload_hash_sha256` (Match!)

Ohne ACK: Status `queued_local` oder `failed` — **kein Grün**

## Schritt 6 — ACK dokumentieren (optional Datei)

```bash
# Beispiel — nur Hash/ACK, keine Secrets
echo '{"status":"acknowledged","ack_id":"...","payload_hash_sha256":"..."}' \
  > docs/evidence/windows-rescue/operator_telemetry_ack_latest.json
bash scripts/windows-rescue/ingest-operator-hardware-run.sh
```

## Ausgaben für Workspace-Ingest (Modus A)

Falls Ergebnisse ins Repo übernommen werden:

1. `operator_windows_readonly_plan_latest.json`
2. `windows_inspect_report_latest.json`
3. `windows_rescue_telemetry_envelope_latest.json`
4. Optional: `operator_telemetry_ack_latest.json`
5. Terminal-Log ohne Secrets als `docs/evidence/windows-rescue/raw/operator_run_<timestamp>/`

## Gates (bleiben blockiert)

Repartition/Dualboot/ Bootloader-Schreiben bis:

- BitLocker geklärt
- Backup verifiziert
- Telemetrie ACK + Hash-Match
- Operator-Freigabe
- Ziel-NVMe-Plan reviewed
- W11-Pro-stable-Medium + Linux-Mint-Version festgelegt
- Bootmanager-Strategie update-resilient dokumentiert

## Verboten in diesem Track

NTFS-write, BitLocker-Unlock, Cloud-Datei-Backup, Restore, Partitionieren, Bootloader-write, Dualboot-Install, Windows-Update, Linux-Mint-Install
