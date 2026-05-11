# Sicherheitshinweise – PI-Installer

Dieses Dokument beschreibt die Sicherheitsmaßnahmen des PI-Installers und empfohlene Vorgehensweisen.

## Threat Model

1. **PI-Installer ist für LAN- und VPN-Betrieb gedacht.**  
   Das System ist darauf ausgelegt, im lokalen Netzwerk oder über ein VPN (z. B. WireGuard, Tailscale) genutzt zu werden. Der Backend-Dienst bindet standardmäßig nur an `127.0.0.1`; LAN-Zugriff ist optional über die Umgebungsvariable `ALLOW_REMOTE_ACCESS=true` und ggf. weitere erlaubte Hosts.

2. **Direkte Internetexposition wird nicht empfohlen.**  
   Ein offener Zugang aus dem Internet erhöht die Angriffsfläche (Brute-Force, Ausnutzung von Schwachstellen, Missbrauch von Rechten). Bei Bedarf soll der Zugriff stark eingeschränkt werden (Firewall, Zugriff nur aus bestimmten IP-Bereichen, Reverse-Proxy mit Authentifizierung).

3. **Reverse-Proxy und HTTPS werden empfohlen.**  
   Wenn der PI-Installer aus dem LAN oder über VPN von außen erreichbar sein soll, wird die Nutzung eines Reverse-Proxys (z. B. Nginx, Caddy) mit TLS (z. B. Let’s Encrypt) empfohlen. Der Backend- und Frontend-Dienst laufen dann hinter dem Proxy; der Proxy übernimmt Terminierung und ggf. Authentifizierung.

4. **Ports und Dienste:**  
   - **Backend (API):** Standard-Port 8000, standardmäßig nur an `127.0.0.1` gebunden.  
   - **Frontend (Web-GUI):** Standard-Port 3001.  
   - Bei Installation über systemd werden die Dienste mit eingeschränkten Rechten (systemd-Härtung) gestartet.  
   - In Docker: Das Backend ist nur intern („expose“) sichtbar; das Frontend ist über Port 3001 erreichbar.

## Netzwerk-Zugriff: Lokal vs. Internet

### Lokales Netzwerk (empfohlen)

- Der PI-Installer ist **für die Nutzung im lokalen Netzwerk (LAN)** ausgelegt.
- Backend (Port 8000) und Frontend (Port 3001) können von anderen Geräten im gleichen Netzwerk (z. B. Laptop, Tablet) erreicht werden.
- **CORS** ist standardmäßig auf `localhost`, `127.0.0.1` und `pi-installer.local` (Port 3001) beschränkt. Für Zugriff von anderen LAN-Hosts die Umgebungsvariable **`PI_INSTALLER_CORS_ORIGINS`** setzen, z. B.:
  ```bash
  export PI_INSTALLER_CORS_ORIGINS="http://192.168.1.10:3001,http://raspberrypi.local:3001"
  ```
  (Werte kommagetrennt, ohne Leerzeichen.)

### Zugriff aus dem Internet

- Ein **Zugriff von außen (Internet)** ist **nicht** Teil der Standard-Installation und richtet sich an **erfahrene Nutzer**.
- **Bei der ersten Installation** sollte der Zugriff **nur aus dem lokalen Netz** möglich sein. Eine Freigabe ins Internet (Port-Weiterleitung, offener Port ohne Absicherung) ist **nicht** empfohlen.
- **Empfehlung für Remote-Zugriff:** Nutzen Sie ein **VPN** (z. B. WireGuard, Tailscale, OpenVPN), um sich aus der Ferne mit dem heimischen Netz zu verbinden und den PI-Installer wie im LAN zu nutzen. So bleibt die Oberfläche nicht direkt dem Internet ausgesetzt.
- **Wenn Sie den PI-Installer dennoch aus dem Internet erreichbar machen:**  
  - Der Zugriff für **jeden** aus dem Internet birgt **erhebliche Gefahren** (Brute-Force, Ausnutzung von Schwachstellen, Missbrauch von sudo-Rechten).
  - **Starke Einschränkung** ist erforderlich, z. B.:
    - **Firewall:** Nur bestimmte IP-Bereiche oder einen Reverse-Proxy (z. B. Nginx mit Authentifizierung) vor dem Backend/Frontend.
    - Keine offene Bindung an 0.0.0.0 ohne weitere Absicherung nach außen.
    - Regelmäßige Updates und starke Passwörter.
  - Die Verantwortung für Konfiguration und Risiko liegt beim Betreiber.

## Umgesetzte Sicherheitsmaßnahmen

- **Netzwerk:** Backend bindet standardmäßig nur an `127.0.0.1`; LAN über `ALLOW_REMOTE_ACCESS=true`. TrustedHost-Middleware beschränkt gültige Host-Header.
- **CORS:** Erlaubte Origins sind eingeschränkt und über `PI_INSTALLER_CORS_ORIGINS` erweiterbar (LAN).
- **Sudo-Passwort:** Wird nur verschlüsselt (Fernet) im Speicher gehalten und läuft nach 30 Minuten ab (TTL).
- **Rate-Limiting:** Der Endpoint zum Speichern des sudo-Passworts ist auf 10 Anfragen pro Minute begrenzt.
- **Security-Header:** Antworten enthalten u. a. `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`, `Content-Security-Policy`, `Permissions-Policy`; bei HTTPS zusätzlich `Strict-Transport-Security`.
- **Systemd:** Die Services nutzen Härtungsoptionen (ProtectSystem, ProtectHome, PrivateTmp, PrivateDevices, NoNewPrivileges, RestrictAddressFamilies, SystemCallFilter, ReadWritePaths, begrenzter Speicher/Datei-Handles).
- **Supply-Chain:** Python-Abhängigkeiten mit Versionsbereichen; Dockerfile mit Hinweis auf Image-Pinning. GitHub-Workflow „Security“: pip-audit, npm audit, Semgrep, Secret-Scan (nur Berichte, keine Codeänderungen).

## Security Reporting

Wenn Sie eine **Sicherheitslücke** gefunden haben:

- **Melden Sie diese bitte nicht öffentlich** (z. B. nicht in einem normalen GitHub-Issue oder in öffentlichen Foren).
- Nutzen Sie einen **vertraulichen Kanal** (z. B. E-Mail an die Betreiber des Projekts oder über die GitHub-Security-Funktion „Report a vulnerability“, sofern für das Repository aktiviert).
- Geben Sie nach Möglichkeit eine kurze Beschreibung des Problems, Schritte zur Reproduktion (ohne Ausnutzungscode zu verbreiten) und die betroffene Version an.
- Die Betreiber werden sich um eine zeitnahe Rückmeldung und ggf. Koordination bei der Veröffentlichung eines Fixes bemühen.

Vielen Dank für Ihre verantwortungsvolle Meldung.
