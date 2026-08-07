# ASUS G513QM — ASUS-01 Ergebnisbericht (km/h)

Quelle: `SETUP_LOGS/.../20260807_162137_boot`  
Profil: **ASUS-01** (kein `nomodeset`, NVIDIA/nouveau blacklisted, Text/TUI)

## Urteil

**ASUS-01 bestanden.** Internes Display läuft über **AMD Cezanne + amdgpu KMS**.
Das Panel ist nicht tot — unter ASUS-00 war KMS absichtlich aus (`nomodeset`).

## Messwerte (Pass-Kriterien)

| Kriterium | Ergebnis |
|---|---|
| `amdgpu` an `06:00.0` | **ja** (`Kernel driver in use: amdgpu`) |
| Framebuffer | **`amdgpudrmfb`** (vorher EFI VGA) |
| Connector | **`eDP-1 = connected`**, HDMI-A-1 disconnected |
| Nouveau/NVIDIA aktiv | **nein** (blacklist greift) |
| GUI erzwungen | **nein** (`kiosk=0`, UI-Unit skipped) |
| TUI | `main_menu` |
| Failed units | 0 |

## Vergleich ASUS-00 → ASUS-01

| | ASUS-00 | ASUS-01 |
|---|---|---|
| Cmdline | `nomodeset` | ohne nomodeset + NVIDIA blacklist |
| FB | EFI VGA | amdgpudrmfb |
| AMD gebunden | nein | ja |
| eDP | nicht als DRM | connected |

## Zusatz

- ATPX/`vga_switcheroo` erkannt (Hybrid-MUX-Pfad vorhanden)
- NVIDIA `01:00.0` ohne Treiberbindung (gewollt in diesem Profil)
- Ethernet weiterhin DHCP ok; Telemetrie-Health ok, Push-ACK weiter offen

## Nächster Schritt

**ASUS-02 AMD GUI** — eine Variable: GUI/Kiosk auf dem jetzt bewiesenen AMD-DRM-Pfad.
Fail → TUI-Fallback / ASUS-00 oder ASUS-RECOVERY dokumentieren.
