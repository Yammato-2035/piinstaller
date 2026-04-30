# FAQ – Backup & Restore – English

## Why must the backup not be stored on the root filesystem?

A backup stored on the same filesystem as the running system is unsafe. A disk failure, user error, or restore problem may destroy both the original system and the backup.

## Why was `/mnt/setuphelfer/backups` blocked?

The path was located on the root filesystem and was not a separate safe target device. The storage protection logic correctly blocked it.

## Why was `/media/...` initially blocked?

The previous logic blocked `/media` globally. This was too strict because Linux desktop systems typically mount external drives below `/media/<user>/...`.

## How was this fixed?

`/media` was not globally allowed. A target below `/media` is only accepted if it resolves to a real, safe block device and is not a system, boot, Windows, or EFI partition.

## Why must `/media` be excluded from full backups?

When backing up `/`, including `/media` would also include external drives. This can lead to huge backups, recursive backup runs, or stalls.

## Which paths are excluded from full backups?

At least:

- `/proc`
- `/sys`
- `/dev`
- `/tmp`
- `/run`
- `/mnt`
- `/media`
- `/run/media`
- the specific backup target path

## Why did the backup stall?

The specific run stalled at approximately 27.46 GB. Probable causes were:

- backup source scope too broad, including `/media`
- possible pipe blocking through tar stdout/stderr

## What was changed?

- `/media` and `/run/media` were added as excludes.
- stdout is no longer buffered.
- stderr is consumed while the process is running.

## What still needs to be done after the fix?

A new full-backup run must complete successfully. Manifest, Basic Verify, and ideally Deep Verify must then be checked.

## When is monolith refactoring allowed?

Only after:

- target check succeeds
- full backup succeeds
- manifest exists
- verify succeeds
