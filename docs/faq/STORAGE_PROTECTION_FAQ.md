# FAQ: Storage-Schutz / Storage protection

## Warum wird mein Laufwerk blockiert? / Why is my drive blocked?

**DE:** Setuphelfer schreibt nur unter fest definierten Pfaden (z. B. `/mnt/setuphelfer/…`, vorbereitete USB-Mounts unter `/mnt/pi-installer-usb`, Rescue-Staging unter `/tmp/setuphelfer-rescue-*`). Laufwerke unter `/media/` oder `/run/media/` sind für Schreibbackups **nicht** vorgesehen — dort greifen Desktop-Automounts und hohe Verwechslungsgefahr mit System- oder Windows-Platten.

**EN:** Setuphelfer only writes under fixed path prefixes (e.g. `/mnt/setuphelfer/…`, prepared USB mounts under `/mnt/pi-installer-usb`, rescue staging under `/tmp/setuphelfer-rescue-*`). Drives under `/media/` or `/run/media/` are **not** approved write targets — desktop automounts and confusion with system or Windows disks are too likely.

**DE (Restore):** Dieselben Schutzregeln gelten auch für `mode=restore`: Zielpfade unter `/media`/`/run/media` werden mit `backup.restore_target_invalid` (typisch `STORAGE-PROTECTION-005`) abgewiesen.

**EN (Restore):** The same protection rules apply to `mode=restore`: target paths under `/media`/`/run/media` are rejected with `backup.restore_target_invalid` (typically `STORAGE-PROTECTION-005`).

---

## Warum sehe ich `STORAGE-PROTECTION-004`, obwohl ext4 unter `/mnt/setuphelfer/...` gemountet ist? / Why can `STORAGE-PROTECTION-004` happen even with ext4 under `/mnt/setuphelfer/...`?

**DE:** Bei `x-systemd.automount` kann `findmnt` zuerst einen **autofs-Layer** (`source=systemd-1`, `fstype=autofs`) zeigen und erst darunter das echte Blockgerät (z. B. `/dev/sda4`). Setuphelfer löst diesen Layer jetzt robust auf (`findmnt -T`, rekursive Prüfung, UUID-Symlink-Auflösung). Wenn trotzdem **keine eindeutige** Blockquelle gefunden wird, bleibt der harte Abbruch mit `STORAGE-PROTECTION-004` absichtlich bestehen.

**EN:** With `x-systemd.automount`, `findmnt` may show an **autofs layer** first (`source=systemd-1`, `fstype=autofs`) and the real block device only underneath (e.g. `/dev/sda4`). Setuphelfer now resolves this robustly (`findmnt -T`, recursive lookup, UUID symlink resolution). If no **unambiguous** block source can be derived, `STORAGE-PROTECTION-004` is intentionally kept.

---

## Warum erkennt Setuphelfer Windows-Laufwerke? / Why does Setuphelfer flag Windows drives?

**DE:** Es gibt keine sichere 100 %-Erkennung ohne BitLocker-Metadaten. Deshalb nutzen wir **Heuristiken**: z. B. vorhandenes `EFI/Microsoft/Boot` auf einem Mount oder die Kombination großer NTFS-Partitionen mit EFI/VFAT auf derselben Platte, wenn es **nicht** die Systemplatte (`/`) ist. Ziel ist, Datenverlust durch Schreibzugriff auf die falsche NVMe/SSD zu verhindern.

**EN:** There is no perfect offline detection without BitLocker metadata. We therefore use **heuristics**, e.g. `EFI/Microsoft/Boot` on a mounted volume, or large NTFS plus EFI/vfat-style partitions on the same disk when it is **not** the system disk (`/`). The goal is to prevent data loss from writing to the wrong NVMe/SSD.

---

## Wie mounte ich eine externe NVMe fuer HW1-Tests? / How do I mount external NVMe for HW1 tests?

**DE:** Desktop-Pfade unter `/media/…` sind fuer Setuphelfer-**Schreib**zugriffe gesperrt. NVMe-Partition stattdessen nach **`/mnt/setuphelfer/backups`** (oder ein Unterverzeichnis) einbinden, Besitzer **`root:setuphelfer`**, Modus **0770**. Installer bzw. `debian/postinst` legen die Verzeichnisse an; bei manuellem Mount: `mount /dev/nvmeXnYpZ /mnt/setuphelfer/backups` nur, wenn der Punkt leer ist — danach `chown root:setuphelfer` und `chmod 0770` auf den Mountpoint (als root). Backend neu starten.

**EN:** Desktop paths under `/media/…` are blocked for Setuphelfer **writes**. Mount the NVMe partition to **`/mnt/setuphelfer/backups`** (or a subdirectory), owner **`root:setuphelfer`**, mode **0770**. The installer / `debian/postinst` create the directories; for manual mounts use root to fix ownership/mode on the mountpoint, then restart the backend.

---

