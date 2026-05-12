# TODO: REAL-DATA-HOME-BACKUP

Geplanter Ausbau: **kontrolliert** echte Nutzerdaten aus dem Home-Baum sichern, ohne implizite Vollrechte oder Datenverlust-Risiken durch „magisches“ Verhalten.

**Status:** Nur Planung; **keine** Produktiv-Freigabe, bis die Voraussetzungen unten erfüllt und dokumentiert sind.

---

## Ziel

Später (nach Freigabe) dürfen ausgewählte, **explizit benannte** Pfade unter `/home` (oder darunter) in den Daten-Backup-Flow einbezogen werden – mit klarer Nutzerfreigabe, nachvollziehbarer Diagnose bei Rechtefehlern und ohne automatisches Einsammeln fremder Konten.

---

## Voraussetzungen (hart)

| # | Kriterium | Hinweis |
|---|-----------|---------|
| 1 | **HW1-01** bestanden | E2E unverschlüsselt, stabile Ziel-/Quellkonfiguration (siehe Matrix / `HW_EXEC_1_EXTERNAL_NVME_REPORT.md`). |
| 2 | **HW1-02** bestanden | Verschlüsselungspfad (Create/Verify/Preview + Negativtests) stabil. |
| 3 | **HW1-03** Fehlerfälle sauber | Verify-Fehlerpfade deterministisch, keine widersprüchlichen `status`/`severity`-Kombinationen, Evidence nachvollziehbar. |
| 4 | **Restore/Preview** stabil | Sandbox, Entschlüsselung wo nötig, keine stillen Teil-Erfolge. |
| 5 | **Klare Benutzerfreigabe** | UI oder verbindlicher Schritt (z. B. Bestätigungsdialog + dokumentierte Konsequenzen), nicht nur versteckte Konfiguration. |

Solange ein Punkt fehlt, bleibt `/home` außerhalb des unterstützten Real-Data-Scopes bzw. nur über die heute gültigen Mechanismen (siehe Regeln).

---

## Regeln (Nicht verhandelbar)

1. **Kein automatisches `/home/*`-Scanning** – keine Enumeration von Benutzern, keine „alle Homes“. Auswahl nur über explizite Konfiguration/API-Felder.
2. **Keine fremden Homes** – kein implizites `/home/<anderer-nutzer>`; nur Pfade, die zur Freigabe passen (z. B. nur das Home des einwilligenden Nutzers, technisch strikt validiert).
3. **Keine root-only-Bereiche** im nicht-privilegierten `type=data`-Pfad – kein Umgehen von `ProtectHome`, kein sudo-Tar für den Standard-Data-Backup; wer Root-Umfang braucht, bleibt beim dokumentierten Full-/Recovery-Pfad mit eigenen Gates.
4. **Explizite Pfadauswahl** – jede Quelle benannt und allowlist-konform (bestehende `/mnt/setuphelfer`-Logik und Erweiterungen nur bewusst und reviewbar).
5. **Datenschutz- und Rechteprüfung** – vor dem ersten Backup: Lesbarkeit, Gruppenmodell, keine personenbezogenen Überraschungen (Logging ohne Inhalte, keine Passwörter in Evidence).
6. **Diagnose bei Permission-Problemen** – strukturierte Antworten (z. B. bestehende Codes wie `backup.source_permission_denied` / `BACKUP-SOURCE-PERM-032`), keine generischen 500er.

---

## Architektur-Bezug (heute)

- **`type=data`** plant Quellen über `_plan_data_backup_sources()` / `SETUPHELFER_DATA_BACKUP_SOURCES` (kontrollierter HW-Pfad unter `/mnt/setuphelfer/...`). Siehe auch `docs/faq/STORAGE_PROTECTION_FAQ.md` (Abschnitt zu `/home` und Service-Kontext).
- **Katalog:** `docs/knowledge-base/diagnostics/DIAGNOSIS_CATALOG.md` (u. a. Data-Scope außerhalb Service-Kontext).
- **Engines-Überblick:** `docs/developer/BACKUP_RECOVERY_ENGINES.md`.

---

## Offene Arbeitspakete (grobe Reihenfolge)

1. Anforderungs- und Threat-Review (Datenschutz, Multi-User, `ProtectHome`, verschlüsselte Homes).
2. API-/UI-Spezifikation: explizite Quellliste, Validierung, Freigabe-UX, Fehlercodes.
3. Implementierung + Tests (inkl. Negative: nicht lesbar, nicht erlaubt, Symlink außerhalb).
4. HW- oder Pilot-Evidence mit realem Home nur nach schriftlicher Nutzerfreigabe.
5. Doku (FAQ, Execution-Guide) und Matrix-Eintrag, falls neuer Testfall.

---

## Absichtlich nicht Ziel dieses TODO

- Vollautomatisches „Sichern aller Benutzer“.
- Erweiterung der Storage-Allowlist ohne separates Sicherheits-Review.
- Umgehung von `NoNewPrivileges` / systemd-Härtung für den Standard-Datenbackup.
