# Setuphelfer Rettungsstick — Architektur (DE)

## Ziel

Der **Setuphelfer Rettungs-/Installationsstick** ist ein kontrolliert bootfähiges Live-System, das Hardware und Speicher read-only einordnet, Backups findet und prüft, **Restore nur als Preview** vorbereitet und alle Schritte **evidence-basiert** dokumentiert. Er ist kein generischer Linux-Desktop und kein unbegrenzter Experimentierraum.

## Abgrenzung

| Modus | Zweck |
|--------|--------|
| **Rescue** | Diagnose, Backup-Fund, Verify, Restore-Preview, Write-Safety, Evidence — **keine** automatischen Reparaturen oder Systemwrites auf interne Platten in der frühen Phase. |
| **Installer** | Kontrolliertes Aufsetzen eines Systems aus definierten Quellen — **eigenes** Gate und Release-Zyklen; nicht Gegenstand des aktuellen MVP-Strangs. |
| **Provisioning** | Späterer Layer für gezieltes Bereitstellen — klar getrennt vom Rescue-MVP. |

## Basisdistribution

**Debian Live** (stable, `live-build`) ist die empfohlene Grundlage: hohe Hardware- und Paketkompatibilität, vorhersagbare `apt`-Welt, gut passend zum bestehenden Setuphelfer-Backend (Python, systemd-Dokumentation, langfristige Sicherheitsupdates).

## Komponenten

1. **Live OS** — schlankes Debian-Live-Image (amd64 zuerst), optionale minimale GUI.
2. **Setuphelfer Backend** — als Dienst im Live-System (lokal erreichbar).
3. **Setuphelfer Frontend** — lokal (Browser/Kiosk optional).
4. **Inspect Engine** — read-only Block-, Mount-, Netzwerk- und Boot-Plausibilitäten.
5. **Backup / Verify / Restore Preview** — bestehende API- und Safety-Pfade; kein Restore-Execute im MVP.
6. **Device Classification** — interne/externe Medien, Risiko-Flags, keine automatischen Schreibentscheidungen.
7. **Netzwerk / Fernhilfe** — Statusanzeige im MVP; SSH-Hilfe optional und standardmäßig restriktiv.
8. **Evidence Store** — Handoff-JSON, Logs, Export — konsistent mit der bestehenden Evidence-Kette.

## Boot-Modi

- **UEFI** — primärer Zielpfad für amd64-Laptops.
- **Legacy BIOS** — später; nicht MVP-blockierend.
- **Secure Boot** — zunächst **review_required** (Signatur/Shim-Strategie, Testhardware).

## Betriebsmodi (Roadmap)

- **Diagnosemodus** — Inspect + Klassifikation.
- **Backup-Finder** — gezielte Suche und Metadaten/Manifest-Prüfung.
- **Restore-Preview** — nur Preview mit Safety-Gates.
- **Recovery-Assistent** — geführte Schritte ohne automatische Writes.
- **Installationsmodus** — später; strikt separat geschaltet.

## Leitplanken

Kein produktives ISO in dieser Phase, kein `dd` auf USB, kein `mkfs`, kein Bootloader-Rewrite ohne separates Gate — siehe `docs/developer/RESCUE_STICK_BUILD_SAFETY_POLICY.md`.
