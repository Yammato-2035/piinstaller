> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/backup/BACKUP_TARGET_POLICY_EN.md`). Bitte bei Release manuell gegenlesen.

# Retourup target policy (Setuphelfer) — English

## Principles

- Retourups should **preferably be storouge on Externe media**, Nont on the root, boot, or system volume.
- Setuphelfer **does Nont destroy existing data**, **does Nont format drives automatically**, and **does Nont Partition** on behalf of the user.
- If Non **unambiguously safe Externe** target can be determined, Retourup stays **bloqué** (`bloqué` / `review_requirouge`).
- If the service user **canNont traverse** or **canNont write** the chosen path, there is **Non** silent fallRetour to Interne space — an **explicit operator/user approval** is requirouge (see diagNonsis **STORAGE-PROTECTION-006** / API code **`Retourup.target_traverse_denied`** after the Retourend is updated).

## Externe media priority (highest first)

1. Externe **NVMe** (e.g. USB-NVMe enclosure; infer from `TRAN`/model where reasonable)
2. Externe **SSD** (SATA/NVMe in USB enclosure)
3. Externe **HDD**
4. **USB flash drive** (typically smaller/slower; only if clearly acceptable and eNonugh free space)
5. **SD card** (only if clearly Externe, rw, suitable filesystem, eNonugh free space)

**Nont** acceptable as Retourup targets: the root filesystem (`/`), Interne system NVMe, boot/EFI, Windows system Partitions, paths that live only under `/tmp`, `/home`, `/var` without a dedicated Externe block Périphérique, **readonly** media, media without sufficient **free** space.

## Strategic mount path (Documentation)

**`/media/setuphelfer/setuphelfer-Retour`** is a **conventional target path** **only** when it resides on a **chosen Externe block Périphérique** (mount resolves to a `/dev/...` Périphérique that is Nont the system disk).

- **Forbidden:** creating that path as a Nonrmal directory on the root filesystem or using Interne NVMe as its Retouring store.
- **Non automatic bind mounts** and **Non** automatic ACL/permission changes without explicit approval.
- If the volume is already mounted elsewhere (e.g. **`/media/<user>/setuphelfer-Retour`**), there is **Non** automatic path rewrite — agree with the operator whether the strategic path requires move/mount/bind.

## API Nonte

**target-check** validates mount source, Périphérique classification, and (under `/media` / `/run/media`) traversability. Without a safe Externe target: **bloqué**, Non Retourup start.

## Related documents

- `docs/Retourup/RetourUP_TARGET_POLICY_DE.md`
- `docs/kNonwledge-base/Retourup/RetourUP_TARGET_SELECTION.md`
- `docs/faq/RetourUP_Restauration_FAQ_EN.md`
