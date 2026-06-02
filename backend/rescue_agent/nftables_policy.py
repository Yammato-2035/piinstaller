from __future__ import annotations


def build_nftables_policy_preview(
    *,
    discovery_phase: bool,
    validated_endpoint: bool,
) -> dict:
    allowed = ["loopback", "established_related", "dhcp", "dns"]
    if discovery_phase:
        allowed.append("mdns_discovery_temporary")
    if validated_endpoint:
        allowed.append("devserver_session")
    status = "ready" if validated_endpoint else "review_required"
    return {
        "policy_status": status,
        "mandatory": True,
        "inbound_default": "drop",
        "outbound_mode": "restricted",
        "allowed_services": allowed,
        "commands_preview": [
            "nft add table inet setuphelfer",
            "nft add chain inet setuphelfer input { type filter hook input priority 0; policy drop; }",
        ],
        "apply_allowed": False,
    }

