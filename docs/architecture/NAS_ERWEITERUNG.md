# NAS-Bereich: Erweiterungsanalyse & Umsetzbarkeit

## Was bieten kommerzielle NAS-Anbieter (Synology, QNAP)?

| Bereich | Synology | QNAP | Kurzbeschreibung |
|--------|----------|------|------------------|
| **Dateifreigaben** | SMB, NFS, AFP, FTP | SMB, NFS, AFP, FTP | ✅ Bereits im PI-Installer (Samba, NFS, FTP) |
| **Duplikat-Finder** | Storage Analyzer | Teilweise/Forum | Scan, Duplikate melden, ggf. löschen |
| **Bildersuche** | Synology Moments (KI) | QuMagie/Photo Station (KI) | Gesichts-/Objekt-Erkennung, Suche, Alben |
| **Sortierung** | Automatisch nach Datum/Ort | Nach Personen, Ort, Timeline | Intelligente Kategorisierung |
| **Medienserver** | Plex/Video Station | Plex/Video Station | Video/Photo/Audio streaming |
| **Backup** | Hyper Backup | Hybrid Backup Sync | Snapshots, Versionsverlauf, Cloud |

---

## Open-Source-Lösungen für Linux/Raspberry Pi

### 1. Duplikat-Finder

| Tool | Typ | ARM64/Pi | Beschreibung |
|------|-----|----------|--------------|
| **Czkawka** | GUI + CLI | ✅ (Rust, cross-platform) | Schnell, Duplikate + ähnliche Bilder, leere Ordner, Temp-Dateien |
| **fdupes** | CLI | ✅ (apt) | Klassisch: MD5, Byte-Vergleich, rekursiv |
| **rdfind** | CLI | ✅ (apt) | Findet Duplikate, kann Hardlinks erstellen |
| **findimagedupes** | CLI | ✅ | Visuell ähnliche Bilder (inhaltbasiert) |

### 2. Foto-Management & Bildersuche

| Tool | Typ | Pi 4/5 | Beschreibung |
|------|-----|--------|--------------|
| **Immich** | Docker + Web + App | ✅ (Pi 4+ empfohlen) | Google-Photos-Alternative, Gesichtserkennung, Geo-Tags |
| **PhotoPrism** | Docker + Web | ✅ (4 GB RAM min) | Suche, Gesichter, Orte, KI-Tags |
| **Nextcloud Memories** | Nextcloud-Plugin | ✅ | Wenn Nextcloud bereits läuft; Photos + Erkennung |
| **Lychee** | Web | ✅ | Einfaches Fotomanagement, Alben |

### 3. Medienserver (Video/Audio/Photos)

| Tool | Typ | Pi 4/5 | Beschreibung |
|------|-----|--------|--------------|
| **Jellyfin** | Server + Clients | ✅ (Pi 4+ für Transcode) | Kostenlos, Video/Audio/Photos streaming |
| **Plex** | Server + Clients | ✅ | Sehr verbreitet, teils kostenpflichtig |
| **Emby** | Server + Clients | ✅ | Ähnlich Plex |
| **Navidrome** | Audio-only | ✅ | Musik-Server (Subsonic-kompatibel) |

### 4. Sortierung & Backup

| Tool | Typ | Beschreibung |
|------|-----|--------------|
| **rsnapshot** | CLI | Inkrementelle Backups, Snapshots |
| **Borg Backup** | CLI | Deduplizierung, Verschlüsselung |
| **Restic** | CLI | Schnelle Backups, Cloud-S3 |

---

## Umsetzbarkeit im PI-Installer

### 🟢 Gut umsetzbar (apt/apt + Scripts)

