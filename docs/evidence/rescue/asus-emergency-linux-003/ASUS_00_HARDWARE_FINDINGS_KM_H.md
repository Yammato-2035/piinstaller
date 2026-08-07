# ASUS G513QM — ASUS-00 Ergebnisbericht (km/h)

Quelle: `SETUP_LOGS/setuphelfer/diagnostics/20260807_161048_boot`  
Profil: **ASUS-00** (`nomodeset`, Text/TUI, kein Kiosk)

## Urteil in einem Satz

Der Rechner bootet, speichert Diagnose, Netz und Stick funktionieren;
**die interne Hybrid-GPU-Grafikstrecke ist unter ASUS-00 absichtlich totgeschaltet** —
deshalb sagt ASUS-00 nichts über „Display kaputt“, sondern nur: Baseline ok, weiter zu ASUS-01.

## Was steht (grün)

1. **Boot/TUI:** Startassistent auf `main_menu`, keine failed units.
2. **Persistenz:** Diagnose auf Stick (`persistent_to_stick=true`), SquashFS-Hash ok.
3. **CPU/RAM:** Ryzen 9 5900HX, ~30 GiB RAM, kein Speicher-Alarm.
4. **Netz verdrahtet:** Realtek RTL8111 (`enp2s0`) DHCP `192.168.178.103`, Default-Route ok.
5. **WLAN-Hardware:** MediaTek MT7921 (`mt7921e`) + Firmware geladen, rfkill frei; nur nicht verbunden (Ethernet aktiv).
6. **NVMe sichtbar:** 2× Samsung 970 EVO Plus 2 TB (`nvme0`, `nvme1`), SMART-fähig, Kernel erkennt beide.
7. **USB/Eingabe:** ASUS N-KEY, Stick erkannt.

## Was das Problem ist (rot / Kernbefund)

### 1) Hybrid-GPU ohne KMS-Treiberbindung (unter diesem Boot)

| Gerät | PCI | Module vorhanden | Kernel driver in use |
|---|---|---|---|
| NVIDIA RTX 3060 Mobile (GA106M) | `01:00.0` | `nouveau` | **keiner** |
| AMD Cezanne iGPU | `06:00.0` | `amdgpu` | **keiner** |

- `/proc/fb` = nur **`EFI VGA`**
- dmesg: `Booted with the nomodeset parameter. Only the system framebuffer will be available`
- `amdgpu` **nicht geladen**; `nouveau` geladen (Use-Count 0), aber **nicht gebunden**
- VGA-Arbiter: erst NVIDIA als Boot-VGA, dann **AMD überschreibt** als Boot-VGA

**Bedeutung:** Unter ASUS-00 ist „keine GUI / kein normales DRM“ **kein Hardwaredefekt-Beweis**,
sondern Folge von `nomodeset` + Safe-Profil. Ob AMD-KMS auf dem Panel geht, misst erst **ASUS-01**.

### 2) PCIe-Bandbreite GPU (Hinweis, kein Showstopper)

- NVIDIA-Link: effektiv **PCIe 3.0 x8** (statt x16-fähig) — typisch MUX/Hybrid, dokumentieren.
- AMD-iGPU-Link: effektiv **PCIe 3.0 x16** am internen Bridge.

### 3) Telemetrie

- Health-URL erreichbar (`telemetry_health_ok=true`)
- Assistent: `telemetry_ok=false` → **kein erfolgreicher Payload-ACK** in dieser Session
  (Spool/Evidence lokal vorhanden; Push nicht abgeschlossen)

### 4) Nebenbefunde (gelb)

- ACPI Firmware Bug: `_OSI(Linux)` ignored (üblich, nicht ursächlich für Panel)
- `SETUP_LOGS` einmal „not properly unmounted“ (fsck-Hinweis, Daten trotzdem geschrieben)
- Backend-Warnungen: RO-FS `/etc/setuphelfer` — Rescue-erwartet, kein Host-Defekt
- Onboard LAN in DMI als Disabled gelistet — irrelevant, Realtek-PCIe-LAN arbeitet

## Was ASUS-00 bewusst NICHT beantwortet

- Ob internes Display über **amdgpu** geht
- Ob MUX/Hybrid den Panel-Pfad blockiert
- Ob proprietary NVIDIA nötig wäre
- Ob Windows/BitLocker/NVMe-Inhalt ok ist (nur Geräteerkennung, kein Write/Verify der OS-Partition)

## Gate-Entscheidung

| Profil | Status |
|---|---|
| ASUS-00 Baseline | **bestanden** (TUI + Capture + Netz + Stick) |
| ASUS-01 AMD Discovery | **als Nächstes zwingend** — eine Variable: `nomodeset` weg, NVIDIA/nouveau blacklisten, Textmodus behalten |
| ASUS-02 GUI | erst wenn ASUS-01 DRM-Karten zeigt |

### Pass-Kriterien ASUS-01 (messbar)

- `amdgpu` geladen und an `06:00.0` gebunden
- `/dev/dri/card*` vorhanden (nicht nur EFI-FB)
- `nouveau`/`nvidia*` **nicht** aktiv am Panel-Pfad
- TUI bleibt bedienbar; kein GUI-Zwang

### Fail → ASUS-RECOVERY

- Blackscreen ohne TTY, oder kein DRM nach Timeout, oder System hängt hart

## Nächster physischer Schritt (ein Befehl mental)

GRUB: **nur ASUS-01 AMD DISCOVERY** booten. Nicht ASUS-02. Nicht quiet-Kosmetik.
