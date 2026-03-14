# Bewertung: Vorschlag Sicherheits- und Professionalitäts-Verbesserungen

_Stand: März 2026 – Prüfung der vorgeschlagenen To-Do-Liste und der detaillierten sudo-Store-Verschlüsselung anhand des aktuellen PI-Installer-Codes._

---

## Kurzfassung

- **Die Richtung ist sinnvoll:** Deutlich sicherer und professioneller – priorisiert nach Risiko & Aufwand – passt zum Projekt.
- **Viele Punkte sind echte Verbesserungen** und sollten umgesetzt werden, teils mit **Anpassungen** an euren Kontext (Laufzeit als Normalbenutzer, Netzwerk-Zugriff, Schreibzugriffe des Services).
- **Einzelne Vorschläge** (Key-Pfad, systemd ProtectHome, CORS-Liste) müssen **projekt-spezifisch** angepasst werden, damit nichts kaputtgeht.

---

## Phase 1 – Kritische Sicherheitslücken

### 1. CORS strikt einschränken

**Bewertung: Sinnvoll, mit Anpassung.**

- **Ist:** `allow_origins=["*"]` und `allow_credentials=True` – jede Website kann mit Cookies/Credentials Anfragen an eure API schicken (z. B. von einem anderen Rechner im LAN).
- **Vorschlag:** Nur `localhost:3001`, `pi-installer.local:3001`, `127.0.0.1:3001`.

**Anpassung:** Das Backend läuft mit `--host 0.0.0.0` (start-backend.sh, start.sh), das Frontend oft auf Port 3001. Wenn Nutzer die Oberfläche **per IP/Hostname im LAN** aufrufen (z. B. `http://192.168.1.5:3001` oder `http://raspberrypi.local:3001`), ist der Origin **nicht** localhost. Dann müsst ihr entweder:

- zusätzlich erlauben: z. B. `http://<hostname>.local:3001` und/oder
- erlaubte Origins aus Config/Umgebung lesen (z. B. `PI_INSTALLER_CORS_ORIGINS`),

sonst blockiert CORS legitimen Zugriff aus dem Netzwerk. **Empfehlung:** CORS einschränken, aber Liste konfigurierbar machen und in der Doku die Standard-Liste + Option „Zugriff aus dem LAN“ dokumentieren.

---

### 2. Sudo-Password-Store härten (Fernet-Verschlüsselung)

**Bewertung: Deutliche Verbesserung, Umsetzung mit Anpassungen.**

- **Ist:** Ein globales Dict `sudo_password_store = {}`, Schlüssel `"password"` – Klartext im RAM. Bei Memory-Dump oder API-Exploit ist das Passwort sofort lesbar.
- **Vorschlag:** Passwort nur verschlüsselt im RAM halten, Key in Datei, TTL, optional pro Session.

**Was passt:**

- `cryptography` ist bereits in `backend/requirements.txt` (>=43).
- Fernet (AES-128 + HMAC) ist für solche Secrets gut geeignet.
- TTL (15–30 Min) fehlt heute und reduziert das Zeitfenster für Missbrauch.
- Entschlüsselung nur bei `run_command(..., sudo=True)` – kurze Klartext-Phase nur im Prozess, nicht persistent.

**Anpassungen für PI-Installer:**

1. **Key-Datei:** Vorschlag nutzt `/etc/pi-installer/sudo.key`. Der Backend-Service läuft als **Normalbenutzer** (`User={{USER}}`). Unter `/etc/pi-installer/` hat dieser User oft keine Schreibrechte. Besser:
   - Key unter **benutzerbeschreibbarem** Pfad: z. B. `{INSTALL_DIR}/.sudo_key` oder `~/.config/pi-installer/sudo.key` (XDG).
   - Wenn ihr explizit „nur root-Installation“ unterstützen wollt, könnte `/etc/pi-installer/` mit passenden Rechten (z. B. chmod 600, Owner = Service-User) vom Install-Skript angelegt werden – dann in der Doku klar machen.

2. **Store-Schlüssel:** Im Code wird überall `sudo_password_store["password"]` genutzt (ein einziges Passwort pro Prozess), **nicht** PID. Der Vorschlag nutzt PID; ihr könnt entweder:
   - bei einem gemeinsamen Store bleiben und nur **einen** Eintrag `"password"` verschlüsselt ablegen, oder
   - auf Session-ID umstellen (z. B. aus Request-Header/Token), wenn ihr später mehrere Sessions trennen wollt. Für den aktuellen Single-User-Betrieb reicht ein verschlüsselter Einzelwert.

3. **Kein Passwort in Logs:** Audit-Log nur „sudo verwendet“ (z. B. Zeit, Endpoint), **niemals** Passwort oder Entschlüsseltes.

**Fazit:** Umsetzung lohnt sich; Key-Pfad und Store-Struktur (ein Wert vs. Session-ID) an euren Laufzeit- und Installationskontext anpassen.

---

### 3. Systemd-Services härten

**Bewertung: Teilweise sinnvoll; ProtectHome und Schreibzugriffe prüfen.**

- **Ist:** `pi-installer-backend.service` und `pi-installer.service` haben nur User, WorkingDirectory, ExecStart – keine Sandbox-Optionen.
- **Vorschlag:** `ProtectSystem=strict`, `ProtectHome=read-only`, `PrivateTmp=yes`, `NoNewPrivileges=yes`, `MemoryMax=512M`, `LimitNOFILE=4096`.

**Bewertung pro Option:**

