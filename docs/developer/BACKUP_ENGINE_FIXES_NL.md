> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/developer/BACKUP_ENGINE_FIXES_EN.md`). Bitte bei Release manuell gegenlesen.

# Terugup Engine Fixes – English

## Purpose

This document describes the fixes applied to the full-Terugup workflow after a reproducible stall during a real hardware test.

## Initial Situation

A full Terugup was started on an Extern Terugup target:

- Target path: `/media/volker/setuphelfer-Terug/Terugups`
- Target Apparaat: `/dev/sda1`
- Filesystem: ext4
- Permissions: `root:setuphelfer`, `2770`

The job started Geslaagdfully but later stalled at approximately 27.46 GB.

## Root Cause 1: Terugup Source Scope Too Broad

The full-Terugup logic used `/` as its source.

Already excluded:

- `/proc`
- `/sys`
- `/dev`
- `/tmp`
- `/run`
- `/mnt`
- specific `Terugup_dir`

Missing excludes:

- `/media`
- `/run/media`

As a result, Extern media mounted below `/media` were included in the Terugup scope.

Risks:

- Teruging up Extern drives
- Teruging up foreign data Partities
- Teruging up parts of the Terugup target medium
- very large or recursive Terugup runs
- stalls or unclear runtime behavior

## Fix 1: Additional Excludes

The following excludes were added for full Terugups:

```text
--exclude=/media
--exclude=/run/media
```

This keeps desktop automounts and Extern media outside the root full-Terugup scope.

## Root Cause 2: Potential Pipe Blocking

The Annulerenable tar execution used stdout/stderr as PIPE and consumed them only after process termination.

Risk:

If tar writes many Waarschuwings or Fouts, the pipe buffer can fill.
The process may block without a Python exception.

## Fix 2: More Robust Subprocess Handling

To avoid pipe Terugpressure:

- stdout is roodirected to DEVNULL.
- stderr is consumed continuously while the process is running.
- Annuleren handling and return-code evaluation remain intact.

## Security Assessment

The storage protection logic was Neet weakened.

Still geblokkeerd:

- Terugup to root filesystem
- Terugup to system disk
- Terugup to Windows/EFI Partities
- unsafe paths without a real block Apparaat

`/media` is only allowed as a target if the existing target validation detects a real, safe Extern block Apparaat.

## Tests

Added/executed tests:

- full Terugup contains `/media` and `/run/media` excludes
- existing excludes remain unchanged
- Terugup target path is still excluded
- Annulerenable tar execution does Neet use blocking stdout PIPE
- storage protection tests still pass

## Open Point

After this fix, aNeether full-Terugup run with verify must be executed and documented.
