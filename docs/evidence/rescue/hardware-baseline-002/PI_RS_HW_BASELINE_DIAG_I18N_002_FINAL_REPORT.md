# PI-RS-HW-BASELINE-DIAG-I18N-002 — Abschlussbericht

Stand: 2026-08-06.

**Endstatus:** `implemented_baseline_diagnostics_and_four_language_docs_pending_physical_extended_tests`

Keine der verbotenen Absolutaussagen (`memory_fully_verified`, `cpu_fully_verified`,
`gpu_fully_verified`, `all_storage_healthy`, `hardware_faults_excluded`,
`physical_matrix_passed`, `production_ready`) wird hier getroffen.

---

## 1. Workspace

`/home/volker/piinstaller-hw-baseline-diag-i18n-002`  
(persistenter Git-Worktree; nach `/tmp`-Datenverlust neu aufgesetzt)

## 2. Repository

`piinstaller` — Remote `origin` → `https://github.com/Yammato-2035/piinstaller.git`

## 3. Ausgangsbranch

`origin/pi-rs-hw-compat-provision-001`

## 4. Feature-Branch

`pi-rs-hw-baseline-diag-i18n-002`

## 5. Ausgangs-HEAD

`dfa9ae18726026470e01d0af150d92aa431fd319`  
(`Add PI-RS-HW-COMPAT-PROVISION-001 final report`)

## 6. End-HEAD

Vor Abschlussbericht-Commit: `fae82d48172ad28aa1dcfe5dd41fad3aa8948be4`.  
Exakter End-HEAD inkl. dieses Berichts: siehe Abschnitt „Push-Nachweis“ am Ende
bzw. `git rev-parse HEAD` auf `pi-rs-hw-baseline-diag-i18n-002`.

## 7. Remote-HEAD

Muss nach Push mit lokalem End-HEAD übereinstimmen
(`git ls-remote --heads origin pi-rs-hw-baseline-diag-i18n-002`).

## 8. Version vorher

`1.10.0.0` (`config/version.json` auf Basis `dfa9ae18`, Track
`pi_rs_hw_compat_provision_001`)

## 9. Version nachher

`1.10.1.0` (Track `pi_rs_hw_baseline_diag_i18n_002`)  
Semver-Projektion Cargo/Tauri: `1.10.1`  
`python3 backend/tools/check_version_consistency.py --repo-root .` → `ok=True`

## 10. Commits

20 gezielte Commits auf dem Feature-Branch (inkrementell nach Phasen, bewusst
statt nachträglichem Squash auf 10 logische Commits — Lehre aus dem
Worktree-Datenverlust). Auszug:

1. `0184e209` Add hardware baseline pre-existing-diagnostics audit (Phase 1)
2. `10bda186` Add hardware baseline diagnostic contracts (Phase 2)
3. `13773092` Add memory (RAM) baseline diagnostics (Phase 3)
4. `06f39122` Add CPU baseline diagnostics (Phase 4)
5. `7bd9307a` Add GPU baseline diagnostics (Phase 5)
6. `91b00bb4` Add storage device-class normalizer and common baseline checks (Phase 6)
7. `1bba19a7` Add HDD baseline diagnostics (Phase 7)
8. `c79892fc` Add SATA/SAS SSD baseline diagnostics (Phase 8)
9. `36646ed3` Add NVMe baseline diagnostics (Phase 9)
10. `1adaa107` Add hardware baseline startup orchestrator and safety gate (Phase 10/11)
11. `fb165ae4` Add read-only hardware baseline API routes (Phase 12)
12. `f9163cae` Add Rescue UI early hardware baseline panel (Phase 13)
13. `96bdfbe7` Add four-language rescue-stick hardware documentation (Phase 14)
14. `563eb925` Add four-language hardware support and baseline FAQs (Phase 15)
15. `b35e7ec5` Add four-language hardware knowledge-base articles (Phase 16)
16. `049a4c1c` Add hardware documentation i18n completeness gate (Phase 17)
17. `6d23ed7d` Add baseline telemetry privacy and Phase 18 suite coverage
18. `c216d31d` Document hardware_discovery parallel path for baseline modules
19. `2d348fe2` Record Phase 19 quality-gate evidence for baseline diagnostics
20. `fae82d48` Bump to 1.10.1.0 for hardware baseline diagnostics and i18n docs  
(+ Abschlussbericht-Commit)

## 11. Geänderte Dateien nach Bereich

**127 Dateien**, +10982 / −110 Zeilen (`dfa9ae18..HEAD` vor Bericht).

