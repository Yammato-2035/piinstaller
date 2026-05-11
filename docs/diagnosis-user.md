# Diagnosehinweise in der Oberfläche (Kurz)

## Was du siehst

An einigen Stellen erscheint ein Kasten **„Diagnose“** mit einer kurzen Erklärung und **empfohlenen nächsten Schritten**. Technische Details kannst du optional einblenden.

## Was das leistet

- Fasst typische Fehler (z. B. Server nicht erreichbar, Firewall-Regel schlägt fehl) in verständlicher Sprache zusammen.
- Ersetzt **keine** Logs, Support-Bundles oder die fachlichen Prüfungen bei **Backup und Wiederherstellung**.

## Was es nicht leistet

- Keine Garantie für die exakte Ursache.
- Keine automatische Reparatur ohne deine Bestätigung (Phase 1 bietet vor allem Erklärung und Schritte).

Bei Backup/Restore weiterhin die offiziellen Prüf- und Restore-Abläufe nutzen.

**Verify (Backup prüfen):** Schlägt die Prüfung fehl, kann zusätzlich ein Diagnosekasten erscheinen. Er **ersetzt** keine technische Auswertung des Archivs und **bietet keine automatische Reparatur oder Wiederherstellung** – nur Erklärung und sinnvolle nächste Schritte.

**Verify / Restore-Preview und Ressourcen:** Wenn die Meldung auf **wenig Platz unter `/tmp`** oder **PrivateTmp** hindeutet, oder das Backend bei großen Läufen mit **Speicherlimits (systemd `MemoryMax`)** aussteigt, beschreibt die Wissensdatenbank die typischen Ursachen und sinnvollen Einstellungen (`docs/knowledge-base/BACKUP_VERIFY_PREVIEW_RUNTIME.md`). Zugehörige Diagnose-IDs im Katalog: z. B. `RESTORE-TMPFS-007`, `SYSTEMD-MEMORYMAX-037`, `VERIFY-STAGING-038`.

**Webserver konfigurieren:** Wenn die Konfiguration fehlschlägt und die Meldung auf einen **belegten Port** hindeutet, erscheint eine passende Erklärung. Es wird **kein** Dienst automatisch gestoppt oder der Port nicht automatisch geändert.
