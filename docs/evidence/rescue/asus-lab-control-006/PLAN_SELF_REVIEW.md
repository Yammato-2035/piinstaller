# PLAN_SELF_REVIEW — PI-RS-ASUS-LAB-CONTROL-006

## 6.1 Falscher Rechner / Datenträger

| Frage | Antwort / Maßnahme |
|-------|-------------------|
| MSI statt ASUS? | Auth nur bei `exact_match` auf G513QM + machine_id; MSI-Profile blockieren ASUS-Freigaben. |
| nvme0/1 Drift? | Rollen über `nvme_identity_hash` (6b45… / ed84…), nie allein Device-Name. |
| Stick ausgeschlossen? | SETUPHELFER/SETUP_LOGS Labels + USB by-id; keine Write-Ziele auf Stick außer Evidence. |

## 6.2 Stale Runtime/Payload

| Frage | Maßnahme |
|-------|----------|
| Payload = Build? | Gate: Stick SHA256 == Manifest == `rescue_payload_version` == Commit. |
| Alte Logs mischen? | Import nur nach Run-ID; kein „newest session“ Fallback. |

## 6.3 Logverlust

| Risiko | Gegenmaßnahme |
|--------|----------------|
| Setup hängt | Periodischer Collector + Heartbeat vor Hang |
| Reboot | Letzter Flush; Run-ID auf Stick; WinPE erneut mit gleicher Run-ID wenn vorbereitet |
| X: weg | Quellenliste inkl. C:/$WINDOWS.~BT; Stick als Primärziel |
| SETUP_LOGS fehlt | `setup_capture_ready=false` — Setup-Wrapper startet nicht „grün“ |
| Collector stirbt | Heartbeat-Timeout → Operator-Status LOGS_FEHLEN, kein Fake-Erfolg |

## 6.4 Remote-Unterbrechung

| Risiko | Gegenmaßnahme |
|--------|----------------|
| Netz weg | Job-State persistiert; kein Fake-success; Reconnect über job_id |
| Folgebefehl | Keine automatische Ableitung aus stdout |

## 6.5 Firmware / Secure Boot

| Risiko | Gegenmaßnahme |
|--------|----------------|
| Falsches Modell | BIOS-335 nur nach exact model + official package hash |
| BitLocker Recovery | RO-Check + Warnung; keine Mutation; Flash diesmal plan-only |

## 6.6 Zusätzliche Fehlermöglichkeiten (≥5) + Schutz

1. **Collector schreibt auf Windows-NVMe statt Stick** → nur Volumes mit SETUP_LOGS.TAG/Label; Write-Test dort.
2. **Run-ID Kollision / unknown-norunid** → zentraler Generator `asus-win11-<UTC>-<8hex>`; Gate verweigert norunid.
3. **Operator bootet MSI-Lab-Auto GRUB** → ASUS Auto-Capture ConditionKernelCommandLine schließt MSI lab/e2e aus; Identity-Gate.
4. **Dirty NTFS später wieder unmountable** → Bookworm ntfs-3g vendor; fail-closed bei GLIBC≥2.38 Inject.
5. **Remote shell löscht falsche Platte** → vor Raw-Disk erneut Fingerprint; BitLocker-Muster block; Rescue-Stick denylist.
6. **SetupDiag ohne Quellen als Erfolg** → Exitcode + Quellenpflicht; insufficient_evidence ohne Dateien.
7. **Evidence aus 095959Z als „neu“ importiert** → Run-ID/Boot-ID Gate.

## plan_status

```text
plan_status: ready
```

Bereit für Implementierung der Lab-Auth-, Live-Capture- und Remote-Job-Erweiterungen sowie Payload/Stick-Prep.
Physischer instrumentierter Setup-Lauf erfordert Operator vor Ort — nicht ohne P05–P08.
BIOS 335 und Mint bleiben plan-only bis nach Live-Evidence.
