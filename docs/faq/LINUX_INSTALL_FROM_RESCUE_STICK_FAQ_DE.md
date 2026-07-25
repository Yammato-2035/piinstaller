# FAQ — Linux vom Rettungsstick installieren (DE)

## Welche Linux-Systeme sind vorgesehen?
Linux Mint (aktuell unterstützt), Ubuntu Server LTS, Ubuntu Server und Debian-Installation. Debian Live ist die Laufzeit des Sticks, nicht das Installationsziel.

## Wann darf partitioniert/installiert werden?
Nur nach **expliziter Freigabe** oder nach **erfolgreichem Backup+Verify** der betroffenen Medien — plus Bestätigung im Assistenten.

## Was passiert beim ASUS ROG jetzt?
Geplant: Linux Mint auf der **zweiten NVMe** aus der laufenden Stick-Session (ohne Umstecken). Die Windows-NVMe bleibt geschützt. Orchestrierung erfolgt vom Entwicklungsrechner.

## Werden Telemetrie- und Diagnostikserver öffentlich?
Nein. Server bleiben in **privaten** GitHub-Repos; im öffentlichen Repo nur Contracts, Mocks und Doku.

## Wird das BIOS automatisch geflasht?
Nein. Es gibt nur eine geführte Diagnose/Vergleichssession — Flash nur manuell durch den Operator.
