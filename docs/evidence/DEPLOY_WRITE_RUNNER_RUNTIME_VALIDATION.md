# Deploy Write Runner — Runtime-Validierung (Dry-run, keine sudoers-Installation)

Stand: 2026-05-08. **Phase:** nur Contract + Dry-run; kein Blockdevice-Write, kein `dd`/`mkfs`/`mount`, keine produktive sudoers-Datei in diesem Repo.

## Phase 0 — Systemanalyse (Read-only, keine Änderungen)

Auf dem Prüfhost (Beispielauszug, für Reproduzierbarkeit dokumentiert):

| Aspekt | Befund (Beispiel) |
|--------|-------------------|
| Effektiver User | `uid=1002(gabriel)` |
| Gruppen | u. a. `sudo`, `setuphelfer`, `workspace`, `piinstaller` — **nicht** zwingend `disk` |
| `/dev/sd*` | typisch `root:disk`, Modus `brw-rw----` — ohne Gruppe `disk` oft **kein** direkter Zugriff |
| `sudo` | `/usr/bin/sudo` vorhanden |
| `/etc/sudoers` | nicht ohne root lesbar; `/etc/sudoers.d/` existiert mit Drop-ins |
| Späterer Runner-Start | sinnvoll: unprivilegierter Dienst-User + **einmalig** `sudo` auf **fest** eingetragene Runner-Zeile (siehe Phase 4), nicht dauerhaft root-Backend |

Hinweis: Werte sind **hostspezifisch**; vor Betrieb erneut erfassen.

## Phase 1 — Runner-Isolation (Dry-run)

Kommando:

```bash
python3 backend/tools/deploy_write_runner.py --job /abs/path/job.json --dry-run
```

Erwartetes Verhalten (Implementierung):

- **Kein Netzwerk:** Modul importiert keine Netzwerk-Clients.
- **Kein Device-Open:** kein `open(..., "rb+")` auf Zielgerät, nur optional Lesen der Jobdatei.
- **Keine Shell:** kein `shell=True`, kein `os.system`.
- **Kein Kindprozess:** Runner nutzt keine `subprocess`-API (Tests rufen den Runner per `subprocess` auf — das ist Test-Harness, nicht Produktionscode).
- **Keine Fremdpfade für `--job`:** nur unter konfigurierten Wurzeln (siehe Phase 3).
- **Umgebung:** keine Auswertung von `PYTHONPATH`/`LD_PRELOAD` im Runner selbst; bei **sudo** siehe Phase 4 (Risiko `env_keep`).

Optionaler harter Nachweis (manuell): `strace -e trace=openat,connect` auf den Prozess — sollte kein `connect` und kein Öffnen von `/dev/sd*` zeigen (nur Jobdatei unter erlaubtem Pfad).

## Phase 2 — Jobfile-Sicherheit (fail-closed)

| Szenario | Erwartung |
|----------|-----------|
| Manipulierter `job_hash` | `DEPLOY_RUNNER_JOB_HASH_MISMATCH` |
| Manipuliertes `target_device` / `image_path` ohne Hash-Neucompute | Hash-Mismatch |
| Abgelaufen (`expires_at`) | `DEPLOY_RUNNER_JOB_EXPIRED` |
| Fehlende Guard-Felder | `DEPLOY_RUNNER_JOB_INVALID` |
| `image_path` außerhalb Cache | `DEPLOY_RUNNER_JOB_IMAGE_INVALID` |
| Symlink als **Jobdatei** (`--job` zeigt auf Symlink) | Block (`job_path_symlink`) |
| Directory-Traversal bei `--job` | nach `resolve()` außerhalb Präfix → Block |
| Jobdatei außerhalb erlaubter Wurzel | `job_path_outside_allowed_prefix` |
| Replay (optional) | Mit `DEPLOY_RUNNER_REPLAY_GUARD=1` zweite **gültige** Validierung desselben `(job_id, job_hash)` im selben Prozess → `DEPLOY_RUNNER_JOB_REPLAY_DUPLICATE` |

Automatisiert: `backend/tests/test_deploy_write_runner_runtime_v1.py`, `backend/tests/test_deploy_write_runner_contract_v1.py`.

## Phase 3 — Pfad-Containment

- **`Path(...).expanduser()`** und **`resolve(strict=False)`** für `--job`.
- **`Path.is_symlink()`** auf dem vom Operator angegebenen Jobpfad: Symlink → sofort abgelehnt (kein Folgen für Jobdatei).
- **`Path.relative_to(allowed_root)`** pro erlaubter Wurzel.
- Erlaubte Wurzeln (Code): `/var/lib/setuphelfer/deploy-jobs`, `backend/cache/deploy` (modulstabil aufgelöst).
- **Image-Pfad:** weiterhin `resolve` + Cache-Allowlist im Contract (Symlink der Image-Datei nach außen wird durch Auflösung erkannt).

