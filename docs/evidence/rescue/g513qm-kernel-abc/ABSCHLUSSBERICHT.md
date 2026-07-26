# ABSCHLUSSBERICHT — G513QM Kernel A/B/C Control + Out-of-Band KMS Capture

## Endstatus

```text
implemented_ready_for_g513qm_kernel_abc_physical_control
```

Physischer Status:

```text
physical_control_pending
```

Kein physischer Erfolg aus Unit-Tests abgeleitet.

---

## Workspace

```text
============================================================
WORKSPACE BESTÄTIGT
============================================================
Workspace: /tmp/piinstaller-install-assistant-001
Git-Root: /tmp/piinstaller-install-assistant-001
Repository: https://github.com/Yammato-2035/piinstaller.git
Branch: pi-rs-install-assistant-001
HEAD vorher: 4e171c6b0ecc4ab5ee5e7af4fe085d9aa727fcf7
HEAD nachher: c33433587eaf0f44ecfc10ebe6f95f6b805111b0
origin/main: b8651d3337bf30b4443a622fdf8a6c9dc2995df5
Remote: origin → Yammato-2035/piinstaller.git
Dirty-Tree: nur A/B/C-Phase-Dateien
Runtime-Gate: Exit 14 → Arbeitsmodus static_and_build_only
Port-8000-Smokes: nein
Telemetrie-accepted: nein
```

Bestehender Branch beibehalten (baut auf Install-Assistant / Hybrid-Rebuild auf).

---

## Kontrollimages

| Control | Version | Kernel | Quelle | SHA256 | Signatur | USB |
|---------|---------|--------|--------|--------|----------|-----|
| A | Mint 22.1 Cinnamon | 6.8-family (nach Boot prüfen) | kernel.org mirror | `ccf48243…` | GPG OK | **ISO noch nicht heruntergeladen** → kein USB-Write |
| B | Mint 22.3 Cinnamon | as shipped (nach Boot prüfen) | kernel.org mirror | `a081ab20…` | GPG OK | **ISO noch nicht heruntergeladen** → kein USB-Write |
| C | Setuphelfer Diagnose (mint-live) | aktuell 6.14.0-29 bis Remaster | Workspace + Stick-Pack | n/a | n/a | GRUB/Scripts: **Operator-Write empfohlen** (Auto-Write blockiert) |

Details: `CONTROL_IMAGE_VERIFICATION.md`, `control_matrix.json`.

Download A/B:

```bash
./scripts/rescue/g513qm-kernel-abc/verify-control-iso.sh control-a --download-iso
./scripts/rescue/g513qm-kernel-abc/verify-control-iso.sh control-b --download-iso
```

---

## Diagnoseimage (Control C)

| Element | Stand |
|---------|--------|
| Kernel | mint-live `6.14.0-29-generic` dokumentiert; Closure `documented`, Remaster ausstehend |
| Module/Firmware | AMDGPU + Firmware in Live vorhanden; NVIDIA-Blocker dokumentiert, nicht gelöst |
| Debugkonsole | `systemd.debug-shell=1` → tty9, **kein** `rescue.target`, kein sulogin |
| Netconsole | Receiver `scripts/rescue/g513qm-netconsole-receiver.sh` + Lab-JSON |
| pstore | zur Laufzeit prüfen; sonst `pstore_status=not_available` |
| Capture | `setuphelfer-gpu` + early-capture Skripte |
| GRUB | C1–C4 Einträge in `rescue_install_assistant_grub.py`; Default bleibt Basic Emergency |

---

## Sicherheitsnachweis

```text
Interne NVMe beschrieben: nein
Partitionierung: nein
Restore: nein
Windows-EFI verändert: nein
BitLocker verändert: nein
BIOS automatisch verändert: nein
Secure Boot verändert: nein
Linux-Installation gestartet: nein
```

---

## Testergebnisse

- `pytest` `test_g513qm_kernel_abc_control_v1.py` + hybrid contract: **16 passed**
- `./scripts/rescue/g513qm-kernel-abc/check-control-c-gates.sh`: **gates_passed**
- Version consistency: ok (Workspace)
- Referenz-ISO: Checksum+GPG OK; ISO-Dateien `not_available` → A/B USB Write blockiert bis Download

Offene Blocker:

1. Offizielle Control-A/B-ISOs noch nicht lokal vorhanden.
2. Stick-GRUB/Scripts-Update: Agent-Write auf USB wurde vom Auto-Review blockiert — Operator muss schreiben:

```bash
cd /tmp/piinstaller-install-assistant-001
python3 -c 'from backend.core.rescue_install_assistant_grub import generate_gabriel_install_grub_cfg as g; open("/tmp/g513qm-grub-abc.cfg","w").write(g())'
# nach Carrier-Gate (UUID 9BB9-A4A6 / Serial 24111412110686):
sudo cp /tmp/g513qm-grub-abc.cfg /media/…/SETUPHELFER/boot/grub/grub.cfg
./scripts/rescue/g513qm-kernel-abc/install-control-c-scripts-to-stick.sh /media/…/SETUP_LOGS
```

3. Systemd-Units im Live-Root brauchen Remaster für Autostart; bis dahin: tty9 + Skripte vom Pack.
4. Runtime-Gate Exit 14 unverändert.

---

## Operatoranweisung (physisch)

```text
1. Control A – offizielles Mint 22.1 (ISO verifiziert, eigener Stick)
2. Control B – offizielles Mint 22.3
3. Control C – Setuphelfer Debug/KMS Capture (C1 zuerst)
4. erst danach BIOS-335-Entscheidung
5. danach ggf. Wiederholung mit neuen Run-IDs
```

**A/B:** nur bis Desktop, keine Installation, keine Laufwerksauswahl.

**C:**

```text
Control C1 booten
→ Ctrl+Alt+F9 (Debugshell)
→ Run-ID notieren
→ Netconsole-Receiver auf Entwicklungsrechner starten
→ setuphelfer-gpu capture && status
→ setuphelfer-gpu load-amdgpu
→ Verhalten + Alive-Probes (Ping/Netconsole/LED)
→ setuphelfer-gpu finalize
```

Bei Schwarzbild: nicht sofort Totalausfall; Netz/Netconsole/Extern prüfen; bei Stillstand kalt, dann pstore/Evidence importieren.

---

## Entscheidung

Ohne physische A/B/C-Ergebnisse: **keine** Fall-1–7-Bewertung.

Zulässiger Endstatus dieser Phase: `implemented_ready_for_g513qm_kernel_abc_physical_control`.
