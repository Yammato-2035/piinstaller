# Netzwerk-Zugriff: Lokales Netzwerk, VPN, Internet

Diese Seite erläutert, wie Sie den PI-Installer im Netz nutzen und worauf Sie achten sollten.

## Lokales Netzwerk (LAN)

- Der PI-Installer ist dafür ausgelegt, **im lokalen Netzwerk** genutzt zu werden.
- Andere Geräte im gleichen WLAN/LAN (z. B. Laptop, Smartphone) können die Weboberfläche aufrufen, wenn Sie die Adresse des Raspberry Pi verwenden (z. B. `http://192.168.1.5:3001` oder `http://raspberrypi.local:3001`).
- Damit das Frontend vom Backend (API) Antworten erhält, müssen die **CORS-Origins** die genutzte Adresse erlauben. Standardmäßig sind nur `localhost`, `127.0.0.1` und `pi-installer.local` (jeweils Port 3001) erlaubt.
- **Zugriff von einem anderen Rechner im LAN:** Setzen Sie die Umgebungsvariable **`PI_INSTALLER_CORS_ORIGINS`** (z. B. in der systemd-Service-Datei oder in Ihrer Startumgebung), z. B.:
  ```bash
  PI_INSTALLER_CORS_ORIGINS="http://192.168.1.10:3001,http://raspberrypi.local:3001"
  ```
  Ersetzen Sie die Beispiele durch die tatsächlichen Adressen, unter denen Sie das Frontend aufrufen.

## Remote-Zugriff: VPN empfohlen

- **Empfehlung:** Wenn Sie von unterwegs auf den PI-Installer zugreifen möchten, nutzen Sie ein **VPN** in Ihr Heimnetz (z. B. WireGuard, Tailscale, OpenVPN).
- Über das VPN erscheinen Sie im lokalen Netz; Sie können die Oberfläche dann wie im LAN nutzen, ohne den PI-Installer direkt dem Internet zu öffnen.

## Zugriff aus dem Internet (nur für erfahrene Nutzer)

- Ein **direkter Zugriff aus dem Internet** (z. B. durch Port-Weiterleitung am Router) ist **nicht** Teil der Standard-Einrichtung und wird **bei der ersten Installation nicht** freigegeben.
- **Warnung:** Einen offenen Zugang für **jeden** aus dem Internet einzurichten birgt **viele Gefahren** (z. B. Brute-Force-Angriffe, Ausnutzung von Schwachstellen, Missbrauch von Admin-Rechten). Der PI-Installer kann mit sudo-Rechten arbeiten; ein Kompromittierter Zugang ist besonders kritisch.
- **Wenn Sie den Zugriff aus dem Internet dennoch ermöglichen wollen:**
  - **Stark einschränken**, z. B. durch:
    - **Firewall:** Nur bestimmte IP-Adressen oder -Bereiche erlauben.
    - **Reverse-Proxy** (z. B. Nginx) mit Authentifizierung und ggf. HTTPS (Let’s Encrypt) vor Backend und Frontend.
    - Keine unnötige Öffnung weiterer Ports.
  - Regelmäßige Updates, starke Passwörter und ggf. Zwei-Faktor-Authentifizierung am Proxy nutzen.
- Die Verantwortung für Konfiguration und Risiken liegt bei Ihnen als Betreiber.

## Kurzüberblick

| Zugriff            | Empfehlung                    |
|--------------------|-------------------------------|
| Nur lokal (gleicher Rechner) | Standard, unkritisch.        |
| Lokales Netzwerk (LAN)       | Unterstützt, CORS ggf. anpassen. |
| Über VPN ins LAN             | Empfohlen für Remote-Zugriff. |
| Direkt aus dem Internet      | Nur für erfahrene Nutzer, stark absichern (Firewall, Proxy). |

Weitere Sicherheitshinweise: [SECURITY.md](../../SECURITY.md) im Projektroot.
