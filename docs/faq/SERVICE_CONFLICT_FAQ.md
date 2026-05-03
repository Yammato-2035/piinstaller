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

---

## Warum oeffnet "Update im Terminal" manchmal kein sichtbares Terminal?

**DE:** Der Backend-Dienst laeuft unter `systemd` haeufig ohne GUI-Session (`DISPLAY`/`WAYLAND` fehlen). Dann kann er kein sichtbares Desktop-Terminal starten. Die API liefert in dem Fall bewusst eine klare Meldung mit manuellem Befehl. In der Tauri-App wird zusaetzlich ein lokaler Fallback genutzt, der das Terminal direkt aus der Desktop-Session startet.

**EN:** The backend service often runs under `systemd` without a GUI session (`DISPLAY`/`WAYLAND` missing). In that case it cannot spawn a visible desktop terminal. The API deliberately returns a clear message with a manual command. In the Tauri app, an additional local fallback starts the terminal from the desktop session directly.

---

## Warum lief bei Tauri frueher ein nicht schliessbares Terminal mit?

**DE:** Einige Launcher waren mit `Terminal=true` hinterlegt. Dadurch blieb ein Terminal am Startprozess gebunden, bis die App beendet wurde. Setuphelfer-Launcher verwenden jetzt `Terminal=false` und starten Tauri direkt.

**EN:** Some launchers were configured with `Terminal=true`, so a terminal stayed attached to the startup process until the app exited. Setuphelfer launchers now use `Terminal=false` and start Tauri directly.
