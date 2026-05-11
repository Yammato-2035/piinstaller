# Setuphelfer – Öffentlicher Entwicklungs- und Teststatus

Setuphelfer befindet sich in der Stabilisierung für Produktions- und Monetarisierungsreife.

Unser Grundsatz:

> Erst Backup. Dann Änderungen.

## Ampelstatus

| Status | Bedeutung |
|--------|-----------|
| Grün | umgesetzt, getestet, dokumentiert, Evidence vorhanden |
| Gelb | teilweise umgesetzt, weitere Tests erforderlich |
| Rot | geplant oder offen |
| Schwarz | bewusst zurückgestellt |

## Aktuelle Schwerpunkte

1. Backup & Restore stabilisieren  
2. Hardwaretests durchführen  
3. Read-only Rescue-Stick vorbereiten  
4. Monolith analysieren  
5. Website und Monetarisierung transparent vorbereiten  

## Aktueller Stand

| Bereich | Status | Kurzinfo |
|---------|--------|----------|
| Backup | Gelb | Kern vorhanden; Hardware-E2E und Evidence offen |
| Verify | Gelb | Basic/Deep in Matrix; Nachweise teilweise |
| Restore | Rot | kontrollierte Restore-Tests auf freigegebenem Medium ausstehend |
| Rescue Stick | Rot | read-only MVP geplant |
| Hardwaretests | Rot | Matrix vorbereitet |
| Website | Gelb | Repo-Doku & Struktur; Live-Seite separat zu pflegen |
| Affiliate | Gelb | Policies im Repo; Umsetzung auf Site ausstehend |
| Cloudserver Edition | Schwarz | nach Modularisierung |

## Sicherheitshinweis

Tutorials und Systemänderungen sollten nur durchgeführt werden, wenn vorher ein aktuelles Backup erstellt wurde. Setuphelfer soll genau diesen sicheren Arbeitsablauf unterstützen.

## Transparenzsatz (öffentlich)

Setuphelfer wird schrittweise produktionsreif gemacht. Wir veröffentlichen den technischen Fortschritt transparent mit Ampelstatus, Testmatrix und Evidence-Dateien. Grün bedeutet: getestet, dokumentiert und reproduzierbar. Tutorials und Systemänderungen sollten nur mit aktuellem Backup durchgeführt werden.
