# FINAL_RESULT — PI-RS-ASUS-LAB-CONTROL-006

## Status

`implemented_ready_for_physical_run`

(Nicht `physical_evidence_collected` — kein neuer instrumentierter Setup-Lauf am ASUS in dieser Session.)

## Workspace

1. Ausgang: `/home/volker/piinstaller` (Branch `pi-rs-bvr-gui-vt-progress-002`, Drift unberührt)
2. Ziel: `/tmp/piinstaller-asus-lab-control-006`
3. Repo: `Yammato-2035/piinstaller`
4. Branch vorher: `pi-rs-asus-lab-control-006` @ `9ac93c56`; nachher: neuer Commit auf demselben Branch
5. HEAD Basis: `f89a5187` (ASUS Win11 Retest-005)
6. Basisbranch: `origin/pi-rs-asus-win11-retest-005`
7. origin: Feature-Branch `pi-rs-asus-lab-control-006` (Push nach Commit)
8. Fremde Drift in `/home/volker/piinstaller` und `/tmp/piinstaller-asus-win11-retest-005`: **unangetastet**
9. Ja — fremde Drift blieb unangetastet; nur selektive Kopie der untracked ASUS-Boot-Profile-Module

## Planung

10. Kritischer Pfad: **A — instrumentierte Win11 Live-Capture**
11. Verworfen jetzt: B BIOS 335 first, C Mint first
12. plan_status: **ready**
13. Neue Fehler (Self-Review): Collector→NVMe; norunid; MSI-GRUB; glibc ntfs; Remote wipe wrong disk; SetupDiag fake success; stale import; **plus** ESP/Squashfs Versionsdrift; WIN_DIAG-Nesting bei Inject
14. Schutz: SETUP_LOGS-only writes; Run-ID-Gate; Identity+Disk-Fingerprint; Bookworm ntfs-3g; Inject `rm -rf` vor WIN_DIAG; ESP-Carrier-Sync; insufficient_evidence ohne Fake-Ursache

## Zielrechner (aus Evidence 095959Z, nicht neu behauptet)

15. Identity: G513QM / machine_id `79396619…` — Lab-YAML
16. Modell: ROG Strix G513QM
17. BIOS: **331** (unverändert; 335 nicht geflasht)
18. Windows NVMe hash `6b45cc50…`
19. Linux NVMe hash `ed84d453…`
20. Secure-Boot/TPM: nicht neu gemessen in dieser Session
21. BitLocker: nur Policy RO / Guard
22. BitLocker verändert: **nein**

## Implementierung

23. Lab-Autorisierungsprofil: `config/lab-targets/asus-rog-gabriel.yaml` + `rescue_asus_lab_authorization.py`
24. Remote-Job-Contract: `rescue_lab_job_contract.py` + Store GET/Cancel
25. Shell-Audit: command_hash, BitLocker-Guard, Signatur/Nonce/Expiry
26. Windows-Live-Collector: `collect-win11-live-capture.ps1` + Backend-Contract
27. Run-ID: `asus-win11-<UTC>-<8hex>`; `unknown-norunid` verboten
28. SETUP_LOGS: Label/`SETUP_LOGS.TAG`, kein Laufwerksbuchstabe allein
29. SetupDiag: Copy-Ziele vorhanden; Erfolg ohne Quellen unzulässig (Contract)
30. Mint-Node: **plan-only** (`MINT_NODE_DECISION.md`)
31. BIOS-335: **plan-only / deferred** (`BIOS_335_DECISION.md`)

## Physischer Lauf

32. Payload auf Stick: **1.10.3.1** (ESP-Carrier + Squashfs-JSON)
33. Payload-SHA256: `56a37200d7c3c72ead3f9fd8584a57fa36b4e578013b64e6a8d38d3d76491026`
34–43. Neuer instrumentierter Setup-Lauf: **noch nicht ausgeführt** (Operator vor Ort)
    - Collector/Heartbeats/Panther/Rollback/SetupDiag/Freeze-Ursache: n/a bis physischer Lauf
    - Letzter bekannter physischer Lauf bleibt `095959Z` / Payload `1.10.2.9` / `insufficient_evidence`

## Risikohandlungen

44. BIOS geflasht: **nein**
45. Partitionen gelöscht/geändert: **nein**
46. Restore intern: **nein**
47. Windows-EFI geändert: **nein**
48. Secure-Boot-Schlüssel geändert: **nein**
49. Unbeschränkte Shell physisch: **nein** (Contract/API vorhanden)
50. BitLocker verändert: **nein**

## Qualität

51. Tests: lab-control-006 + asus_rog_boot_profile — grün (27)
52. Runtime-/opt-Gate: nicht gegen Live-`/opt` deployed (Code + Stick-Prep; Phase-0 Runtime-Tests nicht Teil dieses Laufs)
53. Payload-Gate: Stick ESP `1.10.3.1`, Squashfs SHA wie oben; Restcarrier `opt/.../rescue_payload_version` Plaintext kann bis nächstem Inject noch stale sein — **JSON ist maßgeblich**
54. Evidence: `docs/evidence/rescue/asus-lab-control-006/`
55–56. Commit + Push auf Feature-Branch
57. Offen: physischer instrumentierter Setup; Disk-Rollen `confirmed:false`; Agent-Execute/mTLS Bridge; Plaintext-Carrier-Rest
58. Nächster Schritt: Operator startet Setup mit Live-Capture am ASUS (`SETUPHELFER_WIN_DIAG`), Stick zurück, Import nach Run-ID, dann BIOS/Mint entscheiden
