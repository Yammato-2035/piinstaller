from __future__ import annotations

from core.diagnostics.models import DiagnosticCase, DiagnosticsAnalyzeRequest
from core.diagnostics.registry import get_case_by_id
from core.diagnostics.sources import normalized_question, normalized_signals
from core.install_paths import path_text_suggests_legacy_pi_tree


def _hard_signal_matches(signals: dict[str, str]) -> list[str]:
    hits: list[str] = []
    # normalized_signals lowercases Werte
    sp = (signals.get("storage_protection") or "").strip().lower()
    code = (signals.get("code") or "").strip().lower()
    details_diag = (signals.get("details.diagnosis_id") or signals.get("diagnosis_id") or "").strip().upper()
    stderr = (signals.get("stderr") or "").strip().lower()
    summary = (signals.get("summary") or "").strip().lower()
    classification = (signals.get("classification") or "").strip().lower()
    email_status = (signals.get("email.status") or signals.get("email_status") or "").strip().lower()
    unreadable_sources = (signals.get("unreadable_sources") or "").strip().lower()
    owner_mode = (signals.get("mount_owner_mode") or signals.get("owner_mode") or "").strip().lower()
    probe_err = (signals.get("target_probe_error") or "").strip().lower()
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
    if sp == "storage-protection-006":
        hits.append("STORAGE-PROTECTION-006")
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
    if code == "backup.sudo_blocked_by_nnp" or details_diag == "SYSTEMD-NNP-031":
        hits.append("SYSTEMD-NNP-031")
    if code == "backup.source_permission_denied" or details_diag == "BACKUP-SOURCE-PERM-032":
        hits.append("BACKUP-SOURCE-PERM-032")
    if code == "backup.verify_integrity_failed":
        hits.append("VERIFY-STAGING-038")
    if code == "backup.restore_failed" and ("enospc" in stderr or "no space left on device" in stderr):
        hits.append("RESTORE-TMPFS-007")
    if ("permission denied" in stderr or "keine berechtigung" in stderr) and unreadable_sources not in {"", "null", "[]"}:
        hits.append("BACKUP-SOURCE-PERM-032")
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
    if "permission denied" in probe_err or "keine berechtigung" in probe_err:
        hits.append("PERM-GROUP-008")
    if signals.get("owner_mode_valid") == "false":
        hits.append("OWNER-MODE-023")
    if "root:root" in owner_mode and ("755" in owner_mode or "drwxr-xr-x" in owner_mode):
        hits.append("OWNER-MODE-023")
    if signals.get("raspi_boot_ok") == "false":
        hits.append("PI-BOOT-024")
    if code == "blocked_requires_operator_sudo_policy" or details_diag == "RESCUE-BUILD-ROOT-001":
        hits.append("RESCUE-BUILD-ROOT-001")
    if (
        "sudo: ein terminal ist erforderlich" in stderr
        or "sudo: ein passwort ist notwendig" in stderr
        or "sudo: a terminal is required" in stderr
        or "sudo: a password is required" in stderr
        or "blocked_requires_operator_sudo_policy" in summary
    ):
        hits.append("RESCUE-BUILD-ROOT-001")
    if code == "blocked_controlled_build_gate_required" or details_diag == "RESCUE-BUILD-GATE-001":
        hits.append("RESCUE-BUILD-GATE-001")
    if "use controlled gate before running lb build" in stderr or "use controlled gate before running lb build" in summary:
        hits.append("RESCUE-BUILD-GATE-001")
    if code == "blocked_build_tools_missing" or details_diag == "RESCUE-BUILD-TOOL-001":
        hits.append("RESCUE-BUILD-TOOL-001")
    if (
        "rsvg-convert fehlt" in stderr
        or "rsvg-convert fehlt" in summary
        or "librsvg2-bin fehlt" in stderr
        or "librsvg2-bin fehlt" in summary
    ):
        hits.append("RESCUE-BUILD-TOOL-001")
    if code == "blocked_legacy_rsvg_command_missing" or details_diag == "RESCUE-BUILD-RSVG-001":
        hits.append("RESCUE-BUILD-RSVG-001")
    if (
        "live-build erwartet /usr/bin/rsvg" in stderr
        or "live-build erwartet /usr/bin/rsvg" in summary
        or "rsvg-convert vorhanden, aber rsvg fehlt" in stderr
        or "rsvg-convert vorhanden, aber rsvg fehlt" in summary
    ):
        hits.append("RESCUE-BUILD-RSVG-001")
    requested_architecture = (signals.get("requested_architecture") or signals.get("target_architecture") or "").strip().lower()
    architecture_track_status = (signals.get("architecture_track_status") or signals.get("target_architecture_status") or "").strip().lower()
    if requested_architecture == "amd64" and (
        signals.get("i386_covered") == "false"
        or signals.get("arm64_covered") == "false"
        or signals.get("armhf_covered") == "false"
        or architecture_track_status == "review_required"
    ):
        hits.append("RESCUE-BUILD-ARCH-001")
    if requested_architecture == "i386" and architecture_track_status == "review_required":
        hits.append("RESCUE-BUILD-ARCH-001")
    if requested_architecture in {"arm64", "armhf"} and architecture_track_status == "deferred":
        hits.append("RESCUE-BUILD-ARCH-001")
    if "i386 requested but status review_required" in summary or "i386 requested but status review_required" in stderr:
        hits.append("RESCUE-BUILD-ARCH-001")
    if "arm64 requested but deferred" in summary or "arm64 requested but deferred" in stderr:
        hits.append("RESCUE-BUILD-ARCH-001")
    if "armhf requested but deferred" in summary or "armhf requested but deferred" in stderr:
        hits.append("RESCUE-BUILD-ARCH-001")
    if (
        code == "notification.email.provider_limit_exceeded"
        or classification == "notification.email.provider_limit_exceeded"
        or details_diag == "NOTIFICATION-EMAIL-PROVIDER-001"
        or email_status == "provider_limit"
    ):
        hits.append("NOTIFICATION-EMAIL-PROVIDER-001")
    if "554 5.7.0 outgoing message limit exceeded" in stderr or "554 5.7.0 outgoing message limit exceeded" in summary:
        hits.append("NOTIFICATION-EMAIL-PROVIDER-001")

    sc_ids = (signals.get("service_conflict_ids") or "").upper()
    for token in (
        "SERVICE-CONFLICT-033",
        "SERVICE-CONFLICT-034",
        "SERVICE-CONFLICT-035",
        "SERVICE-CONFLICT-036",
    ):
        if token in sc_ids:
            hits.append(token)
    if signals.get("systemd_pi_installer_service") == "active" or signals.get("systemd_pi_installer_backend_service") == "active":
        hits.append("SERVICE-CONFLICT-033")
    pot = (signals.get("port_8000_owner_text") or "").strip().lower()
    if path_text_suggests_legacy_pi_tree(pot):
        hits.append("SERVICE-CONFLICT-034")
    if signals.get("mixed_opt_install") == "true" and signals.get("legacy_systemd_still_enabled") == "true":
        hits.append("SERVICE-CONFLICT-035")
    if signals.get("legacy_must_not_overwrite_new") == "true":
        hits.append("SERVICE-CONFLICT-036")
    return hits


