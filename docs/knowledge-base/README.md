# Wissensdatenbank (`docs/knowledge-base/`)

Kuratierte Notizen aus Support- und Setup-Runden, damit Lösungen **nicht doppelt** gesucht werden müssen.

| Datei | Inhalt |
|--------|--------|
| [APT_REPOSITORIEN_UND_DOCKER_FAQ.md](APT_REPOSITORIEN_UND_DOCKER_FAQ.md) | **FAQ:** APT-Repositories, Linux Mint vs. Ubuntu-Codename, Docker / Docker Desktop, Grafana, Cursor, Chrome, totes ASUS-Repo, Diagnosebefehle, Copy-Paste-Blöcke |
| [CHAT_ZUSAMMENFASSUNG_APT_DOCKER_2026-04.md](CHAT_ZUSAMMENFASSUNG_APT_DOCKER_2026-04.md) | **Session-Protokoll** der zugehörigen Chat-Runde (Verlauf + Verweise, ohne doppelte Befehlslisten) |
| [BACKUP_RECOVERY_FILE_ENGINE_REALITY.md](BACKUP_RECOVERY_FILE_ENGINE_REALITY.md) | **Technik-Notiz:** Schwachstelle `arcname=p.name`, Umstellung auf rekursive relative Pfade, Restore/Verify-Konsistenz, offene Full-Recovery-Risiken |
| [RESTORE_ISOLATED_TEST_FROM_BACKUP.md](RESTORE_ISOLATED_TEST_FROM_BACKUP.md) | **Nachweis:** isolierter `restore_files`-Test nach `/tmp/setuphelfer-restore-test`, Skript `tools/setuphelfer_restore_isolated_test.py`, Grenzen (VM-Archiv, absolute Symlink-Ziele) |
| [BACKUP_TARGET_PERMISSIONS.md](BACKUP_TARGET_PERMISSIONS.md) | **Betrieb:** sicheres Schreibmodell für Backup-Mounts (`setuphelfer`-Gruppe, 0770, systemd `SupplementaryGroups`, optional VM-/Test-Flags) |
| [FULL_RESTORE_BOOT_TEST.md](FULL_RESTORE_BOOT_TEST.md) | **Nachweis (VM):** Datei-Restore, Boot von Zielplatte, SSH-Check; Verweis auf ausführlichen Report; Hinweis auf Installer-Finalzustand |
| [BUILD_RUNTIME_CONSISTENCY.md](BUILD_RUNTIME_CONSISTENCY.md) | **Betrieb/Runtime:** Konsistenz von Source, Build, Tauri, API-Version, Status-Ampeln, Netzwerk- und Update-Start-Verhalten |
| [INSTALLATION_PATH_AUDIT.md](INSTALLATION_PATH_AUDIT.md) | **Audit-Leitfaden:** Pfadmigration, Legacy-Erkennung, funktionale Regeln und erwartete Audit-Ausgaben |

**Verwandt im Repo:** [ASUS ROG Lüftersteuerung](../ASUS_ROG_FAN_CONTROL.md) (Link in die APT-FAQ).

Neue Themen: eigene Datei unter `knowledge-base/` oder Abschnitt in der APT-FAQ ergänzen.
