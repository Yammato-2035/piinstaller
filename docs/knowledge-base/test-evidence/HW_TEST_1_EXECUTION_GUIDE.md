# HW-TEST-1 Durchfuehrungsleitfaden

## 1) Voraussetzungen pro Testlauf

- Test-ID aus Matrix festgelegt.
- Zielmedium eindeutig gemountet und identifiziert.
- **FIX-1 / SAFE-DEVICE-1:** Backup-Schreibpfad nur unter **`/mnt/setuphelfer/backups`** (oder Unterverzeichnis). **Nicht** unter `/media/<user>/…` (blockiert durch `validate_write_target`).
- Externe NVMe: als Administrator unter **`/mnt/setuphelfer/backups/<test-run>`** einhängen. **ext4 (HW1 empfohlen):** `mount` **ohne** `gid=`/`umask=`, danach `chown root:setuphelfer` und `chmod 0770` auf dem Mountpunkt — siehe **`HW_EXEC_1_REPEAT_INSTRUCTIONS.md`** (Abschnitt *Mount-Vorbereitung*). **NTFS/exFAT** für HW1 nicht empfehlen. Backend-Dienst: **`SupplementaryGroups=setuphelfer`** (Standard in den mitgelieferten Units).
- Nach `install-system.sh` / Paket-Upgrade: **`systemctl daemon-reload && systemctl restart setuphelfer-backend`**.
- Systemprofil-ID und Medienprofil bekannt.
- Risikoklasse geprueft (`requires_confirmation`, `destructive_risk` bei Bedarf).

## 2) Abbruchkriterien

Sofort abbrechen und `EvidenceRecord` mit `outcome=failed` oder `inconclusive` schreiben bei:

- Zielmedium nicht eindeutig oder verwechselt.
- Schreib-/Mountzustand nicht verifizierbar.
- unerwartete Sicherheitsblocker (Allowlist, Path-Containment).
- Inkonsistenz zwischen geplanter und realer Testumgebung.

## 3) Erfolgsdefinition

Nur bestanden, wenn zutreffend:

- Backup-Artefakt vorhanden und plausibel.
- Verify erfolgreich.
- Restore/Preview erfolgreich (je nach Testziel).
- Post-Restore-Validierung erfolgreich.
- Dienste laufen.
- API erreichbar.
- UI erreichbar.
- Keine manuellen Fixes erforderlich bei deterministischem Endzustand.

## 4) Evidence-Pflicht pro Lauf

Mindestens ein `EvidenceRecord` je realem Lauf:

- `source_type`: `hardware_test` oder passender Typ.
- `scenario`: Test-ID referenzieren.
- `raw_signals`: nur diagnose-relevante Signale.
- `diagnosis_links`: `suspected`/`confirmed`/`refuted`.
- `confirmed_root_cause` nur bei belastbarer Evidenz.

Auch `partial` und `inconclusive` muessen gespeichert werden.

## 5) Nachweise

- API-Resultate (strukturiert, keine unnoetigen Voll-Logs).
- relevante Statussignale (service active, verify status, error code).
- Ergebniszuordnung zur Matrix (`passed`/`failed`/`inconclusive`).

## 6) HW-EXEC-1-REPEAT (externe NVMe, post FIX-1)

- Vollstaendiger Ablauf: **`HW_EXEC_1_REPEAT_INSTRUCTIONS.md`** (Vorbereitung, Reihenfolge HW1-01..05, Evidence, Matrix-Feld `hw_exec_1_repeat_post_fix1`).
- **ext4:** `sudo mount /dev/<partition> /mnt/setuphelfer/backups/<run-id>` **ohne** `gid=`/`umask=`; danach `sudo chown root:setuphelfer` und `sudo chmod 0770` auf den Einhängepunkt. Begründung und typischer Fehler bei falscher Option: dieselbe Datei (*Mount-Vorbereitung*, *Typischer Fehler*).
- **NTFS/exFAT:** für HW1 nicht empfohlen; Kurzinfo nur in **`HW_EXEC_1_REPEAT_INSTRUCTIONS.md`**.
- Erfolg nur nach strenger SUCCESS-Definition in jener Datei dokumentieren; keine Schein-Erfolge.