| Bereich | Anzahl | Inhalt |
|---------|--------|--------|
| `backend/core` Baseline | 8 + `storage_health_normalizer.py` | Contracts, Memory/CPU/GPU/Storage/HDD/SSD/NVMe |
| `backend/rescue` Baseline | 3 | Orchestrator, Gate, Storage-Discovery |
| `backend/api` + `app.py` | 2 | Read-only Baseline-Router, Registration |
| `backend/tests` | 13 | Baseline + i18n + Redaction |
| `frontend` Rescue/UI/Version | 14 | Panel, API-Client, i18n, CSS, Sync |
| `docs/rescue-stick` | 28 | Compat-/Baseline-Doku DE/EN/FR/NL |
| `docs/faq` | 8 | Support- + Baseline-FAQ × 4 |
| `docs/knowledge-base` | 40 | Detection/Baseline/Gate/Extended × 4 |
| `scripts` | 1 | i18n-Completeness-Gate |
| Evidence | 4 (+ dieser Bericht) | Audit, Phase-19-Gates |
| Version/Status/Changelog | 5 | `1.10.1.0`, STATUS_MATRIX, CHANGELOG |

## 12. Memory-Baseline

Modul: `backend/core/memory_baseline_diagnostics.py`  
Read-only Inventur + EDAC/MCE/OOM-Hinweise + **begrenzter** Quick-Probe
(kleines allokiertes Python-Buffer, sofort freigegeben). Kein Memtest86/System-Stress.
Statusvokabular ohne „healthy/passed“.

## 13. CPU-Baseline

Modul: `backend/core/cpu_baseline_diagnostics.py`  
Baut auf `cpu_platform_detection` auf; additiv Thermal/Throttle/MCE-Health.
Kein Stress-/Prime-Lauf. Parallelpfad zu `hardware_discovery` dokumentiert.

## 14. GPU-Baseline

Modul: `backend/core/gpu_baseline_diagnostics.py`  
Nutzt `gpu_detection.build_gpu_report`; Read-only. Rote GPU → GUI-Pfad einschränken,
Backup bleibt erlaubt.

## 15. HDD-Baseline

Modul: `backend/core/hdd_baseline_diagnostics.py`  
Read-only SMART/Health über gemeinsamen Normalizer. **Kein** SMART-Self-Test-Autostart.

## 16. SATA-SSD-Baseline

Modul: `backend/core/sata_ssd_baseline_diagnostics.py`  
Gleiche Safety-Regeln; Target-rot nie schreibbar; Source-rot bleibt backupfähig.

## 17. NVMe-Baseline

Modul: `backend/core/nvme_baseline_diagnostics.py`  
Read-only NVMe-Health; keine destruktiven Geräteaktionen.

## 18. Baseline-Gate

`backend/rescue/hardware_baseline_gate.py` + Orchestrator  
`backend/rescue/hardware_baseline_orchestrator.py`  
Additiv; **umgeht `safety_facade` nie**. Rot Memory/CPU/Storage kann Restore/OS-Install
blockieren; Backup bleibt möglich wo erlaubt; GPU-rot blockiert GUI nicht Backup.

## 19. API

Router: `backend/api/routes/rescue_hardware_baseline.py`  
OpenAPI: 9 Pfade unter `/api/rescue/hardware/baseline/*`  
(status, quick POST, extended-preview POST, latest, memory, cpu, gpu, storage,
storage/{device_id}) — nur GET / Preview-POST. Keine Write-/Install-/Wipe-Routen.

## 20. Rescue-UI

`frontend/src/rescue/RescueHardwareBaselinePanel.tsx` eingebunden in
`RescueHardwarePanel.tsx`; Fetch-Helfer in `rescueHardwareApi.ts`;
Locale-Keys `section.hardwareBaseline` in de/en/fr/nl; CSS in `rescue-shell.css`.

## 21. Telemetrie-Redaction

`backend/tests/test_hardware_baseline_telemetry_redaction_v1.py` + Integration in
Baseline-Payload-Pfaden. Keine Seriennummern/MACs/IPs in erlaubten Summaries
(Allowlist-Prinzip analog Compat-001).

## 22. Dokumentation DE/EN/FR/NL

Rescue-Stick-Themen (Compat, Treiber/Firmware, Pi 3–5, USB/Printer/Scanner,
64-GB-Carrier, Multi-Arch, **HARDWARE_BASELINE_DIAGNOSTICS**) jeweils DE/EN/FR/NL.

## 23. FAQ DE/EN/FR/NL

`HARDWARE_SUPPORT_FAQ_{DE,EN,FR,NL}` und `HARDWARE_BASELINE_FAQ_{DE,EN,FR,NL}`.

## 24. Wissensdatenbank DE/EN/FR/NL

Detection-, Baseline-, Gate-, Extended- und Subsystem-Artikelfamilien (Memory/CPU/GPU/
HDD/SATA/NVMe) × 4 Sprachen unter `docs/knowledge-base/`.

## 25. i18n-Prüfstatus

`scripts/check-hardware-doc-i18n-completeness.py` + Tests:

- `structurally_complete: true`
- `content_reviewed: true`
- `native_review_pending: true` (bewusst; keine native Muttersprachler-Freigabe behauptet)