def _pattern_matches(question: str) -> list[str]:
    hits: list[str] = []
    if "manifest" in question:
        hits.append("BACKUP-MANIFEST-001")
    if "hash" in question or "checksum" in question:
        hits.append("BACKUP-HASH-003")
    if "tmp" in question or "tmpfs" in question:
        hits.append("RESTORE-TMPFS-007")
    if "memorymax" in question or ("cgroup" in question and "memory" in question) or ("oom" in question and ("verify" in question or "preview" in question)):
        hits.append("SYSTEMD-MEMORYMAX-037")
    if "verify_integrity" in question or ("deep" in question and "integrit" in question):
        hits.append("VERIFY-STAGING-038")
    if "startet nicht" in question or "does not start" in question:
        hits.extend(["SYSTEMD-START-009", "RUNTIME-PORT-011"])
    if "crash" in question:
        hits.append("SYSTEMD-CRASH-010")
    if "node_options" in question:
        hits.append("NODE-OPTIONS-012")
    if "addressfamily" in question:
        hits.append("SYSTEMD-AF-014")
    if "no new privileges" in question or "nonewprivileges" in question or "keine neuen privilegien" in question:
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
    if "rescue" in question and "sudo" in question:
        hits.append("RESCUE-BUILD-ROOT-001")
    if "lb build" in question and "gate" in question:
        hits.append("RESCUE-BUILD-GATE-001")
    if "rsvg" in question and ("fehlt" in question or "missing" in question):
        hits.extend(["RESCUE-BUILD-TOOL-001", "RESCUE-BUILD-RSVG-001"])
    if "rescue" in question and "architektur" in question:
        hits.append("RESCUE-BUILD-ARCH-001")
    if "provider limit" in question or "554 5.7.0" in question:
        hits.append("NOTIFICATION-EMAIL-PROVIDER-001")
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
