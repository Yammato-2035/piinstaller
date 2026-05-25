# Setuphelfer Privileged Deploy Helper

## Grundsatz

Der normale Setuphelfer-Backendprozess bleibt unprivilegiert.  
Root-Aktionen laufen ausschliesslich ueber einen vordefinierten `systemd`-Oneshot-Service.

Der Backend-Prozess darf:

- Deploy-Drift lesen
- Helper-Status lesen
- einen kontrollierten Deploy **anfordern**

Der Backend-Prozess darf **nicht**:

- direkt `deploy-to-opt.sh` ausfuehren
- beliebige Root-Kommandos starten
- freie Shell-Strings aus User-Input an Root durchreichen

## Erlaubte Aktionen des Helpers

Der Helper darf ausschliesslich den eng definierten Deploy-Workflow ausfuehren:

- validierten Workspace nach `/opt/setuphelfer` deployen
- Deploy-Manifest erzeugen oder pruefen
- `setuphelfer-backend.service` neu starten
- `setuphelfer.service` neu starten
- Runtime-Gate nach Deploy ausfuehren
- Logs schreiben

## Verbotene Aktionen

Der Helper darf **nicht**:

- beliebige Shellbefehle ausfuehren
- `apt install` oder `apt upgrade` ausfuehren
- `dd` ausfuehren
- `mkfs` ausfuehren
- `parted` ausfuehren
- `mount` oder `umount` ausfuehren
- Backup starten
- Restore starten
- USB-Write ausfuehren
- auf beliebige Zielpfade schreiben
- Safety-Gates aendern oder umgehen

## Sicherheitsanforderungen

- Workspace-Pfad ist fest oder explizit allowlisted.
- Kein Pfad aus freiem User-Input.
- Lockfile verhindert parallele Deploys.
- Exit-Code und Logs werden persistent geschrieben.
- Bei Fehlern wird ein Rollback-Hinweis dokumentiert; es wird kein Erfolg vorgetaeuscht.
- Das Dashboard zeigt niemals "fake green".

## Architekturfluss

1. Dashboard erkennt `deploy_drift`.
2. Backend liest nur Status (`deploy_job_state`, Runtime-Gate, Update-Status).
3. Operator bestaetigt den kontrollierten Deploy im UI.
4. Backend versucht ausschliesslich:
   - `systemctl start setuphelfer-deploy-helper.service`
5. Die systemd-Unit startet das Root-Skript:
   - `/opt/setuphelfer/scripts/setuphelfer-deploy-helper-root.sh --workspace /home/volker/piinstaller`
6. Das Root-Skript validiert:
   - Root-Kontext
   - allowlisted Workspace
   - Git-Repo
   - vorhandenes `scripts/deploy-to-opt.sh`
7. Das Root-Skript fuehrt den festen Deploy aus, schreibt:
   - `/var/lib/setuphelfer/deploy-jobs/latest.json`
   - `/var/lib/setuphelfer/deploy-jobs/latest.log`
8. Danach liest das Dashboard nur noch den persistierten Status.

## Persistente Statusdaten

Der Deploy-Pfad nutzt zwei dashboard-lesbare Dateien:

- `latest.json`: letzter Jobstatus, Exit-Codes, Runtime-Gate vor/nach Deploy
- `latest.log`: letzter Log-Stream, redigiert fuer UI-Anzeige

Fuer Tests darf auf `build/dev-dashboard/deploy-jobs/` ausgewichen werden, wenn `/var/lib/setuphelfer` nicht beschreibbar ist.

## Fehler- und Rollback-Hinweis

Der Helper selbst fuehrt **keinen** automatischen Rollback aus. Stattdessen gilt:

- Fehlerstatus bleibt persistent sichtbar
- Runtime-Gate wird nach dem Versuch erneut bewertet
- das Dashboard zeigt `failed`, `blocked` oder `operator_required`
- ein manueller Rollback oder erneuter Deploy muss bewusst durch den Operator erfolgen

Damit bleibt die Root-Aktion eng begrenzt, nachvollziehbar und mit dem bestehenden Safety-Gate-Modell kompatibel.
