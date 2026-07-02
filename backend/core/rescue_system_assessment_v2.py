"""
Rescue system assessment V2 — automated, reproducible, redactable target machine evaluation.
Read-only on target; missing tools → missing_tool, never crash.
"""

from __future__ import annotations

import json
import re
import subprocess
import uuid
from datetime import datetime, timezone
from typing import Any

from core.rescue_assessment_redaction import redact_assessment_payload
from core.rescue_issue_codes_v2 import RescueIssueCodeV2
from core.rescue_recommendation_codes_v2 import RescueRecommendationCodeV2

ASSESSMENT_SCHEMA_VERSION = "system-assessment.v2"


def _utc_now() -> str:
  return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _run(cmd: list[str], *, timeout: int = 15) -> tuple[str, bool]:
  try:
    out = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT, timeout=timeout)
    return out, True
  except FileNotFoundError:
    return "", False
  except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
    return f"[error:{type(exc).__name__}]", True


def _parse_lshw_summary(text: str) -> dict[str, Any]:
  vendor = re.search(r"vendor:\s*(.+)", text)
  product = re.search(r"product:\s*(.+)", text)
  return {
    "vendor": vendor.group(1).strip() if vendor else None,
    "product": product.group(1).strip() if product else None,
  }


def _collect_system() -> dict[str, Any]:
  dmidecode, dm_ok = _run(["dmidecode", "-t", "system"])
  uname, _ = _run(["uname", "-r"])
  boot_mode = "unknown"
  efivars, ef_ok = _run(["ls", "/sys/firmware/efi/efivars"])
  if ef_ok and efivars and "[error" not in efivars:
    boot_mode = "uefi"
  secure_boot = "unknown"
  sb_text, _ = _run(["mokutil", "--sb-state"])
  if "enabled" in sb_text.lower():
    secure_boot = "enabled"
  elif "disabled" in sb_text.lower():
    secure_boot = "disabled"
  missing: list[str] = []
  if not dm_ok:
    missing.append("dmidecode")
  return {
    "manufacturer": _parse_lshw_summary(dmidecode).get("vendor") if dm_ok else None,
    "model": _parse_lshw_summary(dmidecode).get("product") if dm_ok else None,
    "bios_uefi": "uefi" if boot_mode == "uefi" else "legacy_or_unknown",
    "boot_mode": boot_mode,
    "secure_boot_status": secure_boot,
    "kernel_version": uname.strip() if uname else None,
    "rescue_version": None,
    "boot_session_id": uuid.uuid4().hex,
    "missing_tools": missing,
  }


def _collect_cpu_ram() -> dict[str, Any]:
  lscpu, lscpu_ok = _run(["lscpu"])
  mem, mem_ok = _run(["grep", "MemTotal", "/proc/meminfo"])
  vendor = None
  arch = None
  family = None
  if lscpu_ok:
    for line in lscpu.splitlines():
      if line.startswith("Vendor ID:"):
        vendor = line.split(":", 1)[1].strip()
      if line.startswith("Architecture:"):
        arch = line.split(":", 1)[1].strip()
      if line.startswith("CPU family:"):
        family = line.split(":", 1)[1].strip()
  ram_gb = None
  if mem_ok and mem:
    m = re.search(r"(\d+)", mem)
    if m:
      ram_gb = round(int(m.group(1)) / 1024 / 1024, 1)
  missing = []
  if not lscpu_ok:
    missing.append("lscpu")
  return {
    "cpu_vendor": vendor,
    "cpu_family": family,
    "architecture": arch,
    "ram_size_gb_approx": ram_gb,
    "missing_tools": missing,
  }


