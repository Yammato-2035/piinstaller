# Plan — Multi-Distro Linux-Install vom Rettungsstick + ASUS ROG Sofortpfad

**Stand:** 2026-07-25  
**Status:** Plan (keine destruktive Execute-Freigabe in diesem Dokument)  
**Orchestrierung ASUS-Fall:** Entwicklungsrechner (Dev-Laptop) → Stick (Execute unter Gates) → IONOS Telemetrie/Diagnostik

---

## 1. Produktziel (korrigiert)

Der Rettungsstick soll **dauerhaft** mehrere Linux-Installationen führen können — nicht nur Mint.

### 1.1 Distro-Matrix (Ziel: 3–4 Installationsprofile)

| Profil-ID | Produkt | Priorität | Bemerkung |
|-----------|---------|-----------|-----------|
| `linux_mint` | Linux Mint (aktuelle unterstützte Edition, Desktop) | **P0 — ASUS jetzt** | Erste produktive Zielinstallation |
| `ubuntu_server_lts` | Ubuntu **LTS** Server | P1 | Langfrist-Support-Server |
| `ubuntu_server` | Ubuntu Server (nicht-LTS / aktuelle Server-Linie, falls von Canonical getrennt geführt) | P1 | Explizit neben LTS als eigenes Profil |
| `debian` | Debian (Installationspfad; Live bleibt Boot-/Rescue-Basis) | P1 | Debian **Live** = Stick-Laufzeit; Debian **Install** = Assistenten-Ziel |

**Klarstellung:**

- **Debian Live** = Betriebssystem des Rettungssticks (immer bootfähig).
- **Debian Install / Mint / Ubuntu Server LTS / Ubuntu Server** = vom Assistenten installierbare Zielsysteme.
- Weitere Distros erst nach stabilen vier Profilen.

### 1.2 Wer führt die Installation aus?

| Komponente | Rolle |
|------------|--------|
| **Installationsassistent** (Rescue UI) | Distro wählen, ISO verifizieren, Plan bestätigen, Freigaben einholen |
| **Partitionshelfer** | Layout planen, Hardstops, nach Freigabe Partitionen anlegen/formatieren (Phase-2-Write nur unter Gates) |
| **Rettungsstick Live** | Ausführungsumgebung — Installation startet **aus der laufenden Stick-Session** |
| **Dev-Laptop** (ASUS-Fall) | Orchestrierung, Telemetrie-Lab, Freigaben, Evidenz-Sammlung, Cloud-Anbindung |
| **IONOS Telemetrie- + Diagnostikserver** | Fehlersuche, redigierte Payloads, Hardware-/BIOS-/Install-Failure-Lernen |

### 1.3 Freigabe vor Execute (Pflicht)

Execute (Partition write / Install) nur wenn **mindestens eine** der folgenden Bedingungen erfüllt ist **und** die Operator-Bestätigung vorliegt:

1. **Explizite Freigabe** des Operators (Doppelbestätigung + Phrase + TTL), **oder**
2. **Erfolgreiches Backup** der betroffenen Medien (Verify bestanden) + Freigabe des Install-Plans.

Ohne Freigabe **oder** ohne Backup bei Datenmedien: nur Diagnose + Dry-Run-Plan.

---

## 2. ASUS ROG Sofortpfad (jetzt)

### 2.1 Auftrag

| Anforderung | Umsetzung |
|-------------|-----------|
| Keine weitere Umsteck-Session | Stick bleibt gebootet; alles aus laufender Live-Session |
| Ziel | **Zweite NVMe** (`linux_target`) |
| Distro | **Linux Mint** |
| Zusatz | alle benötigten **Setuphelfer-Komponenten** auf dem neuen System |
| Orchestrierung | **Entwicklungsrechner** (nicht manuell „nur Stick-Menü“) |
| Cloud | Telemetrie- + Diagnostikserver IONOS **weiter ausbauen und für Fehlersuche nutzen** |

### 2.2 Rollenbindung Disks (ASUS)

| Rolle | Disk | Default |
|-------|------|---------|
| `windows_system` | bestehende Windows-NVMe | **read-only / write blocked** |
| `linux_target` | zweite NVMe | Mint-Ziel nach Bind + Freigabe |
| `rescue_usb` | Stick | nur Payload/Updater-Gates |

