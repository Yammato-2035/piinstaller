# FAQ: Service-Konflikte (pi-installer vs. Setuphelfer)

## Warum darf pi-installer nicht parallel zu Setuphelfer laufen?

**DE:** Beide bringen ein Backend auf **Port 8000**. Welcher Prozess antwortet, haengt dann vom Zufall ab — API-Tests, Backups und Diagnosen beziehen sich auf die **falsche** Codebasis.

**EN:** Both stacks expose a backend on **port 8000**. Which process answers becomes nondeterministic, so API tests, backups, and diagnostics may target the **wrong** codebase.

---

## Warum blockiert Setuphelfer bei alter Version / falschem Listener?

**DE:** Ein Start soll **keine stillschweigende Mischung** aus Alt- (`/opt/pi-installer`) und Neu-Installation (`/opt/setuphelfer`) erzeugen. `scripts/start-backend.sh` und optional `python -m uvicorn` pruefen deshalb Listener und Pfade, bevor gebunden wird. Es wird **nichts** per API gekillt — bei Konflikt gibt es eine klare Meldung und Exit-Code.

**EN:** Startup must not create a **silent mix** of legacy (`/opt/pi-installer`) and current (`/opt/setuphelfer`) stacks. `scripts/start-backend.sh` (and `python -m uvicorn` when used) checks listeners/paths before binding. **Nothing** is killed via the API; conflicts yield a clear message and exit code.

---

## Warum wird `/opt/pi-installer` nicht automatisch geloescht?

**DE:** Dort koennen noch Konfigurationen, Skripte oder manuelle Anpassungen liegen. Automatisches Loeschen waere **destruktiv** und nicht rückversicherbar. Stattdessen: Dienste stoppen/disable, Daten bei Bedarf **manuell** pruefen und archivieren.

**EN:** That tree may still hold configs, scripts, or manual tweaks. Auto-deletion would be **destructive** and hard to recover. Prefer stopping/disabling services and **manually** reviewing/archiving data if needed.
