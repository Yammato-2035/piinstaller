# Rescue Stick FAQ (DE)

## Warum wurde kein ISO gebaut?
Dieser Lauf war strikt auf Contract-/Stub-Implementierung begrenzt.

## Warum E2EE zusätzlich zu TLS?
TLS schützt den Kanal, E2EE schützt die Payload Ende-zu-Ende zwischen Agent und Server.

## Welche Daten werden gemeldet?
Session-/Agent-Metadaten, Discovery-/Sicherheitsstatus, Systemreport-Struktur.

## Welche Daten werden nicht gemeldet?
Keine Klartext-Seriennummern, keine persistierten Klartext-IP-Adressen, keine automatische Standortdaten.

## Warum ist Pairing Pflicht?
Der Rettungsstick darf sich nicht blind anmelden; Operator-Bestätigung ist Sicherheitsanforderung.

## Warum ist nftables Pflicht?
Default-deny reduziert Angriffsfläche im Rettungsszenario.
