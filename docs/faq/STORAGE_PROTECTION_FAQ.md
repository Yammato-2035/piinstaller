# FAQ: Storage-Schutz / Storage protection

## Warum wird mein Laufwerk blockiert? / Why is my drive blocked?

**DE:** Setuphelfer schreibt nur unter fest definierten Pfaden (z. B. `/mnt/setuphelfer/…`, vorbereitete USB-Mounts unter `/mnt/pi-installer-usb`, Rescue-Staging unter `/tmp/setuphelfer-rescue-*`). Laufwerke unter `/media/` oder `/run/media/` sind für Schreibbackups **nicht** vorgesehen — dort greifen Desktop-Automounts und hohe Verwechslungsgefahr mit System- oder Windows-Platten.

**EN:** Setuphelfer only writes under fixed path prefixes (e.g. `/mnt/setuphelfer/…`, prepared USB mounts under `/mnt/pi-installer-usb`, rescue staging under `/tmp/setuphelfer-rescue-*`). Drives under `/media/` or `/run/media/` are **not** approved write targets — desktop automounts and confusion with system or Windows disks are too likely.

---

## Warum erkennt Setuphelfer Windows-Laufwerke? / Why does Setuphelfer flag Windows drives?

**DE:** Es gibt keine sichere 100 %-Erkennung ohne BitLocker-Metadaten. Deshalb nutzen wir **Heuristiken**: z. B. vorhandenes `EFI/Microsoft/Boot` auf einem Mount oder die Kombination großer NTFS-Partitionen mit EFI/VFAT auf derselben Platte, wenn es **nicht** die Systemplatte (`/`) ist. Ziel ist, Datenverlust durch Schreibzugriff auf die falsche NVMe/SSD zu verhindern.

**EN:** There is no perfect offline detection without BitLocker metadata. We therefore use **heuristics**, e.g. `EFI/Microsoft/Boot` on a mounted volume, or large NTFS plus EFI/vfat-style partitions on the same disk when it is **not** the system disk (`/`). The goal is to prevent data loss from writing to the wrong NVMe/SSD.
