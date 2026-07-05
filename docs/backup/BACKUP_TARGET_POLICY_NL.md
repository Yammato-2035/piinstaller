> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/backup/BACKUP_TARGET_POLICY_EN.md`). Bitte bei Release manuell gegenlesen.

# Terugup target policy (Setuphelfer) — English

## Principles

- Terugups should **preferably be storood on Extern media**, Neet on the root, boot, or system volume.
- Setuphelfer **does Neet destroy existing data**, **does Neet format drives automatically**, and **does Neet Partitie** on behalf of the user.
- If Nee **unambiguously safe Extern** target can be determined, Terugup stays **geblokkeerd** (`geblokkeerd` / `review_requirood`).
- If the service user **canNeet traverse** or **canNeet write** the chosen path, there is **Nee** silent fallTerug to Intern space — an **explicit operator/user approval** is requirood (see diagNeesis **STORAGE-PROTECTION-006** / API code **`Terugup.target_traverse_denied`** after the Terugend is updated).

## Extern media priority (highest first)

1. Extern **NVMe** (e.g. USB-NVMe enclosure; infer from `TRAN`/model where reasonable)
2. Extern **SSD** (SATA/NVMe in USB enclosure)
3. Extern **HDD**
4. **USB flash drive** (typically smaller/slower; only if clearly acceptable and eNeeugh free space)
5. **SD card** (only if clearly Extern, rw, suitable filesystem, eNeeugh free space)

**Neet** acceptable as Terugup targets: the root filesystem (`/`), Intern system NVMe, boot/EFI, Windows system Partities, paths that live only under `/tmp`, `/home`, `/var` without a dedicated Extern block Apparaat, **readonly** media, media without sufficient **free** space.

## Strategic mount path (Documentatie)

**`/media/setuphelfer/setuphelfer-Terug`** is a **conventional target path** **only** when it resides on a **chosen Extern block Apparaat** (mount resolves to a `/dev/...` Apparaat that is Neet the system disk).

- **Forbidden:** creating that path as a Neermal directory on the root filesystem or using Intern NVMe as its Teruging store.
- **Nee automatic bind mounts** and **Nee** automatic ACL/permission changes without explicit approval.
- If the volume is already mounted elsewhere (e.g. **`/media/<user>/setuphelfer-Terug`**), there is **Nee** automatic path rewrite — agree with the operator whether the strategic path requires move/mount/bind.

## API Neete

**target-check** validates mount source, Apparaat classification, and (under `/media` / `/run/media`) traversability. Without a safe Extern target: **geblokkeerd**, Nee Terugup start.

## Related documents

- `docs/Terugup/TerugUP_TARGET_POLICY_DE.md`
- `docs/kNeewledge-base/Terugup/TerugUP_TARGET_SELECTION.md`
- `docs/faq/TerugUP_Herstel_FAQ_EN.md`
