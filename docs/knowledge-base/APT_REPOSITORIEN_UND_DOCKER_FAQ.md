# FAQ / Wissensdatenbank: APT-Repositories, Linux Mint, Docker, Grafana

**Stand:** 2026-04-11  
**Kontext:** Entwicklungsrechner mit **Linux Mint** (Codename z. B. `zena`), Ubuntu-Basis **noble**; gesammelte Lösungen aus Support-Runden, um **nicht doppelt** zu recherchieren.

**Chronologisches Chat-Protokoll (ohne doppelte Befehle):** [CHAT_ZUSAMMENFASSUNG_APT_DOCKER_2026-04.md](CHAT_ZUSAMMENFASSUNG_APT_DOCKER_2026-04.md) · **Übersicht Ordner:** [README.md](README.md)

---

## Inhaltsverzeichnis

1. [APT-Meldungen kurz erklärt](#apt-meldungen-kurz-erklärt)
2. [Cursor-APT-Repository: `NO_PUBKEY 42A1772E62E492D6`](#cursor-apt-repository-no_pubkey-42a1772e62e492d6)
3. [Grafana: Warnung „Schlüssel in trusted.gpg“](#grafana-warnung-schlüssel-in-trustedgpg)
4. [Google Chrome: `main/binary-i386` wird übersprungen](#google-chrome-mainbinary-i386-wird-übersprungen)
5. [`repo.asus-linux.org`: tot, DNS, Alternativen](#repoasus-linuxorg-tot-dns-alternativen)
6. [Linux Mint und Docker-Repository (`zena` vs. `noble`)](#linux-mint-und-docker-repository-zena-vs-noble)
7. [`docker-ce-cli`: kein Installationskandidat](#docker-ce-cli-kein-installationskandidat)
8. [`docker.io` vs. Docker Inc. (`docker-ce-cli`, Docker Desktop)](#dockerio-vs-docker-inc-docker-ce-cli-docker-desktop)
9. [Docker Desktop: lokale `.deb` zuverlässig installieren](#docker-desktop-lokale-deb-zuverlässig-installieren)
10. [Einmalblock: ASUS-Repo entfernen + Grafana migrieren](#einmalblock-asus-repo-entfernen--grafana-migrieren)
11. [Diagnose-Befehle (Schnellreferenz)](#diagnose-befehle-schnellreferenz)
12. [Bezug zum Piinstaller-Repo](#bezug-zum-piinstaller-repo)

---

## APT-Meldungen kurz erklärt

| Präfix | Bedeutung |
|--------|-----------|
| **E:** | Fehler; Aktion schlägt fehl oder Depot wird abgelehnt. |
| **W:** | Warnung; Update läuft oft weiter, sollte aber behoben werden. |
| **N:** | Hinweis (häufig unkritisch, z. B. fehlende Architektur im Depot). |

---

## Cursor-APT-Repository: `NO_PUBKEY 42A1772E62E492D6`

**Symptom:** `GPG-Fehler … NO_PUBKEY 42A1772E62E492D6`, Depot „nicht signiert“.

**Ursache:** Öffentlicher Schlüssel von Anysphere fehlt im für apt genutzten Keyring.

**Lösung:**

```bash
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://downloads.cursor.com/keys/anysphere.asc | sudo gpg --dearmor -o /etc/apt/keyrings/cursor-anysphere.gpg
sudo chmod 644 /etc/apt/keyrings/cursor-anysphere.gpg
echo 'deb [arch=amd64,arm64 signed-by=/etc/apt/keyrings/cursor-anysphere.gpg] https://downloads.cursor.com/aptrepo stable main' | sudo tee /etc/apt/sources.list.d/cursor.list
sudo apt update
```

**Fingerprint (Kontrolle):** Schlüssel zeigt u. a. `Anysphere Inc` und endet auf `42A1772E62E492D6`.

---

## Grafana: Warnung „Schlüssel in trusted.gpg“

**Symptom:** `Schlüssel ist im veralteten Schlüsselbund trusted.gpg gespeichert` für `packages.grafana.com`.

**Ursache:** Früher mit `apt-key` o. Ä. global eingetragen; apt empfiehlt `signed-by` + `/etc/apt/keyrings/`.

**Lösung:** Key nach `/etc/apt/keyrings/grafana.gpg`, Quelle mit `signed-by=` (siehe [Einmalblock](#einmalblock-asus-repo-entfernen--grafana-migrieren)).

**Hinweis:** Wenn die Warnung **trotzdem** bleibt, kann derselbe Schlüssel **zusätzlich** noch in `/etc/apt/trusted.gpg` liegen – dann gezielt bereinigen (z. B. `apt-key list`, veraltete Einträge entfernen; je nach Distribution leicht unterschiedlich).

---

## Google Chrome: `main/binary-i386` wird übersprungen

**Symptom:** `N: Das Laden … main/binary-i386/Packages wird übersprungen … unterstützt i386 nicht`.

**Bewertung:** **Unkritisch** – das Google-Repo liefert nur amd64.

**Optional abschaffen:** In der Chrome-`.list`/`.sources` nur amd64 anfordern, z. B. `deb [arch=amd64 signed-by=…] https://dl.google.com/linux/chrome/deb/ stable main` (Pfad zum Keyring ggf. anpassen).

---

## `repo.asus-linux.org`: tot, DNS, Alternativen

**Symptom:** `repo.asus-linux.org konnte nicht aufgelöst werden` / `Fehl … InRelease`.

**Feststellung:** Öffentliches DNS liefert für `repo.asus-linux.org` typischerweise **NXDOMAIN** – der Hostname ist **nicht mehr vergeben**; das ist kein reines „Netzwerk weg“, sondern ein **totes Depot**.

**Maßnahme auf dem System:** Datei unter `/etc/apt/sources.list.d/` entfernen oder Zeile auskommentieren, die `repo.asus-linux.org` enthält (z. B. früher `asus-linux.list`).

**Optional:** verwaistes Keyring ` /usr/share/keyrings/asus-linux.gpg` löschen.

**Offizielle Alternativen für `asusctl` (ohne Debian-APT vom Projekt):**

| Umgebung | Quelle |
|----------|--------|
| Fedora | COPR [lukenukem/asus-linux](https://copr.fedorainfracloud.org/coprs/lukenukem/asus-linux/) |
| openSUSE | [home:luke_nukem:asus](https://download.opensuse.org/repositories/home:/luke_nukem:/asus/) |
| Arch | [arch.asus-linux.org](https://arch.asus-linux.org/) |
| Debian/Ubuntu (offiziell) | **Kein** offizielles APT-Repo – [Quelltext / Anleitung](https://gitlab.com/asus-linux/asusctl), ggf. **DistroBox** mit unterstützter Distro ([Hinweis auf asus-linux.org](https://asus-linux.org/guides/asusctl-install/)) |
| Ubuntu (Community) | z. B. PPA `ppa:mitchellaugustin/asusctl` (Drittanbieter, siehe z. B. [mitchellaugustin.com](https://mitchellaugustin.com/asusctl.html)) |

---

## Linux Mint und Docker-Repository (`zena` vs. `noble`)

**Hintergrund:** Unter Mint liefert `/etc/os-release` oft `VERSION_CODENAME=zena` (Mint-Name). **Docker** bietet Pakete unter `https://download.docker.com/linux/ubuntu/` nur für **Ubuntu-Codenames** (z. B. `noble`), nicht für Mint-Namen.

**Regel:** In `/etc/apt/sources.list.d/docker.list` immer den Codename der **Ubuntu-Basis** verwenden (für Mint 22.x i. d. R. `noble`), z. B.:

```text
deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu noble stable
```

**Prüfen:** `Ubuntu_CODENAME` in `/etc/os-release` oder Inhalt von `/etc/upstream-release/lsb-release`.

---

## `docker-ce-cli`: kein Installationskandidat

**Symptom:** `apt-cache policy docker-ce-cli` zeigt keinen Kandidaten; `Paket docker-ce-cli ist nicht verfügbar`.

**Häufigste Ursachen:**

1. Docker-APT-Repo fehlt oder falscher **Ubuntu**-Codename in `docker.list` (siehe [Mint vs. noble](#linux-mint-und-docker-repository-zena-vs-noble)).
2. `apt update` schlägt wegen **anderer** defekter Depots teilweise fehl – trotzdem prüfen, ob `https://download.docker.com/linux/ubuntu …` **OK** ist.

**Repo einrichten (Ubuntu noble):**

```bash
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu noble stable" | sudo tee /etc/apt/sources.list.d/docker.list
sudo apt update
apt-cache policy docker-ce-cli
```

---

## `docker.io` vs. Docker Inc. (`docker-ce-cli`, Docker Desktop)

**Kontext:** Paket **`docker.io`** kommt aus Ubuntu/Mint-Repos; **`docker-ce-cli`** / **`docker-ce`** von Docker Inc. kommen von **download.docker.com**. Docker Desktop (`.deb`) hängt von **`docker-ce-cli`** (und weiteren Komponenten) ab.

**Typischer Wechsel:** Entfernen von `docker.io`, danach Installation von `docker-ce-cli` (und ggf. Plugins) aus dem Docker-Repo; anschließend Docker Desktop mit **vollem Pfad** zur `.deb` (siehe unten).

**Hinweis:** Beim Entfernen von `docker.io` werden Dienste angehalten; Daten unter `/var/lib/docker` bleiben in der Regel erhalten – trotzdem vor wichtigen Daten **Backup**/Ruhestand beachten.

---

## Docker Desktop: lokale `.deb` zuverlässig installieren

**Symptom:** `Hinweis: »docker-desktop« wird an Stelle von »/tmp/docker-desktop-amd64.deb« gewählt`.

**Ursache:** apt interpretiert die Anfrage als **Paketname aus dem Index**, nicht als lokale Datei.

**Lösung:** **Vollständigen Pfad** angeben:

```bash
sudo apt install -y /tmp/docker-desktop-amd64.deb
```

(Pfad anpassen.) Alternativ `sudo dpkg -i …` und danach `sudo apt-get install -f -y`.

---

## Einmalblock: ASUS-Repo entfernen + Grafana migrieren

Ein Shell-Block für den Zielzustand (nach erfolgreichem `sudo` mit Passwort):

```bash
sudo bash -c '
set -e
rm -f /etc/apt/sources.list.d/asus-linux.list
install -d -m 0755 /etc/apt/keyrings
curl -fsSL https://apt.grafana.com/gpg.key | gpg --dearmor -o /etc/apt/keyrings/grafana.gpg
chmod 644 /etc/apt/keyrings/grafana.gpg
printf "%s\n" "deb [signed-by=/etc/apt/keyrings/grafana.gpg] https://packages.grafana.com/oss/deb stable main" > /etc/apt/sources.list.d/grafana.list
'
sudo apt update
```

Optional danach: `sudo rm -f /usr/share/keyrings/asus-linux.gpg`

---

## Diagnose-Befehle (Schnellreferenz)

```bash
# Welche Mint/Ubuntu-Codenames?
. /etc/os-release && echo "VERSION_CODENAME=$VERSION_CODENAME"
[ -f /etc/upstream-release/lsb-release ] && . /etc/upstream-release/lsb-release && echo "UPSTREAM=$DISTRIB_CODENAME"

# Wo steht welches Depot?
grep -rE 'asus-linux|grafana|docker\.com|cursor\.com' /etc/apt/sources.list /etc/apt/sources.list.d/ 2>/dev/null

# Paket sichtbar?
apt-cache policy docker-ce-cli docker-desktop

# DNS ASUS (Erwartung bei totem Host: kein A-Record / NXDOMAIN)
getent hosts repo.asus-linux.org || true
```

---

## Bezug zum Piinstaller-Repo

- **ASUS / Lüfter:** Nutzerdoku [ASUS_ROG_FAN_CONTROL.md](../ASUS_ROG_FAN_CONTROL.md); Installationslogik u. a. in `scripts/install-asusctl.sh` – dort wird historisch noch `repo.asus-linux.org` erwähnt; bei totem DNS greift der **Fallback (Build aus GitLab)** bzw. manuelle Anpassung. Diese FAQ dokumentiert den **System-/apt-Teil** unabhängig vom Script-Stand.
- **Erweiterung:** Weitere apt-Themen (z. B. Plex, VS Code, Cursor-Updates) können in **neuen Abschnitten** in dieser Datei oder als `docs/knowledge-base/…` ergänzt werden; Stichwort **„knowledge-base“** im Dateinamen erleichtert die Suche.
