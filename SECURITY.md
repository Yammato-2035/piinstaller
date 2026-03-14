# Sicherheitshinweise – PI-Installer

Dieses Dokument beschreibt die Sicherheitsmaßnahmen des PI-Installers und empfohlene Vorgehensweisen.

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

- **CORS:** Erlaubte Origins sind eingeschränkt und über `PI_INSTALLER_CORS_ORIGINS` erweiterbar (LAN).
- **Sudo-Passwort:** Wird nur verschlüsselt (Fernet) im Speicher gehalten und läuft nach 30 Minuten ab (TTL).
- **Rate-Limiting:** Der Endpoint zum Speichern des sudo-Passworts ist auf 10 Anfragen pro Minute begrenzt.
- **Security-Header:** Antworten enthalten u. a. `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`.
- **Systemd:** Die Services nutzen `ProtectSystem=strict`, `PrivateTmp=yes`, `NoNewPrivileges=yes`, begrenzten Speicher und Datei-Handles.

## Sicherheitslücken melden

Wenn Sie eine Sicherheitslücke gefunden haben, melden Sie diese bitte **nicht** öffentlich (z. B. in einem normalen Issue), sondern per E-Mail oder über einen vertraulichen Kanal an die Betreiber des Projekts. Danke.
