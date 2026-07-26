# Control image verification — G513QM A/B

## Sources

| Control | Mirror | Files |
|---------|--------|-------|
| A (Mint 22.1) | https://mirrors.edge.kernel.org/linuxmint/stable/22.1/ | sha256sum.txt + .gpg (+ ISO pending) |
| B (Mint 22.3) | https://mirrors.edge.kernel.org/linuxmint/stable/22.3/ | sha256sum.txt + .gpg (+ ISO pending) |

GPG key: `27DEB15644C6B3CF3BD7D291300F846BA25BAE09` (Linux Mint ISO Signing Key)

## Results (2026-07-26)

| Control | Checksum file | GPG | ISO on disk | Status |
|---------|---------------|-----|-------------|--------|
| A | present | Good signature | **not downloaded** | `checksum_only` / ISO `not_available` |
| B | present | Good signature | **not downloaded** | `checksum_only` / ISO `not_available` |

Expected SHA256 (Cinnamon 64-bit):

- A: `ccf482436df954c0ad6d41123a49fde79352ca71f7a684a97d5e0a0c39d7f39f`
- B: `a081ab202cfda17f6924128dbd2de8b63518ac0531bcfe3f1a1b88097c459bd4`

## Operator download

```bash
cd /tmp/piinstaller-install-assistant-001
./scripts/rescue/g513qm-kernel-abc/verify-control-iso.sh control-a --download-iso
./scripts/rescue/g513qm-kernel-abc/verify-control-iso.sh control-b --download-iso
```

Blocked statuses (must not write USB): `signature_failed`, `checksum_failed`, `source_untrusted`.

Control ISOs must never be remastered with Setuphelfer files.