def _collect_gpu() -> dict[str, Any]:
  lspci, ok = _run(["lspci", "-nnk"])
  vendors: list[str] = []
  drivers: list[str] = []
  nvidia_compat = False
  if ok:
    for line in lspci.splitlines():
      if re.search(r"VGA|3D|Display", line, re.I):
        if "Intel" in line:
          vendors.append("intel")
        if "AMD" in line or "ATI" in line:
          vendors.append("amd")
        if "NVIDIA" in line:
          vendors.append("nvidia")
      if "Kernel driver in use:" in line:
        drivers.append(line.split(":", 1)[1].strip())
      if "nouveau" in line.lower() or "nvidia" in line.lower():
        nvidia_compat = "nvidia" in " ".join(vendors)
  return {
    "vendors": sorted(set(vendors)),
    "drivers_loaded": drivers,
    "nvidia_compat_mode_detected": nvidia_compat,
    "missing_tools": [] if ok else ["lspci"],
  }


def _collect_storage() -> dict[str, Any]:
  lsblk_json, ok = _run(["lsblk", "-J", "-o", "NAME,TYPE,SIZE,TRAN,ROTA,FSTYPE"])
  disks: list[dict[str, Any]] = []
  partition_types: list[str] = []
  fstypes: list[str] = []
  if ok:
    try:
      data = json.loads(lsblk_json)
      for dev in data.get("blockdevices") or []:
        if not isinstance(dev, dict):
          continue
        tran = str(dev.get("tran") or "unknown")
        disks.append({
          "name": dev.get("name"),
          "transport": tran,
          "size": dev.get("size"),
          "rotational": dev.get("rota"),
          "internal_guess": tran in {"nvme", "sata", "ata"} and dev.get("type") == "disk",
        })
        for child in dev.get("children") or []:
          if isinstance(child, dict) and child.get("fstype"):
            fstypes.append(str(child["fstype"]))
    except json.JSONDecodeError:
      pass
  smart_summary: list[dict[str, Any]] = []
  for disk in disks[:4]:
    name = disk.get("name")
    if not name:
      continue
    smart_out, smart_ok = _run(["smartctl", "-H", f"/dev/{name}"], timeout=8)
    if smart_ok:
      passed = "PASSED" in smart_out.upper()
      smart_summary.append({"device": name, "health_passed": passed})
  nvme_health: list[dict[str, Any]] = []
  nvme_list, nvme_ok = _run(["nvme", "list"])
  if nvme_ok:
    nvme_health.append({"raw_lines": len(nvme_list.splitlines())})
  return {
    "disk_count": len(disks),
    "disks": disks,
    "partition_table_types": partition_types,
    "filesystem_types": sorted(set(fstypes)),
    "smart_summary": smart_summary,
    "nvme_health_summary": nvme_health,
    "backup_target_suitability": "external_usb_preferred" if any(d.get("internal_guess") for d in disks) else "unknown",
    "missing_tools": [] if ok else ["lsblk"],
  }


def _collect_firmware() -> dict[str, Any]:
  dmesg, ok = _run(["dmesg", "--ctime"])
  missing_fw: list[str] = []
  if ok:
    for line in dmesg.splitlines():
      if "firmware" in line.lower() and ("failed" in line.lower() or "not found" in line.lower()):
        missing_fw.append(line[:120])
  lsmod, _ = _run(["lsmod"])
  drivers = [ln.split()[0] for ln in lsmod.splitlines()[1:6] if ln.strip()]
  return {
    "dmesg_missing_firmware_redacted": missing_fw[:10],
    "sample_loaded_modules": drivers,
    "missing_tools": [] if ok else ["dmesg"],
  }


def _collect_pcie_aer() -> dict[str, Any]:
  dmesg, ok = _run(["dmesg", "--ctime"])
  corrected = nonfatal = fatal = 0
  if ok:
    corrected = len(re.findall(r"AER.*Corrected", dmesg, re.I))
    nonfatal = len(re.findall(r"AER.*Non-Fatal|AER.*non-fatal", dmesg, re.I))
    fatal = len(re.findall(r"AER.*Fatal", dmesg, re.I))
  cmdline, _ = _run(["cat", "/proc/cmdline"])
  noaer = "pci=noaer" in (cmdline or "")
  return {
    "corrected_count": corrected,
    "nonfatal_count": nonfatal,
    "fatal_count": fatal,
    "pci_noaer_cmdline": noaer,
    "limitation": "pci_noaer" if noaer else None,
    "missing_tools": [] if ok else ["dmesg"],
  }