| Option | Bewertung |
|--------|-----------|
| `ProtectSystem=strict` | Sinnvoll – schützt Systemverzeichnisse. |
| `PrivateTmp=yes` | Sinnvoll – eigener /tmp für den Service. |
| `NoNewPrivileges=yes` | Sinnvoll – keine Privilegien-Eskalation. |
| `MemoryMax=512M` | Sinnvoll – begrenzt Ressourcen. |
| `LimitNOFILE=4096` | Sinnvoll. |
| `ProtectHome=read-only` | **Vorsicht:** Der Service schreibt in `INSTALL_DIR` (Logs, ggf. config, Pip-Cache). Wenn `INSTALL_DIR` unter **/home** liegt (z. B. `/home/pi/piinstaller`), verbietet `ProtectHome=read-only` alle Schreibzugriffe in /home – dann funktionieren Logs/Konfiguration nicht. **Empfehlung:** `ProtectHome=read-only` weglassen oder nur setzen, wenn `INSTALL_DIR` außerhalb von /home liegt (z. B. /opt/pi-installer) und ihr bestätigt, dass nirgends unter /home geschrieben wird. |

---

### 4. Rate-Limiting + Security Headers

**Bewertung: Sinnvoll.**

- **Ist:** Kein Rate-Limit auf `/api/users/sudo-password` und anderen sensiblen Endpoints – Brute-Force möglich. Keine HSTS/X-Frame-Options etc.
- **Vorschlag:** slowapi/fastapi-limiter auf sudo + actions; SecurityHeadersMiddleware.

**Empfehlung:** Rate-Limit auf sudo-Passwort-Endpoint und ggf. `/api/actions`; Security-Header (HSTS, X-Frame-Options, X-Content-Type-Options) ergänzen. Geringer Aufwand, klarer Sicherheitsgewinn.

---

### 5. Self-Update + Installer-Skript absichern

**Bewertung: Professionell, Aufwand höher.**

- SHA256-Hash + Commit-Verify vor `git pull`; Installer-Skript mit Hash/GPG auf GitHub – erhöht Vertrauen und schützt vor manipulierten Updates.
- **Empfehlung:** Als Phase 2/3 einplanen; GPG-Signatur optional, aber Hash-Check und Dokumentation im README sind ein guter erster Schritt.

---

## Phase 2 – Starke Verbesserungen

- **Frontend Production-Modus:** Sinnvoll – `npm run build` + Auslieferung über FastAPI spart Ressourcen und reduziert Angriffsfläche.
- **Bessere Authentifizierung (JWT/Session-Cookies, is_admin-Middleware):** Sinnvoll für Multi-User oder strengere Zugriffskontrolle; Aufwand mittel.
- **Config-Verschlüsselung (Fernet für Passwörter/API-Keys):** Sinnvoll, konsistent mit verschlüsseltem sudo-Store.
- **Audit-Logging (sudo + kritische Aktionen):** Sinnvoll; Logger vorhanden – erweitern um strukturierte Einträge (Timestamp, User, Command, Endpoint), **ohne** Passwörter.
- **Remote-Zugriff Default deaktivieren:** Sinnvoll, wenn „Remote“ explizit ein Feature ist – Default „nur lokal“ reduziert Risiko.

---

## Phase 3 – Qualität & Professionalität

- **Tests (pytest + httpx), CI/CD (Lint, Tests, Security-Scan), Docker, Nginx/Let’s Encrypt, SECURITY.md/CONTRIBUTING.md, API-Versioning:** Alles sinnvoll und typisch für ein „professionelleres“ Projekt. Priorisierung wie in der Liste (Phase 1 → 2 → 3) ist vernünftig.

---

## Sudo-Store-Verschlüsselung – Detail-Check

- **Architektur (EncryptedSudoStore-Klasse):** Passt; klare Trennung Key-Load/Store/Get/Clear.
- **Key in config.json als Base64:** Wenn der Master-Key aus dem System kommt, müsst ihr Key-Rotation und Backup klar regeln; Key-Datei (mit Fallback-Pfad für Normalbenutzer) ist oft einfacher.
- **`run_command`-Anpassung:** Statt Passwort aus Dict zu lesen, `sudo_store.get_password(session_id_or_pid)` aufrufen; bei `None` Fehler zurückgeben. Kein `echo '...' | sudo -S` in der Shell (Injectionsrisiko) – ihr macht das bereits korrekt mit `subprocess.Popen` und `stdin=...`.
- **Shutdown clear:** `sudo_store.clear()` beim Shutdown beibehalten, damit nichts im RAM bleibt.

---

## Empfohlene Reihenfolge (für euch)

1. **CORS** einschränken (mit konfigurierbarer Origin-Liste + Doku für LAN-Zugriff).
2. **Sudo-Store** auf Fernet umstellen (Key-Pfad benutzer-writable, TTL, ein Wert "password" oder Session-ID; Audit nur „sudo verwendet“).
3. **Rate-Limiting + Security-Header** auf relevante Endpoints.
4. **Systemd** härten **ohne** `ProtectHome=read-only` (oder nur wenn INSTALL_DIR außerhalb /home und Schreibzugriffe geprüft).
5. Danach: Phase 2 (Production-Frontend, Audit-Log, Config-Verschlüsselung, Remote-Default) und Phase 3 (Tests, CI, Doku, API-Versioning).

---

## Fazit

- Die **Umsetzung ist sinnvoll** und eine **deutliche Verbesserung** für Sicherheit und Professionalität des PI-Installers.
- Mit den genannten **Anpassungen** (CORS-Liste, Key-Pfad, Store-Struktur, ProtectHome) bleibt alles mit eurem aktuellen Setup (Normalbenutzer, LAN-Zugriff, Schreibzugriffe unter INSTALL_DIR) kompatibel.
- Die **detaillierte Fernet-Beschreibung** für den sudo-Store ist technisch stimmig; die konkrete Integration solltet ihr an die bestehende Nutzung von `sudo_password_store["password"]` und an den gewählten Key-Speicherort anpassen.