Bindung über stabile Identitäten (Serien-Hash / Partitionstabelle / Größe) — **nicht** allein `nvme0n1`/`nvme1n1`.

### 2.3 Ablauf ASUS (orchestriert vom Dev-Laptop)

```text
Dev-Laptop
  │  Phase 0 / Lab-Gates, Telemetrie-Health (Lab + IONOS)
  │  Assessment-Auftrag an Stick (read-only)
  ▼
Rettungsstick (bereits gebootet auf ASUS ROG)
  │  Assessment V2 + AER/BIOS/NVMe-Rollen
  │  Install-Failure-Klassifikation → Telemetrie (redigiert)
  │  ISO Mint: Cache/Verify auf Stick oder SETUP_LOGS
  │  Partitionshelfer: Layout-Plan für linux_target (dry-run)
  │  Backup-Gate ODER Freigabe-Gate
  │  Partitionshelfer execute (nur linux_target)
  │  Mint-Install aus Live-Session (Handoff oder orchestriert)
  │  Setuphelfer-Komponenten nachinstallieren/bootstrap
  │  Post-Verify + Evidence → Dev-Laptop + Cloud
  ▼
IONOS Telemetrie / Diagnostik
  │  Quarantine/Accepted, Issue-Codes, BIOS/Hardware-Hints
  ▼
Dev-Laptop
     Review, nächster Schritt (BIOS-Session falls nötig)
```

### 2.4 Setuphelfer auf dem neuen Mint-System

Nach erfolgreicher Mint-Basisinstallation (Mindestumfang, anpassbar):

- Setuphelfer Desktop-/Client-Paket oder Bootstrap-Skript aus verifiziertem Bundle
- Backend-Dienst nur wenn Edition/Profil das vorsieht (nicht „Cloudserver“ auf dem Laptop)
- Telemetrie-Client-Contracts (opt-in), Diagnose-Hooks
- Keine Server-Secrets vom Stick auf das Zielsystem schreiben

### 2.5 Explizit **nicht** in der ASUS-Sofortphase

- Windows neu installieren
- BIOS auto-flashen (nur geführte Session / Anleitung + Evidenz)
- Wipe der Windows-NVMe
- Umstecken des Sticks für einen zweiten Boot-Workflow

---

## 3. Generischer Multi-Distro-Installationspfad (Produkt)

### 3.1 Contract-Schichten

```text
distro_profile (mint | ubuntu_server_lts | ubuntu_server | debian)
  → iso_policy (URL-Spiegel, SHA256, Signatur-Policy)
  → partition_profile (via Partitionshelfer Manifest)
  → install_executor (handoff | orchestrated)
  → post_bootstrap (Setuphelfer Komponenten-Set)
  → verify_boot
```

### 3.2 Zusammenspiel Assistent ↔ Partitionshelfer

1. Assistent: Distro + Zielrolle wählen  
2. Partitionshelfer: Scan → Hardstop → Layout-Preview  
3. Assistent: Backup-Status prüfen **oder** Freigabe einholen  
4. Partitionshelfer: Write nur nach Gate (`write_allowed`)  
5. Assistent: Installer starten (aus Stick-Live)  
6. Assistent: Post-Bootstrap Setuphelfer  
7. Assistent: Verify + Evidence + optional Telemetrie  

### 3.3 Ausführungsmodi

| Modus | Einsatz |
|-------|---------|
| **Handoff** | Offizieller Distro-Installer / Calamares mit vorbereitetem Layout |
| **Orchestrated** | Stick steuert Unattended (später, nach Handoff-Stabilität) |

ASUS-Sofortpfad: **Handoff oder kontrolliert orchestriert aus Live**, aber **ohne Umstecken**.

---

## 4. Cloud: Telemetrie + Diagnostik (IONOS) — Ausbau für Fehlersuche

### 4.1 Zweck im ASUS-/Install-Kontext

| Server | Nutzen |
|--------|--------|
| **Telemetrie** `telemetrie.setuphelfer.de` | Redigierte Assessment-/Install-Events, Quarantine bei fehlender Vereinbarung, Replay-Schutz |
| **Diagnostik** | Hardware-/BIOS-/AER-/Installer-Failure-Codes, Empfehlungen nach Human Review |

### 4.2 Orchestrierung Dev-Laptop