## Warum schlägt `mount` mit `gid=setuphelfer` bei ext4 fehl? / Why does `mount` with `gid=setuphelfer` fail on ext4?

**DE:** Optionen wie **`gid=`** und **`umask=`** sind **keine** gültigen Mount-Optionen für das native Linux-Dateisystem **ext4** (im Gegensatz zu FUSE-Treibern für **NTFS**/**exFAT**). Der Kernel meldet dann typischerweise *Falscher Dateisystemtyp* / *bad option*. **Lösung:** ext4 mit `mount` **ohne** diese Optionen einhängen, danach **`chown root:setuphelfer`** und **`chmod 0770`** auf den Mountpunkt. Details: **`docs/knowledge-base/test-evidence/HW_EXEC_1_REPEAT_INSTRUCTIONS.md`**.

**EN:** Options like **`gid=`** and **`umask=`** are **not** valid mount options for native Linux **ext4** (unlike FUSE drivers for **NTFS**/**exFAT**). You then typically see *wrong fs type* / *bad option*. **Fix:** mount ext4 **without** those options, then run **`chown root:setuphelfer`** and **`chmod 0770`** on the mountpoint. Details: **`docs/knowledge-base/test-evidence/HW_EXEC_1_REPEAT_INSTRUCTIONS.md`**.

---

## Warum blockiert NoNewPrivileges `sudo` im Backend — und warum ist das trotzdem richtig? / Why does NoNewPrivileges block `sudo` in the backend — and why is that still correct?

**DE:** Der Dienst laeuft mit **`NoNewPrivileges=true`** (systemd), damit **Privilegieneskalation** (z. B. setuid-`sudo`) im Prozess nicht moeglich ist — das erhoeht die Sicherheit. **Schreib-Backups** auf freigegebene Ziele unter **`/mnt/setuphelfer/…`** sollen deshalb **ohne sudo** laufen (Backend-Nutzer mit Gruppe `setuphelfer`). Ein pauschaler **sudo-Check** vor jedem Backup widerspricht diesem Modell und scheitert zu Recht unter NNP. Nur Operationen, die **wirklich** Root brauchen (z. B. Full-System-Backup-Gate), sollten weiterhin ein sudo-Erfordernis melden (`backup.sudo_required` / bei NNP **`backup.sudo_blocked_by_nnp`** mit **`SYSTEMD-NNP-031`**).

**EN:** The service runs with **`NoNewPrivileges=true`** so **privilege escalation** (e.g. setuid `sudo`) cannot occur — that improves safety. **Write backups** to approved targets under **`/mnt/setuphelfer/…`** are therefore meant to run **without sudo** (backend user with `setuphelfer` group). A blanket **sudo check** before every backup conflicts with that model and correctly fails under NNP. Only steps that **genuinely** need root (e.g. full-system backup gate) should keep reporting sudo requirements (`backup.sudo_required`, or under NNP **`backup.sudo_blocked_by_nnp`** with **`SYSTEMD-NNP-031`**).

---

## Warum sichert `type=data` nicht automatisch alle Benutzerverzeichnisse unter `/home`? / Why doesn’t `type=data` automatically back up all `/home` user directories?

**DE:** `type=data` ist ein **Service-Context-Backup** ohne sudo. Deshalb wird nur das Home des **effektiven Dienstnutzers** berücksichtigt (z. B. `Path.home()` aus dem laufenden Backend-Kontext), plus klar definierte optionale Quellen. Fremde Homes unter `/home/<anderer-user>` werden nicht automatisch aufgenommen. So bleibt das Verhalten reproduzierbar und es entstehen keine versteckten Privileg-Abhängigkeiten.

**EN:** `type=data` is a **service-context backup** without sudo. It therefore uses only the effective service user’s home (e.g. `Path.home()` in backend runtime), plus explicitly defined optional sources. Other users’ homes under `/home/<other-user>` are not auto-included. This keeps behavior reproducible and avoids hidden privilege dependencies.

---

## Warum nutzen HW-Tests eine explizite Testdatenquelle? / Why do HW tests use an explicit test data source?

**DE:** Auf gehärteten Systemen (z. B. `ProtectHome=yes`) kann das Service-Home absichtlich nicht lesbar sein. Damit HW-Läufe reproduzierbar bleiben, wird für `type=data` eine kontrollierte Quelle unter `/mnt/setuphelfer/...` verwendet (z. B. `/mnt/setuphelfer/test-data`) und per `SETUPHELFER_DATA_BACKUP_SOURCES` gesetzt. So wird kein sudo benötigt und es gibt keine implizite Abhängigkeit von `/home`.

**EN:** On hardened systems (e.g. `ProtectHome=yes`), the service home may be intentionally unreadable. To keep HW runs reproducible, `type=data` uses a controlled source under `/mnt/setuphelfer/...` (e.g. `/mnt/setuphelfer/test-data`) configured via `SETUPHELFER_DATA_BACKUP_SOURCES`. This avoids sudo and removes hidden dependency on `/home`.
