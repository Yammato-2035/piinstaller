# Dev Dashboard Controlled Command Runner (Architecture)

## Scope

Interne Tooling-Schicht für reproduzierbare Developer-Läufe mit strikter Sicherheitsgrenze.

## Architekturprinzipien

1. Kein freier Command-String, nur `command_id` aus Allowlist.
2. Ausführung standardmäßig `shell=false` über `argv`.
3. Safety-Klasse wird vor Ausführung geprüft.
4. `forbidden` und `operator_handoff` werden nicht ausgeführt.
5. Runtime-Gate-Status wird pro Run mitgeschrieben.
6. stdout/stderr werden in getrennte Logdateien persistiert.
7. Evidence-JSON referenziert Logdateien, Excerpts sind nur Zusatz.
8. Roadmap-Delta wird als Vorschlag erzeugt, nicht automatisch angewendet.

## Sicherheitsgrenze

- Kein `sudo` aus Dashboard-Execution.
- Kein apt/pip/systemd/partition/write-Path außerhalb eng definierter read-only/test-only Klassen.
- Keine externe URL-Ausführung außerhalb lokaler allowlisted Endpunkte.

## Operator-Handoff

Kommandos mit erhöhtem Risiko bleiben manuell:

- Build-/Cleanup-Kommandos mit Rootbedarf
- Mount/Unmount/Remove in chroot/build contexts
- Service-Steuerung

Der Runner erzeugt dafür Handoff-Evidence statt Ausführung.