Hardlink zweiten Namens auf dieselbe Jobdatei unter dem Cache: kein Symlink → Dry-run weiterhin möglich (gleicher Inhalt).

## Phase 4 — sudoers-Design (nur Dokumentation)

**Nicht** installiert in diesem Schritt.

### Beispiel (illustrativ — Wildcards absichtlich riskant)

```text
setuphelfer ALL=(root) NOPASSWD: /usr/bin/python3 /opt/setuphelfer/backend/tools/deploy_write_runner.py --job *
```

### Risiken

| Risiko | Problem |
|--------|---------|
| `*` am Ende | **Argument-Injection:** Angreifer mit sudo-Recht könnte `--job /path` durch zusätzliche Tokens erweitern, falls die sudoers-Zeile zu breit ist. |
| `NOPASSWD` | Erhöht Impact bei Kompromittierung des Users. |
| `env_keep` | `PYTHONPATH`, `LD_PRELOAD`, `PYTHONHOME` können Interpreter oder Bibliotheken umleiten → **Codeausführung** trotz festem Skriptpfad. |
| `secure_path` | Wenn nicht gesetzt/gesichert: `PATH`-Hijacking für Hilfsprogramme (hier weniger relevant, wenn Python absolut). |
| Wildcard-Pfade | Joker in sudoers sind fehleranfällig; besser **exakt ein Binary** + **ein** erlaubter Job-Root auf Dateisystemebene. |

### Später akzeptable Richtung

- **Keine** Wildcards in der sudoers-Argumentliste.
- Absoluter Pfad zu **einem** Python-Interpreter und **einem** Runner-Skript.
- Entweder: sudoers erlaubt nur `--dry-run` und `--job` mit **keinem** weiteren freien Text (schwer in sudoers allein zu erzwingen) — praktisch: **zusätzlich** Pfad-Containment im Runner (implementiert) + Jobdateien nur unter `/var/lib/setuphelfer/deploy-jobs/`.
- `Defaults!/pfad/zum/python !env_keep` bzw. minimale `env_keep` nach Vendor-Guidelines; `LD_PRELOAD` leer.
- Optional: `NOEXEC` auf temporären Verzeichnissen für den Ziel-User (Betriebssystem-spezifisch).

## Phase 5 — Dry-run Runtime-Probe

1. Gültigen Job mit `build_real_write_job` erzeugen oder aus Tests übernehmen.
2. Datei unter `backend/cache/deploy/*.json` speichern (kein Symlink).
3. Ausführen:

```bash
cd /path/zum/repo
python3 backend/tools/deploy_write_runner.py --job "$(pwd)/backend/cache/deploy/job.json" --dry-run
```

Erwartung: eine JSON-Zeile auf stdout mit `DEPLOY_RUNNER_DRY_RUN_OK`; Jobdatei byteweise unverändert; keine Mounts, keine Dauerprozesse durch den Runner.

## Phase 6 — Tests

```bash
python3 -m py_compile backend/deploy/real_write_runner_contract.py backend/tools/deploy_write_runner.py
./venv/bin/python3 -m unittest backend.tests.test_deploy_write_runner_runtime_v1 \
  backend.tests.test_deploy_write_runner_contract_v1 -v
./venv/bin/python3 -m unittest backend.tests.test_deploy_real_write_prototype_v1 \
  backend.tests.test_deploy_real_write_guard_v1 -v
```

Hinweis: Modulpfad `backend.tests…` setzt voraus, dass das Arbeitsverzeichnis das Repo-Root ist oder `PYTHONPATH` den `backend`-Ordner enthält.

## Phase 7 — Abnahme-Checkliste

- [x] Kein echter Write auf Blockdevices im Runner.
- [x] Keine sudoers-Installation aus diesem Task.
- [x] Keine Shell/`subprocess`-Eskalation im Runner-Quelltext (Tests ausgenommen).
- [x] Traversal/Symlink auf Jobpfad blockiert.
- [x] Job-Manipulation ohne Hash → Mismatch.
- [x] Dry-run-JSON stabil (festes Schlüsselset).
- [x] Tests grün (siehe Phase 6).

## Bekannte Grenzen

- Replay-Schutz `DEPLOY_RUNNER_REPLAY_GUARD` ist **prozesslokal**; über Prozessgrenzen hinweg ist ein persistenter Ledger oder Einmal-Token nötig.
- Systemanalyse (Phase 0) ist eine Momentaufnahme; vor Produktionsbetrieb erneut prüfen.
