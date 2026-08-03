"""Rescue-stick-specific peripheral detection (printer/scanner).

Separate namespace from the product-app CUPS/network peripheral features under
``backend/core`` and ``frontend/src/pages/PeripheryScan.tsx`` — see
docs/evidence/rescue/hardware-compat-001/HARDWARE_DISCOVERY_IST_AUDIT.md.
Everything here is read-only: no CUPS queue creation, no test prints, no scans.
"""