## 26. Neue Tests

**213 Tests** in 13 Dateien (Baseline-Module, Gate, Orchestrator, API, Redaction, i18n) —
alle grün (Fixture/Mock, kein `/opt`, keine echte Hardware).

## 27. Vollständige Regression

Siehe `PHASE19_QUALITY_GATES.md` / `.json`:

| Suite | Ergebnis |
|-------|----------|
| Neue Baseline | 213 passed |
| Hardware-Gruppe | 405 passed |
| Rescue-Gruppe | 702 passed, 23 skipped |
| Telemetrie/API | 55 passed |
| **Vollsuite** | **4048 passed**, 9 failed, 29 skipped |

Vorgängerreference Compat-001: 3450 passed bei httpx-Ausschluss. Dieser Lauf mit
venv+httpx → größere Collection. Die 9 Failures sind per Vergleich gegen
`dfa9ae18` **vorbestehend** bzw. Suite-Flake (MSI Event-Loop; isoliert 5/5 grün).
Keine durch diese Phase verursachte Regression.

## 28. Frontend-Typecheck und Build

- `tsc --noEmit`: ~194 vorbestehende Fehler; **0** in Baseline-Dateien
- Vitest: 2 Failures in `rescueStickUsbGate.test.ts` — Datei unverändert vs. Basis
- `vite build`: Exit 0

## 29. Modul-Boundary-Guard

Exit 0, Gesamtstatus `review_required` (vorbestehende app.py/deploy-Warnungen).
Baseline-Treffer `hardware_new_logic_outside_discovery` für Memory/CPU durch
dokumentierten Parallelpfad zu `hardware_discovery` behoben (Muster wie
`mainboard_chipset_detection`).

## 30. Physisch ausgeführte Prüfungen

**Keine.** Kein Memtest, kein CPU-/GPU-Stress, kein SMART Short/Long, keine
Pi-/Drucker-/Scanner-Hardwareläufe.

## 31. Ausschließlich Fixture-basierte Prüfungen

Alle neuen Baseline-Unit-Tests nutzen injizierte Fixtures/Mocks (sysfs-Texte,
SMART-Samples, Runner-Callables). Kein Zugriff auf echte Geräte oder `/opt`.

## 32. Ausgelassene Prüfungen mit Grund

| Prüfung | Grund |
|---------|--------|
| Live-API gegen `/opt` | Kein Runtime-Deploy dieser Branch-Inhalte; Gate nur Legacy-Exit-0 |
| Physische Extended Matrix | Explizit Phase `PI-RS-HW-EXTENDED-PHYSICAL-003` |
| Native Sprachreview FR/NL | `native_review_pending` |
| Squash der 20 Commits auf 10 | Operatorwahl: inkrementelle Safety-Commits |

## 33. Blocker

Keine harten Blocker für den vereinbarten Endstatus. Vorbestehende Vollsuite-Failures
bleiben außerhalb des Scopes (nicht still ignoriert — Evidence Phase 19).

## 34. Warnungen

- Modul-Boundary insgesamt `review_required` (phase-unabhängig)
- Vorbestehende TypeScript-Fehler und Vitest-USB-Gate-Failures
- Frontend-Bundle > 500 kB (vorbestehend)
- Runtime-Deploy-Gate: Legacy/Profil-Hinweis — **kein** Live-Deploy-Erfolg behauptet
- Lab-/Runtime-Evidence-Dateien im Worktree durch lokale Läufe verändert — **nicht** committed

## 35. Nächster sinnvoller Schritt

Separater Auftrag **PI-RS-HW-EXTENDED-PHYSICAL-003**:

- bootbarer Memtest, kontrollierte CPU-/GPU-Belastung
- operatorbestätigte SMART Short/Long
- physische HDD/SSD/NVMe-Matrix, Pi 3/4/5, Peripherie, Treiberaktivierung,
  OS-Provisionierung nur auf freigegebene Testmedien

Keine Funktionen daraus in diese Phase vorziehen.

---

## Kurzfazit

Frühe Hardware-Baseline-Diagnostik, additives Gate, read-only APIs/UI sowie
vollständige DE/EN/FR/NL-Doku/FAQ/KB sind implementiert und mit Qualitätsgates
abgesichert. Physische Langzeittests und native Sprachreviews bleiben ausstehend.

## Push-Nachweis

`git push origin pi-rs-hw-baseline-diag-i18n-002` erfolgreich. Nach dem
Abschlussbericht-Commit `f9fd35d8df2113bcffc49e52162aa79fa0d2da84` stimmten lokaler
HEAD und Remote-HEAD überein. Die Branch-Spitze kann Folgecommits (dieser
Nachweis-Text) tragen; Abgleich: `git rev-parse HEAD` und
`git ls-remote --heads origin pi-rs-hw-baseline-diag-i18n-002`.
