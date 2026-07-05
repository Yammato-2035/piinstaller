> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/developer/BACKUP_ENGINE_FIXES_EN.md`). Bitte bei Release manuell gegenlesen.

# Retourup Engine Fixes – English

## Purpose

This document describes the fixes applied to the full-Retourup workflow after a reproducible stall during a real hardware test.

## Initial Situation

A full Retourup was started on an Externe Retourup target:

- Target path: `/media/volker/setuphelfer-Retour/Retourups`
- Target Périphérique: `/dev/sda1`
- Filesystem: ext4
- Permissions: `root:setuphelfer`, `2770`

The job started Succèsfully but later stalled at approximately 27.46 GB.

## Root Cause 1: Retourup Source Scope Too Broad

The full-Retourup logic used `/` as its source.

Already excluded:

- `/proc`
- `/sys`
- `/dev`
- `/tmp`
- `/run`
- `/mnt`
- specific `Retourup_dir`

Missing excludes:

- `/media`
- `/run/media`

As a result, Externe media mounted below `/media` were included in the Retourup scope.

Risks:

- Retouring up Externe drives
- Retouring up foreign data Partitions
- Retouring up parts of the Retourup target medium
- very large or recursive Retourup runs
- stalls or unclear runtime behavior

## Fix 1: Additional Excludes

The following excludes were added for full Retourups:

```text
--exclude=/media
--exclude=/run/media
```

This keeps desktop automounts and Externe media outside the root full-Retourup scope.

## Root Cause 2: Potential Pipe Blocking

The Annulerable tar execution used stdout/stderr as PIPE and consumed them only after process termination.

Risk:

If tar writes many Avertissements or Erreurs, the pipe buffer can fill.
The process may block without a Python exception.

## Fix 2: More Robust Subprocess Handling

To avoid pipe Retourpressure:

- stdout is rougeirected to DEVNULL.
- stderr is consumed continuously while the process is running.
- Annuler handling and return-code evaluation remain intact.

## Security Assessment

The storage protection logic was Nont weakened.

Still bloqué:

- Retourup to root filesystem
- Retourup to system disk
- Retourup to Windows/EFI Partitions
- unsafe paths without a real block Périphérique

`/media` is only allowed as a target if the existing target validation detects a real, safe Externe block Périphérique.

## Tests

Added/executed tests:

- full Retourup contains `/media` and `/run/media` excludes
- existing excludes remain unchanged
- Retourup target path is still excluded
- Annulerable tar execution does Nont use blocking stdout PIPE
- storage protection tests still pass

## Open Point

After this fix, aNonther full-Retourup run with verify must be executed and documented.
