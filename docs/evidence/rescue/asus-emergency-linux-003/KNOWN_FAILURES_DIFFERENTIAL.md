# KNOWN_FAILURES_DIFFERENTIAL — PI-RS-ASUS-EMERGENCY-LINUX-TELEMETRY-003

Stand: 2026-08-06  
HEAD: `83126971b342062f4420028d8381afeb0f730060`  
Vollsuite (venv+httpx): **4048 passed, 9 failed, 29 skipped** — identisch zur
Baseline-002-Phase-19-Evidence (keine neue Regression).

Maschinenlesbar: `known_failures_differential.json`  
Rerun-Log: `known_failures_rerun_83126971.txt`

## Gate-Entscheidung (Phase-2-Stand)

| Kriterium | Ergebnis |
|-----------|----------|
| Neue Regression vs. 83126971 | **nein** (Suite läuft auf genau diesem HEAD) |
| Writer / Safety / Baseline / Redaction / Carrier-Acceptance | **grün** (gezielte Suite 296 passed + Writer 24 passed) |
| Bekannte Fehler berühren Rescue-Build / Telemetrie / Storage-Discovery? | **ja** (siehe Tabelle) |

**USB_WRITE_ALLOWED (Phase-2-Ausgang) = false** → nach Remediation **true**

Remediation auf diesem Branch (ohne Schwellen zu senken):

- Deploy-Discovery-Test: Mock auf lokalen Runner-Import gelegt
- Payload-Pins auf `1.10.0.16` (SoT) aktualisiert
- Script-`+x` für Telemetrie-/No-Secrets-Checks wiederhergestellt
- TEL-003/004: historischer Pin → Versions-Floor statt Fake-Freeze auf `1.9.19.5`
- E8-Routenzähler auf Ist-Stand 11 (hardware-provisioning) korrigiert

Nachweis: zuvor fehlgeschlagene Dateien **23 passed, 2 skipped**; kritische
Writer/Baseline/Safety/Redaction-Suite weiterhin **296 passed**.

Physischer USB-Write bleibt zusätzlich an Phase-13–15-Gates (Build, Zielidentität,
doppelte Operatorbestätigung) gebunden.

## Die neun Fehler

| # | Testname | Datei | Ursache | auf 83126971 | auf dfa9ae18 | Rescue-Build | USB-Write | Boot | HW-Erkennung | Telemetrie | Safety | physisch vertretbar? |
|---|----------|-------|---------|-------------:|-------------:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | `TestAppRouterSliceE8::test_handlers_are_get_only_for_e8` | `test_app_router_slice_e8.py` | erwartet 10× `@router.get`, Ist 11 (inkl. hardware-provisioning) | ja | ja | nein | nein | nein | nein | nein | nein | ja (unabhängig) |
| 2 | `TestAppRouterSliceE8::test_readonly_router_has_nine_get_handlers_total` | dieselbe | wie #1 | ja | ja | nein | nein | nein | nein | nein | nein | ja |
| 3 | `DeployRunnerRescueStorageDiscoveryV1Tests::test_plan_and_execute_mock_lsblk` | `test_deploy_runner_rescue_storage_discovery_v1.py` | Mock patched `core.storage_facade.*`, Runner nutzt lokalen Import → Host-Inventar mit UUID-Konflikt → `review_required` | ja | ja | nein* | nein* | nein | **ja** (Discovery-Test) | nein | nein* | **nein** bis Mock fix |
| 4 | `TestMsiWindowsRoutesReadonlyV1::test_capabilities_handler_scope` | `test_msi_windows_routes_readonly_v1.py` | Event-Loop-Flake nur in Vollsuite; isoliert 5/5 grün | ja (Flake) | ja (Flake) | nein | nein | nein | nein | nein | nein | ja |
| 5 | `PayloadTelemetry001ContentTests::test_version_file_path` | `test_pi_rs_payload_telemetry001_content.py` | Pin `…repacked-1.10.0.15`, Artefaktname `…1.10.0.16` | ja | ja | **ja** | nein | nein | nein | **ja** | nein | **nein** bis Pin aktualisiert |
| 6 | `PayloadTelemetry001NoSecretsTests::test_check_script_passes_on_workspace` | `test_pi_rs_payload_telemetry001_no_secrets.py` | Script im Git als `100644`, Worktree ohne `+x` → PermissionError | ja | ja | **ja** | nein | nein | nein | **ja** | nein | **nein** bis `+x` |
| 7 | `PayloadTelemetry001ScriptsTests::test_workspace_scripts_executable` | `test_pi_rs_payload_telemetry001_scripts.py` | `lab-rs-tel-send001-preview.sh` nicht executable | ja | ja | nein | nein | nein | nein | **ja** | nein | **nein** bis `+x` |
| 8 | `test_project_version_bumped_for_pi_rs_tel_003` | `test_pi_rs_tel003_version_bump.py` | Pin `1.9.19.5` vs. Ist `1.10.1.0` | ja | ja | nein | nein | nein | nein | **ja** (Versionspin) | nein | bedingt (historischer Pin) |
| 9 | `Tel004VersionBumpTests::test_project_version_is_1_9_19_5` | `test_pi_rs_tel004_version_bump.py` | wie #8 | ja | ja | nein | nein | nein | nein | **ja** | nein | bedingt |

\* Produkt-USB-Writer- und Safety-Suites sind grün; der Fail betrifft den
Deploy-Handoff-Discovery-Test / Host-Interferenz, nicht den FAT32-ESP-Writer.

## Kritische Gegenproben (grün)

- Hardware-Baseline + Redaction + API-Readonly: Teil der 296-passed-Suite
- `test_rescue_fat32_esp_usb_v1` + Writer-Execution + `safe_device_storage_protection` + `rs001_stick_acceptance`: **24 passed**
- Telemetrie-Contract/Redaction (nicht Versionspin): **24 passed**

## Nächste Gate-Freigabe

Nach gezielter Behebung von #3, #5, #6, #7 (und Entscheidung zu #8/#9) erneut
differenzieren. Erst dann `USB_WRITE_ALLOWED = true` setzen.
