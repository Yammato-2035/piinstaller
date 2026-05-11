# get.pi-installer.io – One-Liner-Installation

## Ziel

Nutzer können PI-Installer mit einem Befehl installieren:

```bash
curl -sSL https://get.pi-installer.io | bash
```

## Ohne eigene Domain (sofort nutzbar)

Nutzen Sie die **Raw-GitHub-URL** des Installer-Skripts (offizielles Repo `Yammato-2035/piinstaller`):

```bash
curl -sSL https://raw.githubusercontent.com/Yammato-2035/piinstaller/main/scripts/create_installer.sh | bash
```

Bei Klon aus einem anderen Branch: `main` durch den Branch-Namen ersetzen.

## Mit Domain get.pi-installer.io

Wenn Sie die Domain **get.pi-installer.io** besitzen:

1. **Option A – Redirect:** Die Domain (oder einen Pfad wie `https://get.pi-installer.io/install`) per HTTP-Redirect (302) auf die Raw-GitHub-URL zeigen lassen:
   ```
   https://raw.githubusercontent.com/Yammato-2035/piinstaller/main/scripts/create_installer.sh
   ```
   Dann liefert `curl -sSL https://get.pi-installer.io` den Skript-Inhalt.

2. **Option B – Proxy:** Einen kleinen Webserver (z. B. Nginx, Caddy) betreiben, der unter `https://get.pi-installer.io` den Inhalt von
   `https://raw.githubusercontent.com/Yammato-2035/piinstaller/main/scripts/create_installer.sh`
   ausliefert (z. B. per `proxy_pass` oder Fetch).

3. **Option C – Statisches Skript:** Das Skript periodisch von GitHub holen und unter get.pi-installer.io als statische Datei ausliefern (z. B. per Cron + wget/curl).

**Empfehlung:** Option A (Redirect) ist am einfachsten; Nutzer führen weiterhin `curl -sSL https://get.pi-installer.io | bash` aus und erhalten immer das Skript von GitHub (aktueller Branch).

## Klon-URL für das Installer-Skript

Wenn das Skript per `curl | bash` **ohne** bestehendes Repo ausgeführt wird, muss die Umgebungsvariable **PI_INSTALLER_REPO** gesetzt werden oder das Skript muss eine Default-Repo-URL kennen. Aktuell verlangt das Skript bei Klon explizit:

```bash
PI_INSTALLER_REPO=https://github.com/Yammato-2035/piinstaller.git curl -sSL https://get.pi-installer.io | bash
```

Um einen echten One-Liner ohne Umgebungsvariable zu ermöglichen, kann im Skript eine **Default-Repo-URL** gesetzt werden (z. B. die offizielle PI-Installer-Repo-URL). Dann reicht:

```bash
curl -sSL https://get.pi-installer.io | bash
```

Die Default-URL sollte im Skript `scripts/create_installer.sh` in der Variable `REPO_URL` bzw. als Fallback für `PI_INSTALLER_REPO` eingetragen werden (z. B. beim offiziellen Release).
