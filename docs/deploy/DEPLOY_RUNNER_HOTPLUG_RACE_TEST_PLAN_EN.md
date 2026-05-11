# Deploy Runner Hotplug/Unmount Race Test Design (read-only)

## Goal

Safe test design for later hotplug/unmount race validation on disposable media.

## Contents

- preconditions, manual steps, and race cases
- trigger/abort-code/audit evidence per case
- risk controls, stop conditions, and rollback

## API

- `POST /api/deploy/runner/hotplug-race/test-plan`
