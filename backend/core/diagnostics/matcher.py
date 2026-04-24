from __future__ import annotations

from core.diagnostics.models import DiagnosticCase, DiagnosticsAnalyzeRequest
from core.diagnostics.registry import get_case_by_id
from core.diagnostics.sources import normalized_question, normalized_signals


def _hard_signal_matches(signals: dict[str, str]) -> list[str]:
    hits: list[str] = []
    # normalized_signals lowercases Werte
    sp = (signals.get("storage_protection") or "").strip().lower()
    if sp == "storage-protection-001":
        hits.append("STORAGE-PROTECTION-001")
    if sp == "storage-protection-002":
        hits.append("STORAGE-PROTECTION-002")
    if sp == "storage-protection-003":
        hits.append("STORAGE-PROTECTION-003")
    if sp == "storage-protection-004":
        hits.append("STORAGE-PROTECTION-004")
    if sp == "storage-protection-005":
        hits.append("STORAGE-PROTECTION-005")
    if signals.get("manifest_present") == "false":
        hits.append("BACKUP-MANIFEST-001")
    if signals.get("archive_corrupted") == "true":
        hits.append("BACKUP-ARCHIVE-002")
    if signals.get("verify_status") in {"hash_mismatch", "checksum_mismatch"}:
        hits.append("BACKUP-HASH-003")
    if signals.get("restore_path_safe") == "false":
        hits.append("RESTORE-PATH-004")
    if signals.get("restore_status") == "partial":
        hits.append("RESTORE-PARTIAL-005")
    if signals.get("backend_service_active") == "false" and signals.get("frontend_service_active") == "true":
        hits.append("UI-NO-BACKEND-015")
        hits.append("RESTORE-RUNTIME-006")
    if signals.get("node_options_present") == "false":
        hits.append("NODE-OPTIONS-012")
    if signals.get("systemd_restrictive") == "true":
        hits.append("SYSTEMD-RESTRICT-013")
    if signals.get("address_family_restricted") == "true":
        hits.append("SYSTEMD-AF-014")
    if signals.get("sudo_no_new_privileges") == "true":
        hits.append("SYSTEMD-NNP-031")
    if signals.get("ssh_enabled") == "false":
        hits.append("SSH-DISABLED-017")
    if signals.get("port_22_open") == "false":
        hits.append("SSH-PORT-016")
    if signals.get("dns_ok") == "false":
        hits.append("DNS-018")
    if signals.get("firewall_blocks_access") == "true":
        hits.append("FIREWALL-020")
    if signals.get("filesystem_readonly") == "true":
        hits.append("FS-RO-021")
    if signals.get("storage_full") == "true":
        hits.append("FS-FULL-022")
    if signals.get("setuphelfer_group_present") == "false":
        hits.append("PERM-GROUP-008")
    if signals.get("owner_mode_valid") == "false":
        hits.append("OWNER-MODE-023")
    if signals.get("raspi_boot_ok") == "false":
        hits.append("PI-BOOT-024")
    return hits


def _pattern_matches(question: str) -> list[str]:
    hits: list[str] = []
    if "manifest" in question:
        hits.append("BACKUP-MANIFEST-001")
    if "hash" in question or "checksum" in question:
        hits.append("BACKUP-HASH-003")
    if "tmp" in question or "tmpfs" in question:
        hits.append("RESTORE-TMPFS-007")
    if "startet nicht" in question or "does not start" in question:
        hits.extend(["SYSTEMD-START-009", "RUNTIME-PORT-011"])
    if "crash" in question:
        hits.append("SYSTEMD-CRASH-010")
    if "node_options" in question:
        hits.append("NODE-OPTIONS-012")
    if "addressfamily" in question:
        hits.append("SYSTEMD-AF-014")
    if "no new privileges" in question or "nonewprivileges" in question:
        hits.append("SYSTEMD-NNP-031")
    if "ssh" in question:
        hits.extend(["SSH-DISABLED-017", "SSH-PORT-016"])
    if "dns" in question:
        hits.append("DNS-018")
    if "firewall" in question:
        hits.append("FIREWALL-020")
    if "read-only" in question or "readonly" in question:
        hits.append("FS-RO-021")
    if "voll" in question or "full" in question:
        hits.append("FS-FULL-022")
    if "gruppe" in question or "group" in question:
        hits.append("PERM-GROUP-008")
    if "nvme" in question or "usb boot" in question:
        hits.append("PI-NVME-025")
    if "docker" in question:
        hits.append("DOCKER-028")
    if "laufwerk blockiert" in question or "drive blocked" in question or "write protection" in question:
        hits.extend(
            [
                "STORAGE-PROTECTION-001",
                "STORAGE-PROTECTION-004",
                "STORAGE-PROTECTION-005",
            ]
        )
    if "windows" in question and ("laufwerk" in question or "disk" in question or "partition" in question):
        hits.append("STORAGE-PROTECTION-003")
    return hits


def match_diagnoses(req: DiagnosticsAnalyzeRequest) -> list[DiagnosticCase]:
    signals = normalized_signals(req)
    question = normalized_question(req)

    ordered_ids: list[str] = []
    for diag_id in _hard_signal_matches(signals) + _pattern_matches(question):
        if diag_id not in ordered_ids:
            ordered_ids.append(diag_id)

    if not ordered_ids and question:
        ordered_ids.append("LOGS-029")
    if not ordered_ids:
        ordered_ids.append("APP-030")

    out: list[DiagnosticCase] = []
    for diag_id in ordered_ids:
        item = get_case_by_id(diag_id)
        if item is not None:
            out.append(item)
    return out
