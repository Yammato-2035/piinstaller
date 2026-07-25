"""
Linux distro install profiles for rescue stick Installationsassistent.

Debian Live = stick runtime (not an install target profile).
Install targets: Linux Mint, Ubuntu Server LTS, Ubuntu Server, Debian Install.
"""

from __future__ import annotations

from enum import Enum
from typing import Any


class LinuxDistroProfileId(str, Enum):
  LINUX_MINT = "linux_mint"
  UBUNTU_SERVER_LTS = "ubuntu_server_lts"
  UBUNTU_SERVER = "ubuntu_server"
  DEBIAN_INSTALL = "debian"


# Stick runtime — not selectable as install target
DEBIAN_LIVE_RUNTIME = "debian_live"


DISTRO_PROFILES: dict[str, dict[str, Any]] = {
  LinuxDistroProfileId.LINUX_MINT.value: {
    "id": "linux_mint",
    "label_de": "Linux Mint",
    "label_en": "Linux Mint",
    "edition": "desktop",
    "priority": "p0",
    "support_level": "supported",
    "arch": "amd64",
    "iso_kind": "desktop",
    "default_for_asus_second_nvme": True,
    "setuphelfer_bootstrap": True,
  },
  LinuxDistroProfileId.UBUNTU_SERVER_LTS.value: {
    "id": "ubuntu_server_lts",
    "label_de": "Ubuntu Server LTS",
    "label_en": "Ubuntu Server LTS",
    "edition": "server",
    "priority": "p1",
    "support_level": "planned",
    "arch": "amd64",
    "iso_kind": "server_lts",
    "default_for_asus_second_nvme": False,
    "setuphelfer_bootstrap": True,
  },
  LinuxDistroProfileId.UBUNTU_SERVER.value: {
    "id": "ubuntu_server",
    "label_de": "Ubuntu Server",
    "label_en": "Ubuntu Server",
    "edition": "server",
    "priority": "p1",
    "support_level": "planned",
    "arch": "amd64",
    "iso_kind": "server",
    "default_for_asus_second_nvme": False,
    "setuphelfer_bootstrap": True,
  },
  LinuxDistroProfileId.DEBIAN_INSTALL.value: {
    "id": "debian",
    "label_de": "Debian Installation",
    "label_en": "Debian install",
    "edition": "install",
    "priority": "p1",
    "support_level": "planned",
    "arch": "amd64",
    "iso_kind": "netinst_or_dvd",
    "default_for_asus_second_nvme": False,
    "setuphelfer_bootstrap": True,
    "note_de": "Debian Live ist die Stick-Laufzeit; dieses Profil ist die Zielinstallation.",
  },
}


def list_distro_profiles(*, include_planned: bool = True) -> list[dict[str, Any]]:
  out = []
  for profile in DISTRO_PROFILES.values():
    if not include_planned and profile.get("support_level") != "supported":
      continue
    out.append(dict(profile))
  return out


def get_distro_profile(profile_id: str) -> dict[str, Any] | None:
  return DISTRO_PROFILES.get(profile_id)


def distro_install_allowed(profile_id: str) -> bool:
  profile = get_distro_profile(profile_id)
  return bool(profile and profile.get("support_level") == "supported")


def alias_to_profile_id(raw: str | None) -> str | None:
  """Map legacy ASUS-branch names to canonical profile IDs."""
  if not raw:
    return None
  key = raw.strip().lower().replace("_", "-")
  mapping = {
    "linux-mint": "linux_mint",
    "linux_mint": "linux_mint",
    "mint": "linux_mint",
    "ubuntu-lts": "ubuntu_server_lts",
    "ubuntu_server_lts": "ubuntu_server_lts",
    "ubuntu-server-lts": "ubuntu_server_lts",
    "ubuntu-server": "ubuntu_server",
    "ubuntu_server": "ubuntu_server",
    "debian-stable": "debian",
    "debian": "debian",
    "debian-install": "debian",
  }
  return mapping.get(key)
