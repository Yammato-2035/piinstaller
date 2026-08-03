"""Target-OS provisioning planning (catalog, compatibility, verification preview,
install plan). Separate namespace from ``backend/deploy`` (Setuphelfer's own
self-deployment) — see docs/evidence/rescue/hardware-compat-001/
HARDWARE_DISCOVERY_IST_AUDIT.md. No image is ever written to a real device by
anything in this package; ``write_allowed`` is always false in this phase.
"""
