# Backup Engine Fixes – English

## Purpose

This document describes the fixes applied to the full-backup workflow after a reproducible stall during a real hardware test.

## Initial Situation

A full backup was started on an external backup target:

- Target path: `/media/volker/setuphelfer-back/backups`
- Target device: `/dev/sda1`
- Filesystem: ext4
- Permissions: `root:setuphelfer`, `2770`

The job started successfully but later stalled at approximately 27.46 GB.

## Root Cause 1: Backup Source Scope Too Broad

The full-backup logic used `/` as its source.

Already excluded:

- `/proc`
- `/sys`
- `/dev`
- `/tmp`
- `/run`
- `/mnt`
- specific `backup_dir`

Missing excludes:

- `/media`
- `/run/media`

As a result, external media mounted below `/media` were included in the backup scope.

Risks:

- backing up external drives
- backing up foreign data partitions
- backing up parts of the backup target medium
- very large or recursive backup runs
- stalls or unclear runtime behavior

## Fix 1: Additional Excludes

The following excludes were added for full backups:

```text
--exclude=/media
--exclude=/run/media
```

This keeps desktop automounts and external media outside the root full-backup scope.

## Root Cause 2: Potential Pipe Blocking

The cancelable tar execution used stdout/stderr as PIPE and consumed them only after process termination.

Risk:

If tar writes many warnings or errors, the pipe buffer can fill.
The process may block without a Python exception.

## Fix 2: More Robust Subprocess Handling

To avoid pipe backpressure:

- stdout is redirected to DEVNULL.
- stderr is consumed continuously while the process is running.
- cancel handling and return-code evaluation remain intact.

## Security Assessment

The storage protection logic was not weakened.

Still blocked:

- backup to root filesystem
- backup to system disk
- backup to Windows/EFI partitions
- unsafe paths without a real block device

`/media` is only allowed as a target if the existing target validation detects a real, safe external block device.

## Tests

Added/executed tests:

- full backup contains `/media` and `/run/media` excludes
- existing excludes remain unchanged
- backup target path is still excluded
- cancelable tar execution does not use blocking stdout PIPE
- storage protection tests still pass

## Open Point

After this fix, another full-backup run with verify must be executed and documented.
