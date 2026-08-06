# FAQ: Hardware-baselinediagnostiek (NL)

Verplichte vragen voor PI-RS-HW-BASELINE-DIAG-I18N-002. Korte, eerlijke antwoorden.

Talen: [Deutsch](HARDWARE_BASELINE_FAQ_DE.md) · [English](HARDWARE_BASELINE_FAQ_EN.md) · [Français](HARDWARE_BASELINE_FAQ_FR.md) · [Nederlands](HARDWARE_BASELINE_FAQ_NL.md)

## 1. Betekent een groene tegel dat de hardware gegarandeerd foutvrij is?

Nee. `no_immediate_issue_detected` betekent alleen dat de korte baseline geen onmiddellijke afwijking vond. Het vervangt geen lange test en garandeert nooit foutvrije hardware.

## 2. Wat controleert de snelle geheugentest?

Inventaris (`/proc/meminfo`, optioneel DMI), kernelsignalen (EDAC/MCE/OOM) en een begrensde quick probe (hoogstens 128 MiB of 2% van MemAvailable, harde timeout).

## 3. Waarom vervangt hij geen volledige Memtest?

Een volledige Memtest duurt uren en belast al het RAM. De baseline is bewust kort en veilig en start nooit Memtest86+/memtester automatisch.

## 4. Wat wordt bij de CPU gecontroleerd?

Platformgegevens (via `cpu_platform_detection`), machine-check-/hardware-error-meldingen, thermiek/throttling en een korte deterministische quick probe.

## 5. Waarom wordt er geen lange CPU-stresstest automatisch gestart?

Lange stresstests (stress-ng/Prime95) veroorzaken hoge last en hitte. Ze vereisen operatorbevestiging en horen bij uitgebreide tests, niet bij de baseline.

## 6. Wat wordt bij de GPU gecontroleerd?

Detectie via `gpu_detection`, render-nodes, kernel-/firmwarefouten en optionele read-only probes (`glxinfo`/`eglinfo`/`vulkaninfo`). Geen renderstress.

## 7. Waarom kan een backup ondanks een defecte GPU nog mogelijk zijn?

Het baseline-gate blokkeert bij een rode GPU de GUI-modus, maar niet automatisch backup. Backup is leesgericht en heeft geen stabiele grafische weergave nodig.

## 8. Welke HDD-waarden zijn kritiek?

SMART overall FAILED, Pending Sectors, Offline Uncorrectable en herhaalde kernel-I/O-fouten. Reallocated Sectors en CRC-fouten zijn gele waarschuwingen.

## 9. Wat betekenen Pending Sectors?

Sectoren die de schijf als problematisch heeft gemarkeerd en die nog niet zijn omgezet. Dit is een kritieke bevinding en prioriteert dataredding.

## 10. Welke SATA-SSD-waarden worden gecontroleerd?

Wear Leveling, Available Reserved Space, Reported Uncorrectable, UDMA CRC, Unexpected Power Loss en TRIM-ondersteuning via sysfs.

## 11. Welke NVMe-waarden zijn kritiek?

Critical Warning ≠ 0, Available Spare ≤ Threshold, Percentage Used ≥ 100%, Media/Data Integrity Errors en herhaalde controllerresets.

## 12. Waarom start Setuphelfer geen SMART-zelftest automatisch?

SMART-zelftests kunnen lang duren en belasten de schijf. De baseline leest alleen bestaande attributen; zelftests vereisen operatorbevestiging.

## 13. Wat gebeurt er bij een kritieke opslagbevinding?

Restore en OS-installatie worden door het gate geblokkeerd. Backup vanaf de bronschijf blijft mogelijk zodat data nog gered kan worden.

## 14. Mag een opvallende schijf nog als backupdoel worden gebruikt?

Nee. Een rode doelschijf mag niet worden beschreven. Als bron voor een noodbackup blijft een opvallende schijf leesbaar.

## 15. Welke tests vereisen latere operatorbevestiging?

Memtest86+, CPU-stress, GPU-renderstress, SMART short/extended self-test. De baseline start geen van deze automatisch.

## 16. Welke gegevens worden naar de telemetrieserver gestuurd?

Alleen geredigeerde samenvattingen (platformklasse, CPU-/GPU-fabrikantklasse, statusaantallen, issue-codes, kernel-/payloadversie).

## 17. Worden serienummers verzonden?

Nee. Serienummers, MAC-adressen, IP-adressen en volledige EDID-gegevens worden nooit verzonden.

## 18. Welke verschillen zijn er tussen Pi 3, Pi 4 en Pi 5?

Ze worden individueel via device tree gedetecteerd en krijgen eigen bootmedia- en OS-compatibiliteitsbeoordelingen. Details: `RASPBERRY_PI_3_TO_5_SUPPORT_NL.md`.

## 19. Kan één enkele 64-GB-stick alle besturingssystemen bevatten?

Nee. Setuphelfer gebruikt catalogus + begrensde cache in plaats van „alles erop". Details: `64GB_CARRIER_ARCHITECTURE_NL.md`.

## 20. Wanneer is een fysieke hardwaretest vereist?

Zodra de baseline rood/geel meldt, tools ontbreken (`test_unavailable`), of een echte functie (GUI, print, scan, boot) bevestigd moet worden.
