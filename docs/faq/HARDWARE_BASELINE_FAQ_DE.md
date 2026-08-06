# FAQ: Hardware-Baseline-Diagnostik (DE)

Pflichtfragen zu PI-RS-HW-BASELINE-DIAG-I18N-002. Kurze, ehrliche Antworten.

Sprachen: [Deutsch](HARDWARE_BASELINE_FAQ_DE.md) · [English](HARDWARE_BASELINE_FAQ_EN.md) · [Français](HARDWARE_BASELINE_FAQ_FR.md) · [Nederlands](HARDWARE_BASELINE_FAQ_NL.md)

## 1. Bedeutet eine grüne Kachel, dass die Hardware sicher fehlerfrei ist?

Nein. `no_immediate_issue_detected` bedeutet nur, dass der kurze Basistest keine unmittelbare Auffälligkeit gefunden hat. Er ersetzt keinen vollständigen Langzeittest und garantiert keine Fehlerfreiheit.

## 2. Was prüft der schnelle Speichertest?

Inventur (`/proc/meminfo`, optional DMI), Kernel-Hinweise (EDAC/MCE/OOM) und einen begrenzten Quick-Probe (höchstens 128 MiB bzw. 2 % von MemAvailable, harter Timeout).

## 3. Warum ersetzt er keinen vollständigen Memtest?

Ein vollständiger Memtest benötigt Stunden und belastet den gesamten Speicher. Der Basistest ist bewusst kurz und sicher und startet nie Memtest86+/memtester automatisch.

## 4. Was wird bei der CPU geprüft?

Plattformdaten (über `cpu_platform_detection`), Machine-Check-/Hardware-Error-Meldungen, Thermik/Throttling und ein kurzer deterministischer Quick-Probe.

## 5. Warum wird kein langer CPU-Stresstest automatisch gestartet?

Lange Stresstests (stress-ng/Prime95) erzeugen hohe Last und Hitze. Sie brauchen Operatorbestätigung und gehören zu erweiterten Tests, nicht zur Baseline.

## 6. Was wird bei der GPU geprüft?

Erkennung über `gpu_detection`, Render-Nodes, Kernel-/Firmwarefehler und optionale Lese-Probes (`glxinfo`/`eglinfo`/`vulkaninfo`). Kein Render-Stress.

## 7. Warum kann ein Backup trotz defekter GPU möglich sein?

Das Baseline-Gate blockiert bei roter GPU den GUI-Modus, aber nicht automatisch Backup. Backup ist lesend und braucht keine stabile Grafik.

## 8. Welche HDD-Werte sind kritisch?

SMART overall FAILED, Pending Sectors, Offline Uncorrectable und wiederholte Kernel-I/O-Fehler. Reallocated Sectors und CRC-Fehler sind gelbe Warnsignale.

## 9. Was bedeuten Pending Sectors?

Sektoren, die der Datenträger als problematisch markiert hat und die noch nicht umgebucht wurden. Sie gelten als kritische Auffälligkeit und priorisieren Datenrettung.

## 10. Welche SATA-SSD-Werte werden geprüft?

Wear Leveling, Available Reserved Space, Reported Uncorrectable, UDMA CRC, Unexpected Power Loss sowie TRIM-Unterstützung über sysfs.

## 11. Welche NVMe-Werte sind kritisch?

Critical Warning ≠ 0, Available Spare ≤ Threshold, Percentage Used ≥ 100 %, Media/Data Integrity Errors und wiederholte Controller-Resets.

## 12. Warum startet Setuphelfer keinen SMART-Selbsttest automatisch?

SMART Self-Tests können lange dauern und belasten den Datenträger. Die Baseline liest nur vorhandene Attribute; Self-Tests brauchen Operatorbestätigung.

## 13. Was geschieht bei einem kritischen Datenträgerbefund?

Restore und OS-Installation werden über das Gate blockiert. Backup vom Quelllaufwerk bleibt möglich, damit Daten noch gerettet werden können.

## 14. Darf ein auffälliger Datenträger noch als Backupziel verwendet werden?

Nein. Ein rotes Ziellaufwerk darf nicht beschrieben werden. Als Quelle für eine Notfall-Sicherung bleibt ein auffälliges Laufwerk lesbar.

## 15. Welche Tests benötigen eine spätere Operatorbestätigung?

Memtest86+, CPU-Stress, GPU-Render-Stress, SMART Short/Extended Self-Test. Die Baseline startet keine davon automatisch.

## 16. Welche Daten werden an den Telemetrieserver übertragen?

Nur redigierte Zusammenfassungen (Plattformklasse, CPU-/GPU-Herstellerklasse, Statuszähler, Issue-Codes, Kernel-/Payload-Version).

## 17. Werden Seriennummern übertragen?

Nein. Seriennummern, MAC-Adressen, IP-Adressen und vollständige EDID-Daten werden nicht übertragen.

## 18. Welche Unterschiede gibt es zwischen Pi 3, Pi 4 und Pi 5?

Sie werden einzeln über Device-Tree erkannt und erhalten eigene Bootmedien- und OS-Kompatibilitätsbewertungen. Details: `RASPBERRY_PI_3_TO_5_SUPPORT_DE.md`.

## 19. Kann ein einzelner 64-GB-Stick alle Betriebssysteme enthalten?

Nein. Setuphelfer nutzt Katalog + begrenzten Cache statt „Alles drauf“. Details: `64GB_CARRIER_ARCHITECTURE_DE.md`.

## 20. Wann ist ein physischer Hardwaretest erforderlich?

Immer wenn die Baseline rot/gelb meldet, Tools fehlen (`test_unavailable`) oder die Funktion (GUI, Druck, Scan, Boot) im realen Einsatz bestätigt werden muss.
