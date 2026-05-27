from __future__ import annotations

from core.diagnostics.models import DiagnosticAction, DiagnosticCase, DiagnosticCheck


def _a(action_id: str, prio: int, de: str, en: str) -> DiagnosticAction:
    return DiagnosticAction(id=action_id, priority=prio, text_de=de, text_en=en)


def _c(check_id: str, desc: str, expects: str) -> DiagnosticCheck:
    return DiagnosticCheck(id=check_id, description=desc, expects=expects)


DIAGNOSTIC_CATALOG: list[DiagnosticCase] = [
    DiagnosticCase(
        id="BACKUP-MANIFEST-001",
        domain="backup_restore",
        title_de="Manifest fehlt im Backup",
        title_en="Manifest missing in backup",
        summary_de="Das Archiv ist ohne MANIFEST.json nicht als belastbares Restore-Backup nutzbar.",
        summary_en="Archive without MANIFEST.json is not reliable for restore validation.",
        severity="critical",
        confidence="high",
        detection_sources=["api_result", "file_check"],
        checks=[_c("manifest-present", "Pruefe MANIFEST.json im Archiv", "present")],
        root_causes=["Unvollstaendiger Backup-Lauf", "Archiv manuell veraendert"],
        recommended_actions=[_a("recreate-backup", 1, "Backup neu erstellen und Verify ausfuehren.", "Create a new backup and run verify.")],
        related_docs=["docs/developer/BACKUP_MANIFEST.md"],
        related_faq=["docs/faq/RESCUE_FAQ.md"],
        tags=["manifest", "fail-fast"],
    ),
    DiagnosticCase(id="BACKUP-ARCHIVE-002", domain="backup_restore", title_de="Archiv beschaedigt", title_en="Archive is corrupted", summary_de="Gzip/Tar-Integritaet fehlgeschlagen.", summary_en="Gzip/tar integrity failed.", severity="critical", confidence="high", detection_sources=["api_result"], root_causes=["Abbruch beim Schreiben", "Speichermediumfehler"], recommended_actions=[_a("use-other-archive", 1, "Anderes Archiv pruefen.", "Verify a different archive.")], tags=["archive", "verify"]),
    DiagnosticCase(id="BACKUP-HASH-003", domain="backup_restore", title_de="Hash-Mismatch", title_en="Hash mismatch", summary_de="Manifest und extrahierte Daten stimmen nicht ueberein.", summary_en="Manifest hash and extracted data do not match.", severity="high", confidence="high", detection_sources=["api_result"], root_causes=["Dateibeschaedigung", "Falsches Archiv"], recommended_actions=[_a("new-backup", 1, "Neues Vollbackup erstellen.", "Create a new full backup.")], tags=["hash_mismatch"]),
    DiagnosticCase(id="RESTORE-PATH-004", domain="backup_restore", title_de="Unsicherer Restore-Pfad", title_en="Unsafe restore path", summary_de="Path-Containment wurde verletzt oder Pfad ist nicht erlaubt.", summary_en="Path containment failed or path is not allowlisted.", severity="critical", confidence="high", detection_sources=["api_result", "file_check"], destructive_risk=True, requires_confirmation=True, tags=["path_containment"]),
    DiagnosticCase(id="RESTORE-PARTIAL-005", domain="backup_restore", title_de="Restore nur teilweise erfolgreich", title_en="Restore partially successful", summary_de="Kritische Dateien fehlen nach Restore.", summary_en="Critical files are missing after restore.", severity="high", confidence="high", detection_sources=["api_result"], tags=["partial_restore"]),
    DiagnosticCase(id="RESTORE-RUNTIME-006", domain="backup_restore", title_de="Restore-Ziel ungueltig oder fehlend", title_en="Restore target missing or invalid", summary_de="Restore wurde ohne gueltiges target_dir angefordert oder auf ein gesperrtes Ziel gelenkt.", summary_en="Restore was requested without a valid target_dir or pointed to a blocked target.", severity="high", confidence="high", detection_sources=["api_result", "config_check"], tags=["restore_target", "write_protection"]),
    DiagnosticCase(
        id="RESTORE-TMPFS-007",
        domain="storage_filesystem",
        title_de="Restore in /tmp fehlgeschlagen",
        title_en="Restore on /tmp failed",
        summary_de="/tmp (tmpfs) oder PrivateTmp reicht fuer Verify/Preview-Extraktion oft nicht aus.",
        summary_en="/tmp (tmpfs) or PrivateTmp often lacks space for verify/preview extraction.",
        severity="medium",
        confidence="high",
        detection_sources=["file_check", "api_result"],
        root_causes=["Kleines tmpfs", "PrivateTmp ohne grosses TMPDIR", "Preview unter /tmp"],
        recommended_actions=[
            _a("set-tmpdir-dropin", 1, "TMPDIR auf grosses persistentes Verzeichnis setzen (systemd drop-in), Dienst neu starten.", "Set TMPDIR to a large persistent path (systemd drop-in) and restart the service."),
        ],
        related_docs=["docs/knowledge-base/BACKUP_VERIFY_PREVIEW_RUNTIME.md"],
        related_faq=["docs/faq/BACKUP_RESTORE_FAQ_DE.md", "docs/faq/BACKUP_RESTORE_FAQ_EN.md"],
        tags=["tmpfs", "storage", "private_tmp", "preview"],
    ),
    DiagnosticCase(id="PERM-GROUP-008", domain="permissions", title_de="Gruppenmodell fehlt", title_en="Group permission model missing", summary_de="setuphelfer-Gruppe/0770/SupplementaryGroups ist nicht konsistent.", summary_en="setuphelfer group/0770/SupplementaryGroups is inconsistent.", severity="high", confidence="high", detection_sources=["config_check", "file_check"], tags=["permissions"]),
    DiagnosticCase(id="SYSTEMD-START-009", domain="systemd_services", title_de="Dienst startet nicht", title_en="Service fails to start", summary_de="systemd meldet Startfehler.", summary_en="systemd reports startup failure.", severity="high", confidence="medium", detection_sources=["systemctl", "log_pattern"], tags=["systemd"]),
    DiagnosticCase(id="SYSTEMD-CRASH-010", domain="systemd_services", title_de="Dienst startet und crasht", title_en="Service starts then crashes", summary_de="Dienst faellt nach kurzer Laufzeit aus.", summary_en="Service exits shortly after startup.", severity="high", confidence="medium", detection_sources=["systemctl", "log_pattern"], tags=["crashloop"]),
    DiagnosticCase(id="RUNTIME-PORT-011", domain="app_setuphelfer_runtime", title_de="Port nicht gebunden", title_en="Required port not bound", summary_de="Backend/UI-Port ist nicht offen oder belegt.", summary_en="Backend/UI port is not open or is already used.", severity="high", confidence="high", detection_sources=["api_result", "log_pattern"], tags=["port"]),
    DiagnosticCase(id="NODE-OPTIONS-012", domain="app_setuphelfer_runtime", title_de="NODE_OPTIONS fehlen", title_en="NODE_OPTIONS missing", summary_de="Runtime-Umgebung fehlt notwendige Node-Optionen.", summary_en="Runtime environment is missing required Node options.", severity="medium", confidence="medium", detection_sources=["config_check", "systemctl"], tags=["node"]),
    DiagnosticCase(id="SYSTEMD-RESTRICT-013", domain="systemd_services", title_de="Restriktive Unit blockiert Laufzeit", title_en="Restrictive unit blocks runtime", summary_de="Unit-Optionen verhindern benoetigte Zugriffe.", summary_en="Unit options block required runtime access.", severity="high", confidence="medium", detection_sources=["systemctl", "config_check"], tags=["unit-hardening"]),
    DiagnosticCase(id="SYSTEMD-AF-014", domain="systemd_services", title_de="AddressFamily zu restriktiv", title_en="AddressFamily too restrictive", summary_de="Netzwerkfamilien sind in der Unit nicht freigegeben.", summary_en="Required address families are blocked by unit settings.", severity="high", confidence="medium", detection_sources=["systemctl", "config_check"], tags=["addressfamily"]),
    DiagnosticCase(id="UI-NO-BACKEND-015", domain="app_setuphelfer_runtime", title_de="UI erreichbar, Backend nicht", title_en="UI reachable, backend not", summary_de="Frontend laeuft, API-Dienst ist nicht erreichbar.", summary_en="Frontend is running but API service is unreachable.", severity="high", confidence="high", detection_sources=["api_result", "systemctl"], tags=["frontend", "backend"]),
    DiagnosticCase(id="SSH-PORT-016", domain="ssh_remote_access", title_de="SSH-Port geschlossen", title_en="SSH port closed", summary_de="Port 22 antwortet nicht.", summary_en="Port 22 is not reachable.", severity="medium", confidence="high", detection_sources=["network", "config_check"], tags=["ssh"]),
    DiagnosticCase(id="SSH-DISABLED-017", domain="ssh_remote_access", title_de="SSH deaktiviert", title_en="SSH disabled", summary_de="SSH-Service ist nicht aktiviert.", summary_en="SSH service is disabled.", severity="medium", confidence="high", detection_sources=["systemctl", "config_check"], tags=["ssh"]),
    DiagnosticCase(id="DNS-018", domain="network", title_de="DNS-Aufloesung fehlerhaft", title_en="DNS resolution failing", summary_de="Namen koennen nicht in IPs aufgeloest werden.", summary_en="Hostnames cannot be resolved to IP addresses.", severity="medium", confidence="medium", detection_sources=["network", "api_result"], tags=["dns"]),
    DiagnosticCase(id="NET-IFACE-019", domain="network", title_de="Falsches Interface/IP", title_en="Wrong interface or IP", summary_de="Verbindungsversuch nutzt falsche Ziel-IP oder falsches Interface.", summary_en="Connection target uses wrong IP or wrong network interface.", severity="medium", confidence="medium", detection_sources=["network", "api_result"], tags=["ip"]),
    DiagnosticCase(id="FIREWALL-020", domain="security_hardening", title_de="Firewall blockiert Zugriff", title_en="Firewall blocks access", summary_de="Regeln blockieren benoetigte Verbindungen.", summary_en="Firewall rules block required traffic.", severity="high", confidence="medium", detection_sources=["config_check", "api_result"], tags=["firewall"]),
    DiagnosticCase(id="FS-RO-021", domain="storage_filesystem", title_de="Dateisystem read-only", title_en="Filesystem is read-only", summary_de="Zielmedium ist nur lesbar gemountet.", summary_en="Target medium is mounted read-only.", severity="high", confidence="high", detection_sources=["file_check"], tags=["filesystem"]),
    DiagnosticCase(id="FS-FULL-022", domain="storage_filesystem", title_de="Zielmedium voll", title_en="Target medium full", summary_de="Freier Speicher ist zu gering fuer Aktion.", summary_en="Insufficient free disk space for operation.", severity="high", confidence="high", detection_sources=["file_check"], tags=["storage"]),
    DiagnosticCase(id="OWNER-MODE-023", domain="permissions", title_de="Owner/Mode unpassend", title_en="Wrong owner or mode", summary_de="Pfad existiert, aber Owner/Mode weicht vom Modell ab.", summary_en="Path exists but owner/mode does not match expected model.", severity="medium", confidence="high", detection_sources=["file_check"], tags=["permissions"]),
    DiagnosticCase(id="PI-BOOT-024", domain="hardware_raspberry_pi", title_de="Pi bootet nicht sauber", title_en="Pi does not boot cleanly", summary_de="Bootmedium erkannt, aber Startpfad bricht ab.", summary_en="Boot medium detected but boot path fails.", severity="high", confidence="medium", detection_sources=["log_pattern", "api_result"], tags=["raspberry_pi", "boot"]),
    DiagnosticCase(id="PI-NVME-025", domain="hardware_raspberry_pi", title_de="NVMe/USB-Bootkontext unstimmig", title_en="NVMe/USB boot context mismatch", summary_de="Boot-Konfiguration passt nicht zum gewaehlten Medium.", summary_en="Boot configuration does not match selected boot medium.", severity="medium", confidence="medium", detection_sources=["config_check"], tags=["nvme", "usb"]),
    DiagnosticCase(id="PI-CONFIG-026", domain="hardware_raspberry_pi", title_de="Noetige Konfigurationsdatei fehlt", title_en="Required config file missing", summary_de="Pi-spezifische Konfiguration ist nicht vorhanden.", summary_en="Pi-specific configuration file is missing.", severity="medium", confidence="high", detection_sources=["file_check"], tags=["config"]),
    DiagnosticCase(id="UPDATES-027", domain="updates_packages", title_de="Paketquellen oder Updates fehlschlagen", title_en="Package updates failing", summary_de="APT/Update-Lauf endet mit Fehlern.", summary_en="APT/update execution fails.", severity="low", confidence="medium", detection_sources=["api_result", "log_pattern"], tags=["apt"]),
    DiagnosticCase(id="DOCKER-028", domain="docker_container_runtime", title_de="Container-Runtime nicht betriebsbereit", title_en="Container runtime not operational", summary_de="Docker/Container-Dienst ist nicht verfuegbar.", summary_en="Docker/container service is unavailable.", severity="medium", confidence="medium", detection_sources=["systemctl", "api_result"], tags=["docker"]),
    DiagnosticCase(id="LOGS-029", domain="logs_runtime", title_de="Nur Symptom, Root-Cause unklar", title_en="Symptom detected, root cause unclear", summary_de="Es gibt Fehleranzeichen, aber keine harte Root-Cause-Evidenz.", summary_en="There are error symptoms but no hard root-cause evidence.", severity="low", confidence="low", detection_sources=["log_pattern"], tags=["symptom"]),
    DiagnosticCase(id="APP-030", domain="app_setuphelfer_runtime", title_de="Setuphelfer Runtime unstabil", title_en="Setuphelfer runtime unstable", summary_de="Mehrere Signale zeigen einen instabilen Laufzeitzustand.", summary_en="Multiple signals indicate unstable runtime state.", severity="medium", confidence="medium", detection_sources=["api_result", "systemctl", "log_pattern"], tags=["runtime"]),
    DiagnosticCase(id="SYSTEMD-NNP-031", domain="systemd_services", title_de="NoNewPrivileges blockiert sudo", title_en="NoNewPrivileges blocks sudo", summary_de="Der Runtime-Kontext verhindert sudo-Ausfuehrung durch gesetztes no_new_privileges.", summary_en="Runtime context blocks sudo execution due to no_new_privileges.", severity="critical", confidence="high", detection_sources=["api_result", "systemctl", "log_pattern"], root_causes=["Zu restriktive Service-Sandboxing-Optionen"], recommended_actions=[_a("review-systemd-sandbox", 1, "Systemd-Optionen wie NoNewPrivileges/Restriktionen pruefen und reproduzierbar korrigieren.", "Review and correct systemd sandbox options such as NoNewPrivileges.")], tags=["systemd", "sudo", "no_new_privileges"]),
    DiagnosticCase(id="BACKUP-SOURCE-PERM-032", domain="backup_restore", title_de="Data-Backup enthält nicht lesbare Quellpfade", title_en="Data backup includes unreadable source paths", summary_de="Das Sicherungsziel funktioniert, aber type=data enthält Quellpfade ohne Leserechte im Dienstkontext.", summary_en="The data backup scope includes paths outside the service user context (e.g. /home/volker), so reads fail in runtime.", severity="high", confidence="high", detection_sources=["api_result", "file_check"], root_causes=["Data-Scope enthält root-only Pfade", "Data-Scope enthält Pfade außerhalb des Service-User-Kontexts"], recommended_actions=[_a("reduce-data-scope", 1, "Data-Quellen auf nicht-privilegierte Pfade begrenzen oder Backup-Typ anpassen.", "Reduce data sources to non-privileged paths or use a different backup type.")], tags=["backup", "permissions", "data_scope"]),
    DiagnosticCase(id="STORAGE-PROTECTION-001", domain="storage_filesystem", title_de="Schreibzugriff: Systemplatte blockiert", title_en="Write blocked: system disk", summary_de="Das Ziel liegt auf der Systemplatte (/) — Schreibzugriffe sind nicht erlaubt.", summary_en="Target is on the system disk (/) — writes are not allowed.", severity="critical", confidence="high", detection_sources=["api_result", "storage_protection"], destructive_risk=True, root_causes=["Backup-Pfad auf Root-Dateisystem", "Falsches Laufwerk gewaehlt"], recommended_actions=[_a("use-safe-mount", 1, "Nur unter /mnt/setuphelfer/… oder freigegebenen Praefixen sichern.", "Use only /mnt/setuphelfer/… or configured safe prefixes.")], tags=["storage", "write_protection", "system_disk"]),
    DiagnosticCase(id="STORAGE-PROTECTION-002", domain="storage_filesystem", title_de="Schreibzugriff: Boot-Medium blockiert", title_en="Write blocked: boot disk", summary_de="Ziel enthaelt /boot oder EFI — Schreibzugriffe sind nicht erlaubt.", summary_en="Target involves /boot or EFI — writes are not allowed.", severity="critical", confidence="high", detection_sources=["api_result", "storage_protection"], destructive_risk=True, tags=["storage", "write_protection", "boot"]),
    DiagnosticCase(id="STORAGE-PROTECTION-003", domain="storage_filesystem", title_de="Schreibzugriff: Fremdes OS (Windows) blockiert", title_en="Write blocked: foreign OS (Windows)", summary_de="Windows-/NTFS-Heuristik oder EFI/Microsoft erkannt — Schreibzugriffe sind nicht erlaubt.", summary_en="Windows/NTFS heuristics or EFI/Microsoft detected — writes are not allowed.", severity="critical", confidence="medium", detection_sources=["api_result", "storage_protection"], destructive_risk=True, tags=["storage", "write_protection", "windows"]),
    DiagnosticCase(id="STORAGE-PROTECTION-004", domain="storage_filesystem", title_de="Schreibzugriff: Ziel nicht auf Allowlist", title_en="Write blocked: not allowlisted", summary_de="Pfad oder Blockgeraet entspricht nicht den freigegebenen Mustern.", summary_en="Path or block device does not match allowed patterns.", severity="critical", confidence="high", detection_sources=["api_result", "storage_protection"], tags=["storage", "write_protection", "allowlist"]),
    DiagnosticCase(id="STORAGE-PROTECTION-005", domain="storage_filesystem", title_de="Schreibzugriff: unsicherer Mount-Baum", title_en="Write blocked: unsafe mount tree", summary_de="Ziel liegt unter /media oder /run/media, aber nicht auf einem sicheren lokalen Blockgeraet-Mount.", summary_en="Target is under /media or /run/media but not on a safe local block-device mount.", severity="critical", confidence="high", detection_sources=["api_result", "storage_protection"], tags=["storage", "write_protection", "automount"]),
    DiagnosticCase(
        id="STORAGE-PROTECTION-006",
        domain="storage_filesystem",
        title_de="Schreibziel: Traverse unter /media blockiert",
        title_en="Write target: traverse under /media denied",
        summary_de="Der Dienst kann den Pfad unter /media oder /run/media nicht traversieren; eine Mount-Ermittlung wuerde sonst irrefuehrend auf die Systemplatte fallen.",
        summary_en="The service cannot traverse the path under /media or /run/media; mount resolution would misleadingly map to the system disk.",
        severity="critical",
        confidence="high",
        detection_sources=["api_result", "storage_protection"],
        destructive_risk=True,
        root_causes=["Fehlende Traverse-Rechte auf Zwischenverzeichnissen (z. B. /media/user)", "Owner/Modus des Einhaengepunkts"],
        recommended_actions=[
            _a(
                "fix-media-traverse",
                1,
                "Traverse fuer den Dienstnutzer sicherstellen (Betrieb) oder Betreiber-Praefix pruefen — keine automatische ACL durch das Produkt.",
                "Ensure service-user traverse permissions (operator) or verify mount prefix — no automatic ACL from the product.",
            )
        ],
        tags=["storage", "permissions", "traverse", "media"],
    ),
    DiagnosticCase(
        id="SERVICE-CONFLICT-033",
        domain="systemd_services",
        title_de="Alte pi-installer-Instanz blockiert Setuphelfer",
        title_en="Legacy pi-installer instance blocks Setuphelfer",
        summary_de="pi-installer.service (oder -backend) ist aktiv und kollidiert mit dem Setuphelfer-Backend auf Port 8000.",
        summary_en="pi-installer.service (or -backend) is active and collides with the Setuphelfer backend on port 8000.",
        severity="high",
        confidence="high",
        detection_sources=["systemctl", "log_pattern"],
        recommended_actions=[
            _a("stop-legacy-pi-installer", 1, "sudo systemctl stop pi-installer.service pi-installer-backend.service && sudo systemctl disable pi-installer.service pi-installer-backend.service", "sudo systemctl stop pi-installer.service pi-installer-backend.service && sudo systemctl disable pi-installer.service pi-installer-backend.service"),
        ],
        tags=["service_conflict", "pi_installer", "port_8000"],
        related_docs=["docs/knowledge-base/diagnostics/SERVICE_CONFLICTS.md"],
        related_faq=["docs/faq/SERVICE_CONFLICT_FAQ.md"],
    ),
    DiagnosticCase(
        id="SERVICE-CONFLICT-034",
        domain="systemd_services",
        title_de="Port 8000 wird von falschem Dienst belegt",
        title_en="Port 8000 is owned by the wrong service",
        summary_de="TCP :8000 lauscht ein Prozess, der nicht zur erwarteten Setuphelfer-Installation gehoert (z. B. archivierter Baum unter /opt, historischer Ordnername pi-installer).",
        summary_en="Something other than the expected Setuphelfer install is listening on TCP :8000 (e.g. archived legacy tree under /opt, historical folder name pi-installer).",
        severity="high",
        confidence="high",
        detection_sources=["api_result", "systemctl"],
        recommended_actions=[
            _a("inspect-listener", 1, "ss -tlnp | grep :8000; falschen Dienst stoppen oder PI_INSTALLER_BACKEND_PORT setzen.", "ss -tlnp | grep :8000; stop the wrong service or set PI_INSTALLER_BACKEND_PORT."),
        ],
        tags=["service_conflict", "port_8000"],
        related_docs=["docs/knowledge-base/diagnostics/SERVICE_CONFLICTS.md"],
        related_faq=["docs/faq/SERVICE_CONFLICT_FAQ.md"],
    ),
    DiagnosticCase(
        id="SERVICE-CONFLICT-035",
        domain="systemd_services",
        title_de="Gemischte Alt-/Neuinstallation erkannt",
        title_en="Mixed legacy and new installation detected",
        summary_de="Der historische Legacy-Baum unter /opt (Ordner pi-installer) und /opt/setuphelfer sind parallel vorhanden; alte systemd-Units sind noch enabled oder aktiv.",
        summary_en="The historical legacy tree under /opt (folder pi-installer) coexists with /opt/setuphelfer; legacy systemd units are still enabled or active.",
        severity="medium",
        confidence="high",
        detection_sources=["systemctl", "file_check"],
        recommended_actions=[
            _a("disable-legacy", 1, "Legacy-Dienste stoppen/disable; archivierte Daten unter /opt nicht automatisch loeschen.", "Stop/disable legacy services; do not auto-delete archived data under /opt."),
        ],
        tags=["service_conflict", "migration"],
        related_docs=["docs/knowledge-base/diagnostics/SERVICE_CONFLICTS.md"],
        related_faq=["docs/faq/SERVICE_CONFLICT_FAQ.md"],
    ),
    DiagnosticCase(
        id="SERVICE-CONFLICT-036",
        domain="systemd_services",
        title_de="Aeltere Version darf neuere Installation nicht ueberschreiben",
        title_en="Older install must not overwrite newer Setuphelfer",
        summary_de="Start aus dem archivierten Legacy-Baum (Ordner pi-installer unter /opt), waehrend unter /opt/setuphelfer eine neuere Version liegt.",
        summary_en="Starting from the archived legacy tree (pi-installer folder under /opt) while a newer version is present under /opt/setuphelfer.",
        severity="critical",
        confidence="high",
        detection_sources=["file_check", "api_result"],
        recommended_actions=[
            _a("use-opt-setuphelfer", 1, "Nur setuphelfer-backend unter /opt/setuphelfer starten; alte pi-installer-Instanz nicht fuer Deploys nutzen.", "Run only setuphelfer-backend under /opt/setuphelfer; do not deploy from the old pi-installer tree."),
        ],
        destructive_risk=False,
        tags=["service_conflict", "version"],
        related_docs=["docs/knowledge-base/diagnostics/SERVICE_CONFLICTS.md"],
        related_faq=["docs/faq/SERVICE_CONFLICT_FAQ.md"],
    ),
    DiagnosticCase(
        id="SYSTEMD-MEMORYMAX-037",
        domain="systemd_services",
        title_de="Zu kleines MemoryMax fuer Verify/Preview",
        title_en="MemoryMax too low for verify/preview",
        summary_de="systemd cgroup MemoryMax/MemorySwapMax begrenzt den Backend-Prozess; grosse Verify/Preview-Laeufe enden mit OOM oder Abbruch.",
        summary_en="systemd cgroup MemoryMax/MemorySwapMax caps the backend; large verify/preview runs hit OOM or abort.",
        severity="high",
        confidence="medium",
        detection_sources=["systemctl", "log_pattern", "api_result"],
        root_causes=["Restriktives MemoryMax in Unit-Drop-in", "Zu wenig wirksamer RAM fuer Staging"],
        recommended_actions=[
            _a("raise-memorymax", 1, "MemoryMax/MemorySwapMax in setuphelfer-backend.service.d erhoehen, daemon-reload, Dienst neu starten.", "Raise MemoryMax/MemorySwapMax in setuphelfer-backend.service.d, daemon-reload, restart service."),
        ],
        related_docs=["docs/knowledge-base/BACKUP_VERIFY_PREVIEW_RUNTIME.md"],
        related_faq=["docs/faq/BACKUP_RESTORE_FAQ_DE.md", "docs/faq/BACKUP_RESTORE_FAQ_EN.md"],
        tags=["systemd", "cgroup", "oom", "verify"],
    ),
    DiagnosticCase(
        id="VERIFY-STAGING-038",
        domain="backup_restore",
        title_de="Deep-Verify Integritaet (Staging/Symlinks)",
        title_en="Deep verify integrity (staging/symlinks)",
        summary_de="verify_integrity_failed durch Staging-Regeln oder Symlinks im Archiv, oft bei Full-Root-Backups ohne Mediumfehler.",
        summary_en="verify_integrity_failed due to staging rules or symlinks, often on full-root archives without media corruption.",
        severity="medium",
        confidence="medium",
        detection_sources=["api_result"],
        root_causes=["Absolute oder aus Staging-Sicht unsichere Symlink-Ziele", "Full-Archive mit Sonderfaellen"],
        recommended_actions=[
            _a("context-verify", 1, "Basic-Verify nutzen, Archivtyp pruefen, technische Notiz lesen.", "Use basic verify, validate archive type, read technical note."),
        ],
        related_docs=["docs/knowledge-base/BACKUP_VERIFY_PREVIEW_RUNTIME.md", "docs/knowledge-base/BACKUP_RECOVERY_FILE_ENGINE_REALITY.md"],
        related_faq=["docs/faq/BACKUP_RESTORE_FAQ_DE.md", "docs/faq/BACKUP_RESTORE_FAQ_EN.md"],
        tags=["verify", "integrity", "symlink", "staging"],
    ),
    DiagnosticCase(
        id="RESCUE-BUILD-ROOT-001",
        domain="rescue_build",
        title_de="Rescue-ISO-Build benötigt kontrollierte Root-Ausführung",
        title_en="Rescue ISO build requires controlled root execution",
        summary_de="Der kontrollierte Rescue-ISO-Build wurde nicht wegen Toolchain oder rsvg blockiert, sondern weil keine sichere Root-Ausführung verfügbar war.",
        summary_en="The controlled rescue ISO build was blocked by missing safe root execution, not by toolchain or rsvg issues.",
        severity="high",
        confidence="high",
        detection_sources=["api_result", "log_pattern", "manual_test"],
        root_causes=[
            "Build läuft ohne echtes Operator-Terminal",
            "Keine eng begrenzte sudo-Allowlist oder Root-Helper-Policy verfügbar",
        ],
        recommended_actions=[
            _a(
                "manual-operator-terminal",
                1,
                "Kontrollierten Rescue-Build aus einem echten Operator-Terminal mit sudo-Rechten starten oder eine dokumentierte eng begrenzte Operator-Policy vorbereiten. Keine Passwortweitergabe über stdin, kein globales NOPASSWD, kein Gate-Bypass.",
                "Run the controlled rescue build from a real operator terminal with sudo privileges or prepare a documented narrowly allowlisted operator policy. Do not pass passwords through stdin, do not use broad NOPASSWD rules, and do not bypass the gate.",
            )
        ],
        related_docs=[
            "docs/knowledge-base/diagnostics/RESCUE_BUILD_DIAGNOSTICS.md",
            "docs/runbooks/RESCUE_CONTROLLED_ISO_BUILD_RUNBOOK.md",
            "docs/knowledge-base/recovery/RESCUE_ISO_CONTROLLED_BUILD_GATE.md",
        ],
        related_faq=["docs/faq/rescue_iso_build_faq.md"],
        tags=["rescue_build", "operator_policy", "safety_gate", "sudo"],
        status_mapping={"blocked_requires_operator_sudo_policy": "warning"},
    ),
    DiagnosticCase(
        id="RESCUE-BUILD-GATE-001",
        domain="rescue_build",
        title_de="Direkter lb build wurde durch kontrolliertes Build-Gate blockiert",
        title_en="Direct lb build was blocked by the controlled build gate",
        summary_de="Der direkte lb-build-Aufruf wurde absichtlich vom kontrollierten `auto/build`-Gate mit Exit 20 gestoppt.",
        summary_en="The direct lb build invocation was intentionally stopped by the controlled `auto/build` gate with exit 20.",
        severity="medium",
        confidence="high",
        detection_sources=["api_result", "log_pattern", "manual_test"],
        root_causes=["Direkter `lb build` statt kontrolliertem Wrapper/noauto-Pfad"],
        recommended_actions=[
            _a(
                "use-controlled-gate",
                1,
                "Nur den dokumentierten kontrollierten Buildpfad mit Wrapper, `./auto/config` und `lb build noauto` verwenden.",
                "Use only the documented controlled build path with the wrapper, `./auto/config`, and `lb build noauto`.",
            )
        ],
        related_docs=[
            "docs/knowledge-base/diagnostics/RESCUE_BUILD_DIAGNOSTICS.md",
            "docs/knowledge-base/recovery/RESCUE_ISO_CONTROLLED_BUILD_GATE.md",
        ],
        related_faq=["docs/faq/rescue_iso_build_faq.md"],
        tags=["rescue_build", "safety_gate", "auto_build", "lb_build"],
        status_mapping={"blocked_controlled_build_gate_required": "warning"},
    ),
    DiagnosticCase(
        id="RESCUE-BUILD-TOOL-001",
        domain="rescue_build",
        title_de="Host-Build-Abhängigkeit für SVG-Konvertierung fehlt oder ist unvollständig",
        title_en="Host build dependency for SVG conversion is missing or incomplete",
        summary_de="Der Rescue-Build scheitert bereits vor dem eigentlichen ISO-Lauf, weil `rsvg-convert` oder das dokumentierte Host-Paket `librsvg2-bin` fehlen.",
        summary_en="The rescue build fails before the actual ISO run because `rsvg-convert` or the documented host package `librsvg2-bin` is missing.",
        severity="medium",
        confidence="high",
        detection_sources=["api_result", "log_pattern", "manual_test"],
        root_causes=[
            "Host-Paket `librsvg2-bin` ist nicht installiert",
            "`rsvg-convert` fehlt im Build-Host-Kontext",
        ],
        recommended_actions=[
            _a(
                "install-documented-rsvg-tooling",
                1,
                "Installiere die dokumentierte Host-Build-Abhängigkeit `librsvg2-bin`. Setuphelfer installiert sie nicht automatisch.",
                "Install the documented host build dependency `librsvg2-bin`. Setuphelfer does not install it automatically.",
            )
        ],
        related_docs=[
            "docs/knowledge-base/diagnostics/RESCUE_BUILD_DIAGNOSTICS.md",
            "docs/evidence/rescue/RESCUE_CONTROLLED_LIVE_BUILD_TOOL_CHECK.md",
        ],
        related_faq=["docs/faq/rescue_iso_build_faq.md"],
        tags=["rescue_build", "host_dependency", "svg", "rsvg_convert"],
        status_mapping={"blocked_build_tools_missing": "warning"},
    ),
    DiagnosticCase(
        id="RESCUE-BUILD-RSVG-001",
        domain="rescue_build",
        title_de="Legacy-rsvg-Erwartung durch live-build erkannt",
        title_en="Legacy rsvg expectation detected from live-build",
        summary_de="`rsvg-convert` ist zwar vorhanden, aber live-build erwartet den Legacy-Befehl `rsvg`; dafür ist ein projektlokaler Kompatibilitätswrapper erforderlich.",
        summary_en="`rsvg-convert` is present, but live-build expects the legacy `rsvg` command; this requires a project-local compatibility wrapper.",
        severity="medium",
        confidence="high",
        detection_sources=["api_result", "log_pattern", "manual_test"],
        root_causes=[
            "live-build referenziert weiterhin `/usr/bin/rsvg`",
            "Nur `rsvg-convert` ist vorhanden, aber kein projektlokaler Wrapper",
        ],
        recommended_actions=[
            _a(
                "use-project-local-rsvg-wrapper",
                1,
                "Nutze den projektlokalen `rsvg`-Kompatibilitätswrapper. Kein globaler Symlink nach `/usr/bin/rsvg`.",
                "Use the project-local `rsvg` compatibility wrapper. Do not create a global symlink at `/usr/bin/rsvg`.",
            )
        ],
        related_docs=[
            "docs/knowledge-base/diagnostics/RESCUE_BUILD_DIAGNOSTICS.md",
            "docs/knowledge-base/recovery/RESCUE_ISO_CONTROLLED_BUILD_GATE.md",
        ],
        related_faq=["docs/faq/rescue_iso_build_faq.md"],
        tags=["rescue_build", "compatibility", "legacy_rsvg", "live_build"],
        status_mapping={"blocked_legacy_rsvg_command_missing": "warning"},
    ),
    DiagnosticCase(
        id="RESCUE-BUILD-ISOHYBRID-001",
        domain="rescue_build",
        title_de="isohybrid fehlt in der live-build Binary-Stage",
        title_en="isohybrid missing in live-build binary stage",
        summary_de="Nach genisoimage scheitert `binary.sh` mit `isohybrid: not found`. Debian liefert `isohybrid` in `syslinux-utils`; die Binary-Paketliste muss es für den Chroot enthalten.",
        summary_en="After genisoimage, `binary.sh` fails with `isohybrid: not found`. Debian ships `isohybrid` in `syslinux-utils`; the binary package list must include it for the chroot.",
        severity="medium",
        confidence="high",
        detection_sources=["api_result", "log_pattern", "manual_test"],
        root_causes=[
            "live-build iso-hybrid installiert nur `syslinux`, nicht `syslinux-utils`",
            "Fehlende `config/package-lists/setuphelfer.list.binary` mit `syslinux-utils`",
        ],
        recommended_actions=[
            _a(
                "add-syslinux-utils-binary-package-list",
                1,
                "Führe `prepare-controlled-live-build-tree.sh` aus (legt `setuphelfer.list.binary` mit `syslinux-utils` an), dann `./auto/clean` und Build-Retry. Optional auf dem Host: `sudo apt install syslinux-utils` — Setuphelfer installiert nicht automatisch.",
                "Run `prepare-controlled-live-build-tree.sh` (creates `setuphelfer.list.binary` with `syslinux-utils`), then `./auto/clean` and retry the build. Optional on host: `sudo apt install syslinux-utils` — Setuphelfer does not install automatically.",
            )
        ],
        related_docs=[
            "docs/knowledge-base/diagnostics/RESCUE_BUILD_DIAGNOSTICS.md",
            "docs/evidence/runtime-results/rescue/RESCUE_ISO_ISOHYBRID_FAILURE.md",
            "docs/runbooks/RESCUE_CONTROLLED_ISO_BUILD_RUNBOOK.md",
        ],
        related_faq=["docs/faq/rescue_iso_build_faq.md"],
        tags=["rescue_build", "syslinux", "isohybrid", "binary_stage"],
        status_mapping={"RESCUE-BUILD-ISOHYBRID-001": "warning"},
    ),
    DiagnosticCase(
        id="RESCUE-BUILD-ARCH-001",
        domain="rescue_build",
        title_de="Zielarchitektur nicht durch aktuellen Rescue-Build abgedeckt",
        title_en="Target architecture is not covered by the current rescue build track",
        summary_de="Der aktuelle Rescue-Build-Pfad deckt nur `amd64` als aktiven x86-Track ab; `i386` bleibt ein separater Review-Track und `arm64`/`armhf` bleiben getrennte ARM-Pfade.",
        summary_en="The current rescue build path only covers `amd64` as the active x86 track; `i386` remains a separate review track and `arm64`/`armhf` remain separate ARM tracks.",
        severity="medium",
        confidence="high",
        detection_sources=["api_result", "manual_test"],
        root_causes=["Architekturmatrix trennt x86-ISO und ARM-Image-Pfade bewusst"],
        recommended_actions=[
            _a(
                "review-architecture-track",
                1,
                "Nur `amd64` als aktuellen ISO-Track behandeln; `i386` separat reviewen und ARM als eigene Image-/Provisioning-Tracks dokumentieren.",
                "Treat only `amd64` as the current ISO track; review `i386` separately and document ARM as dedicated image/provisioning tracks.",
            )
        ],
        related_docs=[
            "docs/knowledge-base/diagnostics/RESCUE_BUILD_DIAGNOSTICS.md",
            "docs/architecture/RESCUE_TARGET_ARCHITECTURE_MATRIX.md",
            "docs/knowledge-base/recovery/RESCUE_TARGET_ARCHITECTURES.md",
        ],
        related_faq=["docs/faq/rescue_iso_build_faq.md"],
        tags=["rescue_build", "architecture", "amd64", "i386", "arm64", "armhf"],
    ),
    DiagnosticCase(
        id="NOTIFICATION-EMAIL-PROVIDER-001",
        domain="notification",
        title_de="E-Mail-Benachrichtigung durch Provider-Limit blockiert",
        title_en="Email notification is blocked by a provider limit",
        summary_de="Die Dashboard-Benachrichtigung ist sichtbar, aber der SMTP-Provider verweigert die E-Mail wegen eines Versandlimits.",
        summary_en="The dashboard notification is visible, but the SMTP provider rejects the email because of an outgoing message limit.",
        severity="medium",
        confidence="high",
        detection_sources=["api_result", "log_pattern", "manual_test"],
        root_causes=[
            "SMTP-Provider-Limit überschritten",
            "Kontingent oder Versandwartezeit des Providers aktiv",
        ],
        recommended_actions=[
            _a(
                "check-provider-limit",
                1,
                "SMTP-Provider-Limit prüfen, Wartezeit einhalten oder Provider-/Kontingentkonfiguration anpassen. Dashboard-Status darf grün bleiben, während E-Mail `provider_limit` bleibt.",
                "Check the SMTP provider limit, wait as required, or adjust provider/quota settings. The dashboard status may stay green while email remains `provider_limit`.",
            )
        ],
        related_docs=[
            "docs/knowledge-base/dev-dashboard/NOTIFICATIONS.md",
            "docs/evidence/dev-dashboard/NOTIFICATION_MODULE_INTEGRATION_RESULT.md",
        ],
        related_faq=["docs/faq/notifications_de.md", "docs/faq/notifications_en.md"],
        tags=["notification", "email", "provider_limit"],
        status_mapping={
            "notification.email.provider_limit_exceeded": "warning",
            "provider_limit": "warning",
        },
    ),
]


def get_catalog() -> list[DiagnosticCase]:
    return DIAGNOSTIC_CATALOG


def get_case_by_id(diagnosis_id: str) -> DiagnosticCase | None:
    for item in DIAGNOSTIC_CATALOG:
        if item.id == diagnosis_id:
            return item
    return None