- Lab-Mocks (8100–8102) für Offline
- Gegen IONOS: Health/TLS zuerst (TEL-CLOUD-FIX), dann Ingest
- Dev-Laptop sendet **keine** Remote-Shell-Kommandos an den Stick; Stick **pullt** Freigaben/Tasks nur über bestehende allowlisted Task-Kanäle oder lokale Operator-API
- Keine Fernsteuerung / kein Command-Polling außerhalb dokumentierter Rescue-Task-Pull-Policy

### 4.3 Neue Issue-/Empfehlungscodes (Install)

- `bios_outdated_likely`
- `pcie_aer_flood_blocks_installer`
- `secure_boot_blocks_unsigned_iso`
- `nvme_role_bind_required`
- `install_iso_hash_mismatch`
- `partition_write_blocked_no_backup_or_approval`
- `linux_install_post_verify_failed`

---

## 5. Geführte BIOS-Session (weiterhin relevant)

Bleibt im Plan, aber **parallel/nachgelagert** zum Mint-Sofortpfad:

- Vergleich offizieller BIOS-Version
- Checkliste + Evidence
- **Kein Auto-Flash**
- Wenn Diagnose `bios_outdated_likely` → Dev-Laptop zeigt Session-Status; Operator entscheidet Timing (ggf. nach Mint, wenn Boot schon möglich)

---

## 6. Arbeitszüge (angepasst)

| Zug | Inhalt | Owner-Orchestrierung |
|-----|--------|----------------------|
| **A0** | Disk-Rollenbindung ASUS + Assessment + Telemetrie-Push (redigiert) | Dev-Laptop |
| **A1** | IONOS Telemetrie TLS/Health + Diagnostik-Preview für Install-Codes | Dev-Laptop + Cloud |
| **A2** | Mint ISO Cache/Verify auf Stick (ohne Umstecken) | Stick + Dev-Laptop |
| **A3** | Partitionshelfer Layout dry-run für `linux_target` | Stick |
| **A4** | Freigabe-Gate **oder** Backup-Gate → Partition Write | Operator + Stick |
| **A5** | Mint-Install aus Live-Session auf 2. NVMe | Stick |
| **A6** | Setuphelfer-Komponenten bootstrap auf Mint | Stick |
| **A7** | Post-Verify + Evidence → Dev + Cloud | Dev-Laptop |
| **B1** | Distro-Profile Ubuntu Server LTS / Ubuntu Server / Debian Install | Public Repo |
| **B2** | Generischer Assistent für 4 Profile | Public Repo |
| **C1** | Windows auf 2. NVMe (später, anderer Track) | später |

---

## 7. Definition of Done — ASUS Sofortpfad

- [ ] Stick-Session ununterbrochen (kein Umstecken für den Install-Workflow)
- [ ] Windows-NVMe unverändert
- [ ] Zweite NVMe: Linux Mint bootfähig
- [ ] Setuphelfer-Komponenten laut Bootstrap-Set vorhanden
- [ ] Freigabe **oder** Backup-Gate nachweisbar in Evidence
- [ ] Redigierte Diagnose-/Install-Events am Dev-Laptop und (soweit Health ok) IONOS
- [ ] Kein BIOS-Flash ohne separaten Operator-Auftrag

---

## 8. Hard Safety (unverändert gültig)

- Kein dd/mkfs/wipefs/parted-write ohne Partitionshelfer-Gates + Operator
- Kein Schreiben auf `windows_system` im ASUS-Sofortpfad
- Keine Remote-Kommandos vom Cloud-Server an den Stick
- Keine Secrets in Public Repo / Telemetrie-Payloads
- Analyse und Empfehlungen automatisch; Behebung nur lokal, nachvollziehbar, mit Evidence

---

## 9. Nächster Umsetzungsschritt (Empfehlung)

1. Feature-Branch von aktuellem `main`: `cursor/asus-mint-second-nvme-orchestrated-<suffix>`
2. Contracts: Distro-Matrix + Freigabe/Backup-Gate + Disk-Rollen
3. Port/Reuse von `origin/pi-rs-asus-win11-linux-001` wo passend
4. Dev-Laptop-Orchestrierungs-Skript/-API (lab send + cloud preview)
5. Erst nach grünem Dry-Run + expliziter Operator-Freigabe: Partition Write + Mint Execute

Dieses Dokument ersetzt die engere „nur Mint“-Annahme des vorherigen Plans und verankert Multi-Distro sowie Dev-Laptop-Orchestrierung + IONOS-Fehlersuche.
