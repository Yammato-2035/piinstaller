# Rescue ISO Controlled Build Gate

## Warum direkter `lb build` blockiert wird

Im materialisierten Live-Build-Tree unter `build/rescue/live-build/setuphelfer-rescue-live` ist `auto/build` absichtlich kein echter Build-Wrapper, sondern ein Stop-Script:

- Meldung: `Use controlled gate before running lb build.`
- Exit-Code: `20`

Das ist kein `live-build`-Konfigurationsfehler, sondern ein bewusstes Safety-Gate. Ein direkter Aufruf wie `lb build` ohne `noauto` wuerde `auto/build` rekursiv ausloesen und damit den kontrollierten Setuphelfer-Pfad umgehen.

## Was das Gate schuetzt

- Es trennt Preflight und echten Build.
- Es verhindert ungeplante Direktaufrufe aus dem Build-Tree.
- Es erzwingt den kontrollierten Operator-Pfad mit Logging und expliziter Freigabe.
- Es haelt USB-Write weiterhin komplett getrennt.

## Der korrekte naechste Build-Pfad

Bevorzugter Wrapper:

```bash
scripts/rescue-live/run-controlled-iso-build-with-logging.sh --operator-confirm-build
```

Der Wrapper fuehrt intern den gate-konformen Pfad aus:

```bash
cd build/rescue/live-build/setuphelfer-rescue-live
export PATH="<repo>/build/rescue/tool-compat/bin:$PATH"
./auto/config
sudo env PATH="<repo>/build/rescue/tool-compat/bin:$PATH" lb build noauto
```

Wichtig:

- Direkter `lb build` bleibt verboten.
- `lb build noauto` ist nur im kontrollierten Operator-Kontext zulaessig.
- Der projektlokale `rsvg`-Wrapper muss ueber `PATH` bevorzugt werden.

## Neues Operator-Policy-Gate

Der letzte gate-konforme Wrapper-Lauf scheiterte **nicht** an `rsvg`, Toolchain oder `live-build`-Konfiguration, sondern an fehlender kontrollierter Root-Ausführung:

- `sudo: ein Terminal ist erforderlich`
- `sudo: Ein Passwort ist notwendig`

Deshalb trennt Setuphelfer jetzt sauber zwischen:

- `RESCUE-BUILD-GATE-001`: direkter `lb build` wurde absichtlich vom `auto/build`-Gate blockiert
- `RESCUE-BUILD-ROOT-001`: kontrollierter Wrapper-Pfad ist bekannt, aber sichere Root-Ausführung fehlt

## Was als sichere Root-Ausführung gilt

- echtes Operator-Terminal mit interaktivem `sudo`
- oder eng begrenzte dokumentierte sudo-Allowlist nur fuer den freigegebenen Wrapper
- spaeter optional: separater Root-Helper (`systemd-run`/Polkit/Root-Unit) als Produktpfad

Nicht erlaubt:

- Passwort via stdin
- Askpass-Helfer als Workaround
- breites/globales `NOPASSWD`
- Aenderungen an `/usr/lib/live/build`
- Deaktivieren oder Umgehen des `auto/build`-Gates

## Was weiterhin getrennt bleibt

- USB-Write bleibt ein separates Safety-Gate.
- ISO-Erfolg ist nicht gleich Rettungsstick-Erfolg.
- Boot-Test und spaeterer Restore-Test bleiben eigene Folgephasen.