def derive_issue_codes(assessment: dict[str, Any]) -> list[str]:
  codes: list[str] = []
  for section in assessment.values():
    if isinstance(section, dict):
      for tool in section.get("missing_tools") or []:
        codes.append(RescueIssueCodeV2.MISSING_TOOL.value)
  storage = assessment.get("storage") or {}
  for smart in storage.get("smart_summary") or []:
    if smart.get("health_passed") is False:
      codes.append(RescueIssueCodeV2.STORAGE_SMART_WARNING.value)
  pcie = assessment.get("pcie_aer") or {}
  if pcie.get("fatal_count", 0) > 0:
    codes.append(RescueIssueCodeV2.PCIE_AER_FATAL.value)
  elif pcie.get("nonfatal_count", 0) > 0:
    codes.append(RescueIssueCodeV2.PCIE_AER_NONFATAL.value)
  if pcie.get("pci_noaer_cmdline"):
    codes.append(RescueIssueCodeV2.PCIE_NOAER_LIMITATION.value)
  fw = assessment.get("firmware") or {}
  if fw.get("dmesg_missing_firmware_redacted"):
    codes.append(RescueIssueCodeV2.DMESG_FIRMWARE_MISSING.value)
  return sorted(set(codes))


def derive_recommendation_codes(issue_codes: list[str]) -> list[str]:
  recs: list[str] = [RescueRecommendationCodeV2.EXPLAIN_ONLY.value]
  if RescueIssueCodeV2.DMESG_FIRMWARE_MISSING.value in issue_codes:
    recs.append(RescueRecommendationCodeV2.CHECK_FIRMWARE_PACKAGES.value)
  if RescueIssueCodeV2.STORAGE_SMART_WARNING.value in issue_codes:
    recs.append(RescueRecommendationCodeV2.REVIEW_STORAGE_SMART.value)
  if RescueIssueCodeV2.PCIE_AER_FATAL.value in issue_codes:
    recs.append(RescueRecommendationCodeV2.DESTRUCTIVE_BLOCKED_MANUAL_GUIDE.value)
  return sorted(set(recs))


def build_system_assessment_v2(*, rescue_version: str | None = None) -> dict[str, Any]:
  system = _collect_system()
  system["rescue_version"] = rescue_version
  raw: dict[str, Any] = {
    "schema_version": ASSESSMENT_SCHEMA_VERSION,
    "collected_at": _utc_now(),
    "system": system,
    "cpu_ram": _collect_cpu_ram(),
    "gpu": _collect_gpu(),
    "storage": _collect_storage(),
    "firmware": _collect_firmware(),
    "pcie_aer": _collect_pcie_aer(),
    "network_summary": {},
    "malware_hints": {"autostart_hints": [], "webroot_hints": []},
  }
  raw["issue_codes"] = derive_issue_codes(raw)
  raw["recommendation_codes"] = derive_recommendation_codes(raw["issue_codes"])
  redacted, report = redact_assessment_payload(raw)
  return {
    "assessment": redacted,
    "redaction_report": report,
    "issue_codes": raw["issue_codes"],
    "recommendation_codes": raw["recommendation_codes"],
  }


def build_assessment_from_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
  """Build assessment from injected snapshot (tests / offline)."""
  raw = dict(snapshot)
  raw.setdefault("schema_version", ASSESSMENT_SCHEMA_VERSION)
  raw.setdefault("collected_at", _utc_now())
  raw["issue_codes"] = derive_issue_codes(raw)
  raw["recommendation_codes"] = derive_recommendation_codes(raw["issue_codes"])
  redacted, report = redact_assessment_payload(raw)
  return {
    "assessment": redacted,
    "redaction_report": report,
    "issue_codes": raw["issue_codes"],
    "recommendation_codes": raw["recommendation_codes"],
  }