| Feature | Lösung | Aufwand | Vorschlag |
|---------|--------|---------|-----------|
| **Duplikat-Finder** | Czkawka oder fdupes installieren + Scan-Pfad konfigurieren | Mittel | Neuer Unterbereich „Duplikate & Aufräumen“ |
| **Einfacher Medienserver** | Jellyfin per Docker/apt | Mittel | Eigenes Modul oder Unterbereich NAS |
| **Backup auf NAS** | Integration mit Backup-Modul (Pfad = NAS-Share) | Gering | Backup-Modul erweitern |

### 🟡 Umsetzbar mit Docker

| Feature | Lösung | Aufwand | Vorschlag |
|---------|--------|---------|-----------|
| **Foto-Management** | Immich oder PhotoPrism (Docker) | Hoch | Optionales Modul „Foto-NAS“ |
| **Medienserver** | Jellyfin/Plex per Docker | Mittel | Wenn Docker schon im Stack |

### 🔴 Hoher Aufwand / Limitierungen

| Feature | Limitierung |
|---------|-------------|
| **KI-Bildersuche** | Immich/PhotoPrism bringen das mit; eigener KI-Service wäre sehr aufwändig |
| **Synology-ähnliche All-in-One-Oberfläche** | Eigenentwicklung unrealistisch; Kombination aus Tools besser |

---

## Empfohlene Erweiterungen für den NAS-Bereich

### Phase 1: Duplikat-Finder (prioritär)

1. **Czkawka** oder **fdupes** per apt installierbar machen
2. Backend: API z. B. `/api/nas/duplicates/scan` – Scan eines Pfads (z. B. NAS-Share)
3. Frontend: Pfad eingeben, Scan starten, Duplikate auflisten; Option: in Backup-Ordner verschieben statt löschen
4. Optional: Czkawka-GUI per Flatpak/AppImage starten (wie Mixer)

### Phase 2: Medienserver

1. **Jellyfin** als Option im NAS-Bereich
2. Installation: Docker oder `apt install jellyfin` (wenn im Repo)
3. Konfiguration: Media-Pfad auf NAS-Share zeigen, Server starten
4. Link zur Jellyfin-Weboberfläche

### Phase 3: Foto-Management (optional)

1. **Immich** oder **PhotoPrism** als Docker-Option
2. Einmalige Setup-Anleitung + Link zur Weboberfläche
3. Upload-Pfad auf NAS-Share

### Phase 4: Backup-Integration

1. Im Backup-Modul: Ziel „NAS-Share“ (SMB/NFS-Pfad) wählbar
2. Duplikate-Backup: Gefundene Duplikate in Unterordner des Backups verschieben statt löschen

---

## Technische Hinweise

- **Czkawka**: `apt install czkawka` oder von GitHub Releases; CLI: `czkawka_cli duplicate -d /pfad`
- **fdupes**: `apt install fdupes`; `fdupes -r /pfad` für rekursiven Scan
- **Jellyfin**: Docker-Image `jellyfin/jellyfin`; Port 8096
- **Immich**: Docker-Compose mit mehreren Services; benötigt PostgreSQL

---

## Nächste Schritte

- [x] **Phase 1 umgesetzt (v1.2.0.6):** Duplikat-Finder (fdupes) – siehe unten
- [ ] Phase 2: Medienserver (Jellyfin)
- [ ] Phase 3: Foto-Management (Immich/PhotoPrism)
- [ ] Phase 4: Backup-Integration

---

## Phase 1: Duplikat-Finder (implementiert)

- **Backend:** `POST /api/nas/duplicates/install` (fdupes installieren), `POST /api/nas/duplicates/scan`, `POST /api/nas/duplicates/move-to-backup`
- **Frontend:** NAS-Seite – Karte „Duplikate & Aufräumen“ mit Scan-Pfad, Backup-Pfad, Scan-Button, Verschieben-Button
- **Verhalten:** Pro Duplikat-Gruppe bleibt die erste Datei, die restlichen werden in den Backup-Ordner verschoben (nicht gelöscht)

---

**Version:** 1.1  
**Stand:** Februar 2026
