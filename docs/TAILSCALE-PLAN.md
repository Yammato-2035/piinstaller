# Companion über Tailscale statt unverschlüsseltem LAN-HTTP (Paket 5, E-09)

## Warum diese Option

Ihr habt Tailscale/WireGuard ohnehin auf der Werkzeugliste (Fernwartung/VPN).
Das über den Companion-Traffic zu legen löst das TLS-im-LAN-Problem, ohne
dass ihr selbst Zertifikate verwalten, verteilen oder erneuern müsst —
Tailscale übernimmt Schlüsselaustausch und Verschlüsselung vollständig.

## Wie es funktioniert (Kurzfassung)

1. Pi und Smartphone sind beide im selben **Tailnet** (Tailscale-eigenes,
   Ende-zu-Ende-verschlüsseltes Overlay-Netzwerk).
2. Der Companion-Traffic läuft über die Tailscale-IP des Pi
   (`100.x.y.z`), nicht über die normale LAN-IP.
3. Optional: Tailscale MagicDNS + `tailscale cert` liefert sogar ein
   echtes, gültiges TLS-Zertifikat für einen `*.ts.net`-Namen — dann ist
   es nicht nur verschlüsselt, sondern auch mit gültigem Zertifikat
   (kein Browser-Warnhinweis, im Gegensatz zu selbstsigniert).

## Voraussetzungen / Trade-offs (bewusst benennen)

- **Smartphone braucht die Tailscale-App** — ein zusätzlicher
  Installationsschritt gegenüber "einfach WLAN verbinden und QR scannen".
  Das ist der Haupt-UX-Kompromiss dieser Option.
- Pairing-Flow muss angepasst werden: QR-Payload sollte die
  Tailscale-Adresse/den MagicDNS-Namen enthalten, sobald Tailscale aktiv
  ist — sonst verbindet sich die PWA weiter über die alte LAN-IP.
- Erstes Setup pro Pi: `tailscale up` einmalig ausführen (idealerweise
  ins Ersteinrichtungs-Flow von Setuphelfer selbst integrieren, passt zu
  "geführte Härtung").

## Konkrete Umsetzungsschritte

1. **Erkennung:** Backend prüft beim Start, ob `tailscale status --json`
   verfügbar ist und der Pi Teil eines Tailnets ist. Wenn ja: Tailscale-IP
   ermitteln.
2. **QR-Payload anpassen** (`core/qr.py`, `build_pairing_payload`): Wenn
   Tailscale erkannt, `host` im Payload auf die Tailscale-IP/MagicDNS-Name
   setzen statt der LAN-IP. Fallback auf LAN-IP, wenn kein Tailscale aktiv
   — damit nichts kaputtgeht, wo Tailscale (noch) nicht genutzt wird.
3. **UI-Hinweis:** Auf der Pairing-Seite anzeigen, ob die Verbindung über
   Tailscale (verschlüsselt) oder normales LAN (unverschlüsselt, mit
   Warnhinweis) läuft — Transparenz statt stillschweigender Annahme.
4. **Dokumentation:** Kurzanleitung "Companion sicher nutzen" für
   Tutorials/Website: Tailscale-App installieren, mit demselben Tailnet
   wie der Pi verbinden, dann pairen.
5. **Migrationsfenster:** Reines LAN-HTTP bleibt als Fallback bestehen
   (mit deutlichem UI-Warnhinweis), bis Tailscale-Onboarding im
   Ersteinrichtungs-Assistenten selbst verankert ist — kein Zwang von
   heute auf morgen.

## Was ich NICHT umgesetzt habe (bewusst, braucht dein Go)

Die QR-Payload-Anpassung und Tailscale-Erkennung fasse ich nicht ungefragt
an, weil das den Pairing-Flow ändert, den echte Beta-Tester schon nutzen
könnten — das ist ein guter Kandidat für einen eigenen, kleinen
Arbeitsschritt, sobald du grünes Licht gibst. Ich kann das umsetzen; sag
Bescheid, wenn's losgehen soll.
