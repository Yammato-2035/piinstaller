# Nginx-Boot-Fehler beheben

Wenn der Pi beim Boot hängt und `systemctl --failed` **nginx.service** als fehlgeschlagen zeigt:

## Häufig: „Address already in use“ (Port 80 belegt)

Fehlermeldung: `bind() to 0.0.0.0:80 failed (98: Address already in use)`  
→ Ein anderer Dienst (z.B. Apache, lighttpd, ein anderes Programm) nutzt Port 80, bevor nginx startet.

**Wenn nginx nicht gebraucht wird (z.B. nie konfiguriert):** nginx beim Boot deaktivieren:

```bash
sudo systemctl disable nginx
sudo systemctl stop nginx
```

Danach blockiert nginx den Reboot nicht mehr. Beim nächsten Neustart startet nginx nicht.

**Prüfen, was Port 80 belegt:** `sudo ss -tlnp | grep :80` oder `sudo lsof -i :80`

---

## 1. Warum nginx fehlschlägt prüfen

Auf dem Pi (per SSH):

```bash
sudo systemctl status nginx
sudo journalctl -u nginx.service -n 50 --no-pager
```

Typische Ursachen:
- **Konfigurationsfehler:** z.B. Syntax in `/etc/nginx/nginx.conf` oder in `/etc/nginx/sites-enabled/`
- **Port schon belegt:** z.B. 80 oder 443 von einem anderen Dienst
- **Fehlende Datei:** z.B. ein `include` zeigt auf eine nicht existierende Config

## 2. Nginx-Config testen

```bash
sudo nginx -t
```

Wenn hier ein Fehler ausgegeben wird (z.B. "syntax is wrong" oder "could not open ..."), die genannte Datei/Zeile anpassen.

## 3. Option A: Nginx reparieren

- Fehlende Config-Dateien anlegen oder fehlerhafte Zeilen in `/etc/nginx/` korrigieren.
- Danach: `sudo nginx -t` und `sudo systemctl restart nginx`.

## 4. Option B: Nginx beim Boot deaktivieren (wenn nicht benötigt)

Wenn du nginx vorerst nicht brauchst:

```bash
sudo systemctl disable nginx
sudo systemctl stop nginx
```

Nach dem nächsten Reboot startet nginx nicht mehr und blockiert den Boot nicht.

## 5. PI-Installer und Nginx

Falls nginx für den PI-Installer (Reverse Proxy) eingerichtet wurde: Config liegt oft unter `/etc/nginx/sites-enabled/` oder in `/etc/nginx/nginx.conf`. Nach Änderungen immer `sudo nginx -t` und dann `sudo systemctl restart nginx` ausführen.
